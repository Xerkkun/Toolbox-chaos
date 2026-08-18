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

python -m pip install --upgrade -r requirements-bootstrap.txt
python -m pip install -c requirements-release.txt ".[build,webengine]"
python -c "from PySide6.QtWebEngineCore import QWebEnginePage; from PySide6.QtWebEngineWidgets import QWebEngineView; print('Qt WebEngine build dependency OK')"
python scripts/verify_distribution_compliance.py --check-installed --require-webengine --check-release-pins --check-build-pins

mkdir -p core/bin
"$compiler" -O3 -dynamiclib -fPIC -std=c11 -Wall -Wextra -Wpedantic -Werror \
    core/csrc/chaos_core.c \
    -o core/bin/libchaos_core.dylib \
    -lm
python scripts/verify_hafo_runtime.py
python -m pip check
python -c "import sys; from core.native import validate_precompiled_library; validate_precompiled_library(sys.argv[1]); print('Precompiled native backend OK')" core/bin/libchaos_core.dylib
python scripts/prepare_runtime_resources.py
python scripts/verify_packaging.py
mkdir -p build/pyinstaller
pyinstaller_log="build/pyinstaller/macos-build.log"
if ! python -m PyInstaller --noconfirm \
    packaging/pyinstaller/chaos_toolbox.spec 2>&1 | tee "$pyinstaller_log"; then
    echo "PyInstaller failed; see $pyinstaller_log." >&2
    exit 1
fi
if grep -Eiq \
    'hidden_attractors\.validation|failed to collect submodules.*hidden_attractors|collect_submodules.*hidden_attractors' \
    "$pyinstaller_log"; then
    echo "PyInstaller reported an unsupported HAFO module path." >&2
    exit 1
fi

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

self_test_output="build/pyinstaller/macos-self-test.json"
"$executable" --self-test-output "$self_test_output"
python scripts/validate_self_test_output.py "$self_test_output"
python scripts/verify_distribution_compliance.py --artifact "$app" \
    --write-bundle-sbom "$app" "dist/chaos-toolbox-macos-bundle.cdx.json"

echo "macOS .app output: $app"
echo "Create a DMG from dist/ after signing/notarization prerequisites are configured."
