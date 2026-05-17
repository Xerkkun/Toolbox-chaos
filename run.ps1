$ErrorActionPreference = "Stop"

python -c "import PyQt6, numpy, matplotlib, pyqtgraph" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install -r requirements.txt
}

python main.py
