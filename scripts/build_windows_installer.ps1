$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

$venvDir = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $venvDir "bin\python.exe"
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvDir = Join-Path $repoRoot ".venv-build"
    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $venvPython = Join-Path $venvDir "bin\python.exe"
    }
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = "python"
}

function Invoke-CheckedPython {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & $script:venvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

function Move-ToInstallerArchive {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$ArchivePath
    )

    $source = Get-Item -LiteralPath $SourcePath
    $destination = Join-Path $ArchivePath $source.Name
    if (Test-Path -LiteralPath $destination) {
        $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
        $token = [Guid]::NewGuid().ToString("N").Substring(0, 8)
        $destinationName = "$($source.BaseName)-$stamp-$token$($source.Extension)"
        $destination = Join-Path $ArchivePath $destinationName
    }

    Move-Item -LiteralPath $source.FullName -Destination $destination
}

function Get-FreeSubstDrive {
    $usedDrives = @(
        [System.IO.DriveInfo]::GetDrives() |
            ForEach-Object { $_.Name.Substring(0, 2).ToUpperInvariant() }
    )
    foreach ($codePoint in 90..68) {
        $candidate = "$([char]$codePoint):"
        if ($usedDrives -notcontains $candidate) {
            return $candidate
        }
    }
    throw "No free drive letter is available to shorten the Inno Setup build path."
}

function Invoke-InnoCompiler {
    param(
        [Parameter(Mandatory = $true)][string]$CompilerPath,
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string]$RepositoryRoot
    )

    $substDrive = $null
    $compilerScript = $ScriptPath
    try {
        if ($ScriptPath.Length -ge 80) {
            $substDrive = Get-FreeSubstDrive
            & subst.exe $substDrive $RepositoryRoot
            if ($LASTEXITCODE -ne 0) {
                throw "subst.exe could not map $substDrive to $RepositoryRoot."
            }
            $shortRoot = "${substDrive}\"
            $compilerScript = Join-Path $shortRoot "packaging\windows\ChaosToolbox.iss"
            if (-not (Test-Path -LiteralPath $compilerScript)) {
                throw "The shortened Inno Setup script path is unavailable: $compilerScript"
            }
            Write-Host "Using shortened Inno Setup path: $compilerScript"
        }

        & $CompilerPath $compilerScript
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup compiler failed with exit code $LASTEXITCODE"
        }
    } finally {
        if ($substDrive) {
            & subst.exe $substDrive /D
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Could not remove temporary subst mapping $substDrive."
            }
        }
    }
}
Write-Host "Reading version from core/app_metadata.py..."
$appVersion = (Invoke-CheckedPython -Arguments @("-c", "from core.app_metadata import APP_VERSION; print(APP_VERSION)") | Out-String).Trim()
Write-Host "Project Version: $appVersion"
Invoke-CheckedPython -Arguments @(
    "scripts\verify_distribution_compliance.py",
    "--artifact",
    "dist\Chaos Toolbox"
)

# 1. Update/Write generated_version.iss
$versionInclude = Join-Path $repoRoot "packaging\windows\generated_version.iss"
Set-Content -LiteralPath $versionInclude -Encoding ASCII -Value "#define MyAppVersion `"$appVersion`""
Write-Host "Updated version in $versionInclude"

# 2. Robust Inno Setup detection
$isccPath = $null
if ($env:INNO_SETUP_ISCC) {
    if (Test-Path -LiteralPath $env:INNO_SETUP_ISCC) {
        $isccPath = $env:INNO_SETUP_ISCC
    } else {
        Write-Warning "INNO_SETUP_ISCC env variable is defined but path does not exist: $env:INNO_SETUP_ISCC"
    }
}

if (-not $isccPath) {
    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmd) {
        $isccPath = $cmd.Source
    }
}

if (-not $isccPath) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    foreach ($cand in $candidates) {
        if (Test-Path -LiteralPath $cand) {
            $isccPath = $cand
            break
        }
    }
}

if (-not $isccPath) {
    Write-Error "Inno Setup compiler (ISCC.exe) was not found on the system."
    Write-Host "Please install Inno Setup 6 or set the INNO_SETUP_ISCC environment variable:" -ForegroundColor Yellow
    Write-Host '  $env:INNO_SETUP_ISCC = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"' -ForegroundColor Yellow
    Write-Host "The PyInstaller executable in 'dist/' remains built, but the installer setup could not be created." -ForegroundColor Yellow
    exit 1
}

# 3. Archive previous installers
$installerDir = Join-Path $repoRoot "installer"
$archiveDir = Join-Path $installerDir "archive"
if (-not (Test-Path -LiteralPath $archiveDir)) {
    Write-Host "Creating archive directory: $archiveDir"
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
}

$oldInstallers = Get-ChildItem -Path $installerDir -Filter "*.exe" -File
if ($oldInstallers) {
    Write-Host "Archiving existing installers to $archiveDir..."
    foreach ($oldInst in $oldInstallers) {
        Move-ToInstallerArchive -SourcePath $oldInst.FullName -ArchivePath $archiveDir
    }
}

# 4. Compile Installer
Write-Host "Compiling Windows installer..."
$issScript = Join-Path $repoRoot "packaging\windows\ChaosToolbox.iss"
$buildStartTime = [DateTime]::Now

Invoke-InnoCompiler `
    -CompilerPath $isccPath `
    -ScriptPath $issScript `
    -RepositoryRoot $repoRoot

# 5. Verify Installer
$expectedInstallerName = "chaos-toolbox-v$appVersion-windows-x64-setup.exe"
$expectedInstallerPath = Join-Path $installerDir $expectedInstallerName

if (-not (Test-Path -LiteralPath $expectedInstallerPath)) {
    throw "Verification failed: Expected installer file was not found at $expectedInstallerPath"
}

$fileInfo = Get-Item -LiteralPath $expectedInstallerPath
if ($fileInfo.LastWriteTime -lt $buildStartTime.AddSeconds(-5)) {
    throw "Verification failed: Installer file at $expectedInstallerPath was not modified in the current build execution."
}

# Double check that we don't have the old installer output name by mistake
$oldNamePath = Join-Path $installerDir "ChaosToolboxSetup-0.1.0.exe"
if (Test-Path -LiteralPath $oldNamePath) {
    Write-Warning "Stale installer with old name found. Archiving it."
    Move-ToInstallerArchive -SourcePath $oldNamePath -ArchivePath $archiveDir
}

# Display results
Write-Host "`nInstaller successfully compiled and verified!" -ForegroundColor Green
Write-Host "Absolute Path: $($fileInfo.FullName)"
Write-Host "Size: $([Math]::Round($fileInfo.Length / 1MB, 2)) MB ($($fileInfo.Length) bytes)"
Write-Host "Modified: $($fileInfo.LastWriteTime)`n"

Write-Host "Available installers in installer/ directory:"
Get-ChildItem -Path $installerDir -Filter "*.exe" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, LastWriteTime, Length |
    Format-Table -AutoSize
