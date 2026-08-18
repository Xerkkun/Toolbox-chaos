param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
Set-Location -LiteralPath $repoRoot

function Find-Python {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return "python"
    }
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($python) {
        return "py"
    }
    throw "Python is required on the build machine to create the distributable."
}

function Test-VenvPip {
    param([Parameter(Mandatory=$true)][string]$PythonPath)

    if (-not (Test-Path -LiteralPath $PythonPath) -and -not (Get-Command $PythonPath -ErrorAction SilentlyContinue)) {
        return $false
    }
    $oldErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $PythonPath -m pip --version > $null 2>&1
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Test-BuildRequirements {
    param([Parameter(Mandatory=$true)][string]$PythonPath)

    $oldErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $PythonPath -c "import cyclonedx_py, PySide6, PySide6.QtWebEngineCore, PySide6.QtWebEngineWidgets, numpy, matplotlib, pyqtgraph, PyInstaller" > $null 2>&1
        if ($LASTEXITCODE -ne 0) { return $false }
        & $PythonPath (Join-Path $repoRoot "scripts\verify_hafo_runtime.py") > $null 2>&1
        if ($LASTEXITCODE -ne 0) { return $false }
        & $PythonPath -m pip check > $null 2>&1
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Clear-GeneratedDirectory {
    param([Parameter(Mandatory=$true)][string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $repoFullPath = [System.IO.Path]::GetFullPath($repoRoot)
    if (-not $fullPath.StartsWith($repoFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clear generated directory outside the repository: $fullPath"
    }
    if (-not (Test-Path -LiteralPath $fullPath)) {
        return
    }

    Get-ChildItem -LiteralPath $fullPath -Recurse -Force | ForEach-Object {
        try {
            $_.Attributes = "Normal"
        } catch {
            Write-Warning "Could not normalize attributes for $($_.FullName): $($_.Exception.Message)"
        }
    }
    try {
        (Get-Item -LiteralPath $fullPath -Force).Attributes = "Normal"
    } catch {
        Write-Warning "Could not normalize attributes for ${fullPath}: $($_.Exception.Message)"
    }
    Remove-Item -LiteralPath $fullPath -Recurse -Force
}

function Find-CCompiler {
    $candidates = @(
        "gcc",
        "clang",
        "C:\msys64\ucrt64\bin\gcc.exe",
        "C:\msys64\mingw64\bin\gcc.exe",
        "C:\msys64\usr\bin\gcc.exe"
    )

    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }

    throw "No gcc/clang compiler was found on the build machine. Install MinGW/MSYS2 or add gcc/clang to PATH before building."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

$venvDir = Join-Path $repoRoot ".venv-build"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $venvDir "bin\python.exe"
}

if ((Test-Path -LiteralPath $venvDir) -and -not (Test-VenvPip -PythonPath $venvPython)) {
    throw ".venv-build exists but is not a usable Python environment. Recreate that dedicated build environment."
}

if (-not (Test-VenvPip -PythonPath $venvPython)) {
    $bootstrapPython = Find-Python
    try {
        Invoke-Checked -FilePath $bootstrapPython -Arguments @("-m", "venv", $venvDir)
        $venvPython = Join-Path $venvDir "Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $venvPython)) {
            $venvPython = Join-Path $venvDir "bin\python.exe"
        }
    } catch {
        throw "Could not create the dedicated build environment at ${venvDir}: $($_.Exception.Message)"
    }
}

if ($venvDir) {
    $activate = Join-Path $venvDir "Scripts\Activate.ps1"
    if (-not (Test-Path -LiteralPath $activate)) {
        $activate = Join-Path $venvDir "bin\Activate.ps1"
    }
    . $activate
}

if (-not (Test-VenvPip -PythonPath $venvPython)) {
    throw "The selected Python interpreter does not provide pip: $venvPython"
}

if (-not $SkipInstall) {
    try {
        Invoke-Checked -FilePath $venvPython -Arguments @(
            "-m", "pip", "install", "--upgrade", "-r", "requirements-bootstrap.txt"
        )
        Invoke-Checked -FilePath $venvPython -Arguments @("-m", "pip", "install", "-c", "requirements-release.txt", ".[build,webengine]")
    } catch {
        if (Test-BuildRequirements -PythonPath $venvPython) {
            Write-Warning "pip install failed, but build requirements are already importable; continuing."
        } else {
            throw
        }
    }
}

if (-not (Test-BuildRequirements -PythonPath $venvPython)) {
    throw "Build requirements, HAFO >=1.1,<2 API, or pip dependency consistency are invalid."
}
Invoke-Checked -FilePath $venvPython -Arguments @(
    (Join-Path $repoRoot "scripts\verify_distribution_compliance.py"),
    "--check-installed",
    "--require-webengine",
    "--check-release-pins",
    "--check-build-pins"
)

$dllDir = Join-Path $repoRoot "core\bin"
New-Item -ItemType Directory -Force -Path $dllDir | Out-Null

$compiler = Find-CCompiler
$source = Join-Path $repoRoot "core\csrc\chaos_core.c"
$dll = Join-Path $dllDir "chaos_core.dll"
Invoke-Checked -FilePath $compiler -Arguments @(
    "-O3", "-shared", "-std=c11",
    "-frandom-seed=chaos-core-v2",
    "-Wl,--no-insert-timestamp,--image-base,0x180000000",
    "-Wall", "-Wextra", "-Wpedantic", "-Werror",
    $source, "-o", $dll, "-lm"
)

Invoke-Checked -FilePath $venvPython -Arguments @(
    "-c",
    "import sys; from core.native import validate_precompiled_library; validate_precompiled_library(sys.argv[1]); print('Precompiled native backend OK')",
    $dll
)

$pyInstallerWorkApp = Join-Path $repoRoot "build\pyinstaller\Chaos Toolbox"
$distApp = Join-Path $repoRoot "dist\Chaos Toolbox"

Write-Host "Verifying release cleanliness..."
Invoke-Checked -FilePath $venvPython -Arguments @(Join-Path $repoRoot "tools\check_no_sprott_originals_in_release.py")
Invoke-Checked -FilePath $venvPython -Arguments @(Join-Path $repoRoot "scripts\prepare_runtime_resources.py")
Invoke-Checked -FilePath $venvPython -Arguments @(Join-Path $repoRoot "scripts\verify_packaging.py")

$appVersion = (& $venvPython -c "from core.app_metadata import APP_VERSION; print(APP_VERSION)").Trim()
$versionInclude = Join-Path $repoRoot "packaging\windows\generated_version.iss"
Set-Content -LiteralPath $versionInclude -Encoding ASCII -Value "#define MyAppVersion `"$appVersion`""

Clear-GeneratedDirectory -Path $pyInstallerWorkApp
Clear-GeneratedDirectory -Path $distApp

$pyInstallerArgs = @(
    "--noconfirm",
    "--distpath", "dist",
    "--workpath", "build\pyinstaller",
    "packaging\pyinstaller\chaos_toolbox.spec"
)
$pyInstallerLog = Join-Path $repoRoot "build\pyinstaller\windows-build.log"
$oldErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    & $venvPython -m PyInstaller @pyInstallerArgs 2>&1 |
        Tee-Object -FilePath $pyInstallerLog
    $pyInstallerExitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $oldErrorActionPreference
}
if ($pyInstallerExitCode -ne 0) {
    throw "PyInstaller failed with exit code $pyInstallerExitCode. See $pyInstallerLog."
}
$criticalPyInstallerWarnings = Select-String -LiteralPath $pyInstallerLog -Pattern @(
    'hidden_attractors\.validation',
    'failed to collect submodules.*hidden_attractors',
    'collect_submodules.*hidden_attractors'
) -CaseSensitive:$false
if ($criticalPyInstallerWarnings) {
    throw "PyInstaller reported an unsupported HAFO module path. See $pyInstallerLog."
}

$exePath = Join-Path $repoRoot "dist\Chaos Toolbox\Chaos Toolbox.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "PyInstaller finished but $exePath was not created."
}

$selfTestOutput = Join-Path $repoRoot "build\pyinstaller\windows-self-test.json"
Invoke-Checked -FilePath $exePath -Arguments @('--self-test-output', $selfTestOutput)
Invoke-Checked -FilePath $venvPython -Arguments @(
    (Join-Path $repoRoot 'scripts\validate_self_test_output.py'),
    $selfTestOutput
)
Invoke-Checked -FilePath $venvPython -Arguments @(
    (Join-Path $repoRoot 'scripts\verify_distribution_compliance.py'),
    '--artifact',
    $distApp,
    '--write-bundle-sbom',
    $distApp,
    (Join-Path $repoRoot 'dist\chaos-toolbox-windows-bundle.cdx.json')
)

Write-Host "Built $exePath"
