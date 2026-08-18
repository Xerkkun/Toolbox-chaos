param(
    [int]$Workers = 0
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv-webengine\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "No existe .venv-webengine. Crea el entorno e instala requirements-webengine.txt primero."
    exit 1
}

function Set-DefaultEnv {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Value
    )
    if (-not [Environment]::GetEnvironmentVariable($Name, "Process")) {
        Set-Item -Path "Env:$Name" -Value $Value
    }
}

Set-DefaultEnv "PYTHONUTF8" "1"
Set-DefaultEnv "CHAOS_MP_START_METHOD" "spawn"
Set-DefaultEnv "OMP_NUM_THREADS" "1"
Set-DefaultEnv "OPENBLAS_NUM_THREADS" "1"
Set-DefaultEnv "MKL_NUM_THREADS" "1"
Set-DefaultEnv "NUMEXPR_NUM_THREADS" "1"
Set-DefaultEnv "VECLIB_MAXIMUM_THREADS" "1"

$ucrtBin = "C:\msys64\ucrt64\bin"
if (Test-Path -LiteralPath $ucrtBin) {
    $env:PATH = "$ucrtBin;$env:PATH"
}

if ($Workers -gt 0) {
    $env:CHAOS_WORKERS = [string]$Workers
}

& $python -c "import PySide6, PySide6.QtWebEngineWidgets, numpy, matplotlib, pyqtgraph"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $python scripts\verify_distribution_compliance.py --check-installed --require-webengine
if ($LASTEXITCODE -ne 0) {
    Write-Error "Recrea .venv-webengine: debe contener solo PySide6 y sus componentes WebEngine."
    exit $LASTEXITCODE
}

& $python main.py
exit $LASTEXITCODE
