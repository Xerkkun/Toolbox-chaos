#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="${PYTHON:-python3}"
fi

export PYTHONUTF8="${PYTHONUTF8:-1}"
export CHAOS_MP_START_METHOD="${CHAOS_MP_START_METHOD:-forkserver}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-1}"

if ! "$PYTHON_BIN" -c "import PyQt6, numpy, matplotlib, pyqtgraph" >/dev/null 2>&1; then
    "$PYTHON_BIN" -m pip install -r requirements.txt
fi

"$PYTHON_BIN" -c "from core.native import library; library(); print('Backend nativo listo para multiproceso.')"
exec "$PYTHON_BIN" main.py
