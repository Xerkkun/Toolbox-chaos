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

python -m pip install --upgrade -r requirements-bootstrap.txt
python -m pip install -c requirements-release.txt ".[build,webengine]"
python -c "from PySide6.QtWebEngineCore import QWebEnginePage; from PySide6.QtWebEngineWidgets import QWebEngineView; print('Qt WebEngine build dependency OK')"
python scripts/verify_distribution_compliance.py --check-installed --require-webengine --check-release-pins --check-build-pins

mkdir -p core/bin
"$compiler" -O3 -shared -fPIC -std=c11 -Wall -Wextra -Wpedantic -Werror \
    core/csrc/chaos_core.c \
    -o core/bin/libchaos_core.so \
    -lm
python scripts/verify_hafo_runtime.py
python -m pip check
python -c "import sys; from core.native import validate_precompiled_library; validate_precompiled_library(sys.argv[1]); print('Precompiled native backend OK')" core/bin/libchaos_core.so
python scripts/prepare_runtime_resources.py
python scripts/verify_packaging.py
mkdir -p build/pyinstaller
pyinstaller_log="build/pyinstaller/linux-build.log"
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

self_test_output="build/pyinstaller/linux-self-test.json"
"$executable" --self-test-output "$self_test_output"
python scripts/validate_self_test_output.py "$self_test_output"
python scripts/verify_distribution_compliance.py --artifact "$bundle" \
    --write-bundle-sbom "$bundle" "dist/chaos-toolbox-linux-bundle.cdx.json"

echo "Linux bundle output: $bundle"
echo "Linux packaged self-test: $self_test_output"
