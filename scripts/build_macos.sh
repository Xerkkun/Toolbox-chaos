#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/prepare_runtime_resources.py
python scripts/verify_packaging.py
python -m PyInstaller --noconfirm packaging/pyinstaller/chaos_toolbox.spec
echo "macOS .app output: dist/Chaos Toolbox.app"
echo "Create a DMG from dist/ after signing/notarization prerequisites are configured."
