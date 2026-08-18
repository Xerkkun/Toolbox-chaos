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

& $python -c "import PySide6, numpy, matplotlib, pyqtgraph" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install -r requirements.txt
}

& $python -c "import PySide6, numpy, matplotlib, pyqtgraph" 2>$null
if ($LASTEXITCODE -ne 0 -and $python -ne "python") {
    Write-Host "El entorno .venv local no tiene las dependencias de la app; usando python del sistema."
    $python = "python"
    & $python -c "import PySide6, numpy, matplotlib, pyqtgraph"
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudieron cargar PySide6, numpy, matplotlib y pyqtgraph. Instala requirements.txt en el Python elegido."
    exit $LASTEXITCODE
}

& $python scripts\verify_distribution_compliance.py --check-installed
if ($LASTEXITCODE -ne 0) {
    Write-Error "El entorno contiene una vinculacion Qt heredada o una instalacion PySide6 incompleta. Recrea el entorno antes de ejecutar."
    exit $LASTEXITCODE
}

& $python -c "from core.native import library; library(); print('Backend nativo listo para multiproceso.')"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $python main.py
exit $LASTEXITCODE
