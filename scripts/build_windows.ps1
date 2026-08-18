param(
    [switch]$AppOnly,
    [switch]$InstallerOnly,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

if ($AppOnly -and $InstallerOnly) {
    Write-Error "Parameters -AppOnly and -InstallerOnly are mutually exclusive."
    exit 1
}

# Find Python
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

# --- 1. BUILD APP STAGE ---
if (-not $InstallerOnly) {
    Write-Host "=== Step 1/2: Building Executable (PyInstaller) ===" -ForegroundColor Cyan
    Invoke-CheckedPython -Arguments @("scripts\prepare_runtime_resources.py")
    Invoke-CheckedPython -Arguments @("scripts\verify_packaging.py")
    
    # Pass switch explicitly using colon syntax
    & packaging\windows\build.ps1 -SkipInstall:$SkipInstall
    if (-not $?) {
        throw "PyInstaller build script failed."
    }
}

# --- 2. BUILD INSTALLER STAGE ---
if (-not $AppOnly) {
    Write-Host "=== Step 2/2: Building Installer (Inno Setup) ===" -ForegroundColor Cyan
    
    $exePath = Join-Path $repoRoot "dist\Chaos Toolbox\Chaos Toolbox.exe"
    if (-not (Test-Path -LiteralPath $exePath)) {
        Write-Error "Cannot build installer: PyInstaller executable was not found at $exePath."
        Write-Host "Please build the executable first using '.\scripts\build_windows.ps1 -AppOnly'" -ForegroundColor Yellow
        exit 1
    }
    
    # Run the installer compiler script
    & scripts\build_windows_installer.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Installer build script failed."
        exit 1
    }
}

# --- 3. POST-BUILD VERIFICATION STAGE ---
if (-not $AppOnly -and -not $InstallerOnly) {
    Write-Host "=== Step 3/3: Running Post-Build Verifications ===" -ForegroundColor Cyan

    $appVersion = (Invoke-CheckedPython -Arguments @("-c", "from core.app_metadata import APP_VERSION; print(APP_VERSION)") | Out-String).Trim()
    $expectedInstaller = Join-Path $repoRoot "installer\chaos-toolbox-v$appVersion-windows-x64-setup.exe"
    $expectedExe = Join-Path $repoRoot "dist\Chaos Toolbox\Chaos Toolbox.exe"

    if (-not (Test-Path -LiteralPath $expectedExe)) {
        throw "Verification failed: Executable missing at $expectedExe"
    }

    if (-not (Test-Path -LiteralPath $expectedInstaller)) {
        throw "Verification failed: Installer missing at $expectedInstaller"
    }

    $genVersionFile = Join-Path $repoRoot "packaging\windows\generated_version.iss"
    $genVersionContent = Get-Content -Raw -LiteralPath $genVersionFile
    if ($genVersionContent -notlike "*$appVersion*") {
        throw "Verification failed: generated_version.iss does not contain version '$appVersion'"
    }

    # Verify no forbidden resources are present in the bundle
    Write-Host "Verifying packaging policies and running bundle size report..."
    Invoke-CheckedPython -Arguments @("scripts\verify_packaging.py")
    Invoke-CheckedPython -Arguments @(
        "scripts\verify_distribution_compliance.py",
        "--artifact",
        "dist\Chaos Toolbox"
    )
    Invoke-CheckedPython -Arguments @("scripts\bundle_size_report.py")
    
    Write-Host "`nAll post-build verifications passed successfully!" -ForegroundColor Green
}
