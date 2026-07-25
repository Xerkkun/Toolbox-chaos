[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$MachineProfile,

    [string]$ToolboxRoot = $env:TOOLBOX_CHAOS_ROOT,

    [string]$OutputDir,

    [switch]$CheckOnly,

    [switch]$AllowAppOnly
)

$ErrorActionPreference = "Stop"
$protocolDir = $PSScriptRoot
$benchmarkScript = Join-Path $protocolDir "run_benchmarks.py"

function Test-ToolboxRoot {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (
        (Test-Path -LiteralPath (Join-Path $Path "main.py") -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $Path "core\lorenz.py") -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $Path "requirements-build.txt") -PathType Leaf)
    )
}

function Resolve-ToolboxRoot {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        $resolved = (Resolve-Path -LiteralPath $ExplicitPath).Path
        if (-not (Test-ToolboxRoot -Path $resolved)) {
            throw "ToolboxRoot does not contain a Toolbox chaos checkout: $resolved"
        }
        return $resolved
    }

    $cursor = Get-Item -LiteralPath $protocolDir
    while ($null -ne $cursor) {
        foreach ($name in @("Toolbox chaos", "Toolbox-chaos")) {
            $candidate = Join-Path $cursor.FullName $name
            if (Test-ToolboxRoot -Path $candidate) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        }
        $cursor = $cursor.Parent
    }

    throw "Toolbox chaos was not found. Pass -ToolboxRoot or define TOOLBOX_CHAOS_ROOT."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Find-BootstrapPython {
    $py = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($py) {
        return [pscustomobject]@{
            FilePath = $py.Source
            Prefix = @("-3")
        }
    }

    $python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command "python" -ErrorAction SilentlyContinue
    }
    if ($python) {
        return [pscustomobject]@{
            FilePath = $python.Source
            Prefix = @()
        }
    }

    throw "Python 3 was not found. Install Python 3.10 or newer and enable the py launcher or PATH entry."
}

function Find-VenvPython {
    param([Parameter(Mandatory = $true)][string]$VenvPath)

    foreach ($relative in @("Scripts\python.exe", "bin\python.exe")) {
        $candidate = Join-Path $VenvPath $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    return $null
}

function Find-CCompiler {
    foreach ($candidate in @(
        "gcc.exe",
        "clang.exe",
        "C:\msys64\ucrt64\bin\gcc.exe",
        "C:\msys64\mingw64\bin\gcc.exe"
    )) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }
    return $null
}

function Find-InnoSetup {
    if ($env:INNO_SETUP_ISCC -and (Test-Path -LiteralPath $env:INNO_SETUP_ISCC -PathType Leaf)) {
        return (Resolve-Path -LiteralPath $env:INNO_SETUP_ISCC).Path
    }

    $command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return $candidate
        }
    }
    return $null
}

function Assert-BuildArchitecture {
    param(
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [string[]]$PythonPrefix = @(),
        [Parameter(Mandatory = $true)][string]$CompilerPath
    )

    $pythonBits = (& $PythonPath @PythonPrefix -c "import struct; print(struct.calcsize('P') * 8)").Trim()
    if ($LASTEXITCODE -ne 0 -or $pythonBits -ne "64") {
        throw "A 64-bit Python interpreter is required; detected pointer width: $pythonBits."
    }
    $compilerTarget = (& $CompilerPath -dumpmachine).Trim()
    if ($LASTEXITCODE -ne 0 -or $compilerTarget -notmatch "(?i)(x86_64|amd64)") {
        throw "A Windows x64 compiler target is required; detected: $compilerTarget."
    }
    Write-Host "Build architecture: Python ${pythonBits}-bit / compiler $compilerTarget"
}

function Assert-TargetMachine {
    param([Parameter(Mandatory = $true)][object]$Profile)

    $env:CHAOS_MACHINE_IDENTITY_VERIFIED = ""
    if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
        throw "This launcher must run on Windows."
    }

    $manufacturer = ""
    $model = ""
    $systemFamily = ""
    try {
        $computer = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
        $manufacturer = [string]$computer.Manufacturer
        $model = [string]$computer.Model
        $systemFamily = [string]$computer.SystemFamily
    } catch {
        Write-Warning "CIM identity lookup failed; trying the read-only BIOS registry values. $($_.Exception.Message)"
        try {
            $bios = Get-ItemProperty `
                -LiteralPath "HKLM:\HARDWARE\DESCRIPTION\System\BIOS" `
                -ErrorAction Stop
            $manufacturer = [string]$bios.SystemManufacturer
            $model = [string]$bios.SystemProductName
            $systemFamily = [string]$bios.SystemFamily
        } catch {
            Write-Warning "Machine identity could not be read. The benchmark inventory will record whatever the OS exposes. $($_.Exception.Message)"
            return
        }
    }

    if (-not $manufacturer -and -not $model -and -not $systemFamily) {
        Write-Warning "Machine identity fields are empty. The launcher cannot validate this profile before the benchmark."
        return
    }

    $expectedManufacturer = [string]$Profile.manufacturer
    $expectedModel = [string]$Profile.model

    if (
        $expectedManufacturer -and
        $manufacturer -and
        $manufacturer.IndexOf($expectedManufacturer, [System.StringComparison]::OrdinalIgnoreCase) -lt 0
    ) {
        throw "This machine does not match the benchmark profile. Expected manufacturer '$expectedManufacturer'; detected '$manufacturer'."
    }
    if ($expectedManufacturer -and -not $manufacturer) {
        Write-Warning "Manufacturer is unavailable; expected '$expectedManufacturer' could not be validated."
    }
    if (
        $expectedModel -and
        $model -and
        -not $model.Equals($expectedModel, [System.StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "This machine does not match the benchmark profile. Expected model '$expectedModel'; detected '$model'."
    }
    if ($expectedModel -and -not $model) {
        Write-Warning "Model is unavailable; expected '$expectedModel' could not be validated."
    }
    if (
        [string]$Profile.machine_id -eq "WINDOWS-ASUS-TUF" -and
        ($model -or $systemFamily) -and
        "$model $systemFamily" -notmatch "(?i)\bTUF\b"
    ) {
        throw "The ASUS benchmark profile requires a TUF model. Detected model '$model' and family '$systemFamily'."
    }
    if (
        [string]$Profile.machine_id -eq "WINDOWS-ASUS-TUF" -and
        -not $model -and
        -not $systemFamily
    ) {
        Write-Warning "Model and SystemFamily are unavailable; the TUF family could not be validated."
    }

    Write-Host "Detected machine: $manufacturer / $model / $systemFamily"
    $env:CHAOS_MACHINE_IDENTITY_VERIFIED = "windows-cim-or-bios-registry"
}

$repoRoot = Resolve-ToolboxRoot -ExplicitPath $ToolboxRoot
$profilePath = (Resolve-Path -LiteralPath $MachineProfile).Path
$profile = Get-Content -Raw -Encoding UTF8 -LiteralPath $profilePath | ConvertFrom-Json
if (-not $profile.machine_id) {
    throw "Machine profile does not define machine_id: $profilePath"
}
if (-not (Test-Path -LiteralPath $benchmarkScript -PathType Leaf)) {
    throw "Benchmark script not found: $benchmarkScript"
}
Assert-TargetMachine -Profile $profile

$venvDir = Join-Path $repoRoot ".venv"
$venvPython = Find-VenvPython -VenvPath $venvDir
$bootstrap = $null
if (-not $venvPython) {
    $bootstrap = Find-BootstrapPython
}
$compiler = Find-CCompiler
$innoSetup = Find-InnoSetup

if ($CheckOnly) {
    $checkPython = if ($venvPython) { $venvPython } else { $bootstrap.FilePath }
    $checkPrefix = if ($venvPython) { @() } else { @($bootstrap.Prefix) }
    if (-not $compiler) {
        throw "No gcc/clang compiler was found. Install MSYS2 UCRT64 or another compatible compiler."
    }
    if (-not $innoSetup -and -not $AllowAppOnly) {
        throw "Inno Setup 6 was not found. Install it, set INNO_SETUP_ISCC, or opt in to -AllowAppOnly."
    }
    Assert-BuildArchitecture `
        -PythonPath $checkPython `
        -PythonPrefix $checkPrefix `
        -CompilerPath $compiler

    Write-Host "Toolbox root: $repoRoot"
    Write-Host "Machine profile: $profilePath"
    Write-Host "Python used for check: $checkPython"
    Write-Host "C compiler: $compiler"
    Write-Host "Inno Setup: $(if ($innoSetup) { $innoSetup } else { 'not found; the app can be built but not the setup installer' })"

    Invoke-Checked -FilePath $checkPython -Arguments (
        $checkPrefix + @(
        $benchmarkScript,
        "--toolbox-root", $repoRoot,
        "--machine-profile", $profilePath,
        "--startup-mode", "source",
        "--check-config"
        )
    )
    exit 0
}

if (-not $venvPython) {
    if (-not $bootstrap) {
        $bootstrap = Find-BootstrapPython
    }
    Invoke-Checked -FilePath $bootstrap.FilePath -Arguments (
        @($bootstrap.Prefix) + @("-m", "venv", $venvDir)
    )
    $venvPython = Find-VenvPython -VenvPath $venvDir
}
if (-not $venvPython) {
    throw "The virtual environment was created without a usable Python executable: $venvDir"
}
if (-not $compiler) {
    throw "No gcc/clang compiler was found. Install MSYS2 UCRT64 or another compatible compiler."
}
Assert-BuildArchitecture -PythonPath $venvPython -CompilerPath $compiler
$env:CHAOS_NATIVE_COMPILER = (& $compiler --version | Select-Object -First 1)
$env:CHAOS_NATIVE_CFLAGS = "-O3 -shared -std=c11 -lm"

Invoke-Checked -FilePath $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked -FilePath $venvPython -Arguments @(
    "-m", "pip", "install", "-r", (Join-Path $repoRoot "requirements-build.txt")
)

$buildScript = Join-Path $repoRoot "scripts\build_windows.ps1"
& $buildScript -AppOnly -SkipInstall
if (-not $?) {
    throw "Windows application build failed."
}

$executable = Join-Path $repoRoot "dist\Chaos Toolbox\Chaos Toolbox.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Packaged executable was not created: $executable"
}
$peMachine = (& $venvPython -c "import pefile,sys; print(hex(pefile.PE(sys.argv[1], fast_load=True).FILE_HEADER.Machine))" $executable).Trim()
if ($LASTEXITCODE -ne 0 -or $peMachine -ne "0x8664") {
    throw "The packaged executable is not PE x64 (machine 0x8664): $peMachine"
}
$selfTestPath = Join-Path `
    ([System.IO.Path]::GetTempPath()) `
    ("chaos-toolbox-self-test-" + [guid]::NewGuid().ToString("N") + ".json")
try {
    $selfTestProcess = Start-Process `
        -FilePath $executable `
        -ArgumentList "--self-test-output `"$selfTestPath`"" `
        -Wait `
        -PassThru `
        -WindowStyle Hidden
    if ($selfTestProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $selfTestPath -PathType Leaf)) {
        throw "The packaged numerical self-test failed with exit code $($selfTestProcess.ExitCode)."
    }
    $selfTest = Get-Content -Raw -Encoding UTF8 -LiteralPath $selfTestPath | ConvertFrom-Json
    if ($selfTest.status -ne "ok" -or -not $selfTest.all_finite) {
        throw "The packaged numerical self-test returned an invalid result."
    }
    $env:CHAOS_PACKAGED_SELF_TEST = "passed"
}
finally {
    if (Test-Path -LiteralPath $selfTestPath) {
        Remove-Item -LiteralPath $selfTestPath -Force
    }
}

$installerArtifact = $null
if ($innoSetup) {
    $env:INNO_SETUP_ISCC = $innoSetup
    & $buildScript -InstallerOnly
    if (-not $?) {
        throw "Windows installer build failed."
    }
    $appVersion = (& $venvPython -c "from core.app_metadata import APP_VERSION; print(APP_VERSION)").Trim()
    $installerCandidate = Join-Path $repoRoot "installer\chaos-toolbox-v$appVersion-windows-x64-setup.exe"
    if (-not (Test-Path -LiteralPath $installerCandidate -PathType Leaf)) {
        throw "Installer build completed without the expected artifact: $installerCandidate"
    }
    $installerArtifact = $installerCandidate
} else {
    if (-not $AllowAppOnly) {
        throw "Inno Setup 6 was not found. Install it, set INNO_SETUP_ISCC, or opt in to -AllowAppOnly."
    }
    Write-Warning "Inno Setup was not found. -AllowAppOnly was supplied, so no setup .exe was created."
}

if (-not $OutputDir) {
    $profileSlug = [System.IO.Path]::GetFileNameWithoutExtension($profilePath)
    $timestamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $protocolParent = Split-Path -Parent $protocolDir
    $resultsRoot = if (
        (Split-Path -Leaf $protocolParent).Equals(
            "supplementary",
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        Join-Path $protocolParent "benchmark_results"
    } else {
        Join-Path $protocolDir "results"
    }
    $OutputDir = Join-Path $resultsRoot "$profileSlug\$timestamp"
}
$outputPath = [System.IO.Path]::GetFullPath($OutputDir)
if (Test-Path -LiteralPath $outputPath) {
    throw "Benchmark output directory already exists: $outputPath"
}

$env:PYTHONUTF8 = "1"
$env:CHAOS_MP_START_METHOD = "spawn"
$env:CHAOS_WORKERS = "1"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$benchmarkArguments = @(
    $benchmarkScript,
    "--toolbox-root", $repoRoot,
    "--machine-profile", $profilePath,
    "--output-dir", $outputPath,
    "--startup-mode", "exe",
    "--executable", $executable
)
if ($installerArtifact) {
    $benchmarkArguments += @("--installer-artifact", $installerArtifact)
}
Invoke-Checked -FilePath $venvPython -Arguments $benchmarkArguments

foreach ($requiredJson in @(
    "run_manifest.json",
    "startup_raw.json",
    "calculations_raw.json",
    "summary.json",
    "benchmark_result.json"
)) {
    $artifact = Join-Path $outputPath $requiredJson
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "Benchmark finished without required JSON artifact: $artifact"
    }
}

Write-Host "Benchmark JSON directory: $outputPath"
