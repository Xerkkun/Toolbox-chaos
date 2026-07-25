#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

compiler="${CC:-}"
if [[ -z "$compiler" ]]; then
    compiler="$(command -v gcc || command -v clang || true)"
fi
if [[ -z "$compiler" ]]; then
    echo "A C compiler (gcc or clang) is required." >&2
    exit 1
fi

mkdir -p core/bin
"$compiler" -O3 -shared -fPIC -std=c11 \
    core/csrc/chaos_core.c \
    -o core/bin/libchaos_core.so \
    -lm
python -c "from core.native import library; library(); print('Native backend OK')"
python scripts/prepare_runtime_resources.py
python scripts/verify_packaging.py
python -m PyInstaller --noconfirm packaging/pyinstaller/chaos_toolbox.spec

bundle="dist/Chaos Toolbox"
executable="$bundle/Chaos Toolbox"
if [[ ! -x "$executable" ]]; then
    echo "PyInstaller did not create the expected Linux bundle: $executable" >&2
    exit 1
fi
if ! find "$bundle" -type f -name libchaos_core.so -print -quit | grep -q .; then
    echo "The Linux bundle does not contain libchaos_core.so." >&2
    exit 1
fi

echo "Linux bundle output: $bundle"
echo "Build AppImage from dist/Chaos Toolbox with appimagetool when available."
