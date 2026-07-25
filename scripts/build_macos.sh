#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

compiler="${CC:-}"
if [[ -z "$compiler" ]]; then
    compiler="$(command -v clang || command -v gcc || true)"
fi
if [[ -z "$compiler" ]]; then
    echo "A C compiler (clang or gcc) is required." >&2
    exit 1
fi

mkdir -p core/bin
"$compiler" -O3 -dynamiclib -fPIC -std=c11 \
    core/csrc/chaos_core.c \
    -o core/bin/libchaos_core.dylib \
    -lm
python -c "from core.native import library; library(); print('Native backend OK')"
python scripts/prepare_runtime_resources.py
python scripts/verify_packaging.py
python -m PyInstaller --noconfirm packaging/pyinstaller/chaos_toolbox.spec

app="dist/Chaos Toolbox.app"
executable="$app/Contents/MacOS/Chaos Toolbox"
if [[ ! -x "$executable" ]]; then
    echo "PyInstaller did not create the expected macOS app: $executable" >&2
    exit 1
fi
if ! find "$app" -type f -name libchaos_core.dylib -print -quit | grep -q .; then
    echo "The macOS app does not contain libchaos_core.dylib." >&2
    exit 1
fi

echo "macOS .app output: $app"
echo "Create a DMG from dist/ after signing/notarization prerequisites are configured."
