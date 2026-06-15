#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/prepare_runtime_resources.py
python scripts/verify_packaging.py
python -m PyInstaller --noconfirm packaging/pyinstaller/chaos_toolbox.spec
echo "Linux AppDir output: dist/Chaos Toolbox"
echo "Build AppImage from dist/Chaos Toolbox with appimagetool when available."
