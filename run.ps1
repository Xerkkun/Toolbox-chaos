param(
    [int]$Workers = 0
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Set-DefaultEnv {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Value
    )

    if (-not [Environment]::GetEnvironmentVariable($Name, "Process")) {
        Set-Item -Path "Env:$Name" -Value $Value
    }
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

Set-DefaultEnv "PYTHONUTF8" "1"
Set-DefaultEnv "CHAOS_MP_START_METHOD" "spawn"
Set-DefaultEnv "OMP_NUM_THREADS" "1"
Set-DefaultEnv "OPENBLAS_NUM_THREADS" "1"
Set-DefaultEnv "MKL_NUM_THREADS" "1"
Set-DefaultEnv "NUMEXPR_NUM_THREADS" "1"
Set-DefaultEnv "VECLIB_MAXIMUM_THREADS" "1"

if ($Workers -gt 0) {
    $env:CHAOS_WORKERS = [string]$Workers
}

& $python -c "import PyQt6, numpy, matplotlib, pyqtgraph" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install -r requirements.txt
}

& $python -c "from core.native import library; library(); print('Backend nativo listo para multiproceso.')"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $python main.py
exit $LASTEXITCODE
