#!/usr/bin/env bash
set -euo pipefail

protocol_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
profile_path="${protocol_dir}/macos-16gb.json"
benchmark_script="${protocol_dir}/run_benchmarks.py"
toolbox_root="${TOOLBOX_CHAOS_ROOT:-}"
output_dir=""
check_only=0

export PYTHONUTF8=1
export CHAOS_MP_START_METHOD="${CHAOS_MP_START_METHOD:-spawn}"
export CHAOS_WORKERS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

usage() {
    printf '%s\n' \
        "Usage: $0 [--toolbox-root PATH] [--output-dir PATH] [--check-only]" \
        "" \
        "Builds a native macOS .app and local benchmark DMG, then runs the" \
        "unchanged benchmark protocol with the macos-16gb machine profile."
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

assert_target_memory() {
    local memory_bytes minimum_bytes maximum_bytes
    memory_bytes="$(sysctl -n hw.memsize 2>/dev/null)" ||
        die "Could not read physical memory from sysctl hw.memsize."
    [[ "$memory_bytes" =~ ^[0-9]+$ ]] ||
        die "Unexpected hw.memsize value: $memory_bytes"

    minimum_bytes=$((15 * 1024 * 1024 * 1024))
    maximum_bytes=$((17 * 1024 * 1024 * 1024))
    ((memory_bytes >= minimum_bytes && memory_bytes <= maximum_bytes)) ||
        die "This profile requires approximately 16 GiB of RAM; hw.memsize reports ${memory_bytes} bytes."

    printf 'Physical memory: %s bytes (16 GiB profile accepted)\n' "$memory_bytes"
}

is_toolbox_root() {
    [[ -f "$1/main.py" && -f "$1/core/lorenz.py" && -f "$1/requirements-build.txt" ]]
}

discover_toolbox_root() {
    local cursor candidate
    cursor="$protocol_dir"
    while [[ "$cursor" != "/" ]]; do
        for candidate in "$cursor/Toolbox chaos" "$cursor/Toolbox-chaos"; do
            if is_toolbox_root "$candidate"; then
                (cd -- "$candidate" && pwd -P)
                return 0
            fi
        done
        cursor="$(dirname -- "$cursor")"
    done
    return 1
}

while (($#)); do
    case "$1" in
        --toolbox-root)
            (($# >= 2)) || die "--toolbox-root requires a path"
            toolbox_root="$2"
            shift 2
            ;;
        --output-dir)
            (($# >= 2)) || die "--output-dir requires a path"
            output_dir="$2"
            shift 2
            ;;
        --check-only)
            check_only=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1"
            ;;
    esac
done

[[ "$(uname -s)" == "Darwin" ]] || die "This script must run on macOS."

if [[ -z "$toolbox_root" ]]; then
    toolbox_root="$(discover_toolbox_root)" ||
        die "Toolbox chaos was not found. Pass --toolbox-root or define TOOLBOX_CHAOS_ROOT."
fi
toolbox_root="$(cd -- "$toolbox_root" && pwd -P)"
is_toolbox_root "$toolbox_root" || die "Not a Toolbox chaos checkout: $toolbox_root"

require_command python3
require_command clang
require_command hdiutil
require_command plutil
require_command codesign
require_command file
assert_target_memory
host_arch="$(uname -m)"
python_arch="$(python3 -c 'import platform; print(platform.machine())')"
python_bits="$(python3 -c 'import struct; print(struct.calcsize("P") * 8)')"
[[ "$python_bits" == "64" && "$python_arch" == "$host_arch" ]] ||
    die "Python architecture (${python_arch}, ${python_bits}-bit) does not match the native host (${host_arch}). Do not build under Rosetta."
export CHAOS_MACHINE_IDENTITY_VERIFIED="macos-system-and-hw.memsize"
export CHAOS_NATIVE_COMPILER="$(clang --version | sed -n '1p')"
export CHAOS_NATIVE_CFLAGS="-O3 -dynamiclib -fPIC -std=c11 -lm"

venv_dir="${toolbox_root}/.venv-benchmark-macos"
venv_python="${venv_dir}/bin/python"
check_python="$(command -v python3)"
if [[ -x "$venv_python" ]]; then
    check_python="$venv_python"
fi

if ((check_only)); then
    "$check_python" -c "import json, numpy, PySide6; json.load(open(r'${profile_path}', encoding='utf-8'))"
    "$check_python" "$benchmark_script" \
        --toolbox-root "$toolbox_root" \
        --machine-profile "$profile_path" \
        --startup-mode source \
        --check-config
    printf 'Check-only completed; no environment, bundle, DMG or result directory was created.\n'
    exit 0
fi

python3 -m venv "$venv_dir"
"$venv_python" -m pip install --upgrade pip
"$venv_python" -m pip install -r "${toolbox_root}/requirements-build.txt"

native_dir="${toolbox_root}/core/bin"
native_library="${native_dir}/libchaos_core.dylib"
mkdir -p -- "$native_dir"
clang -O3 -dynamiclib -fPIC -std=c11 \
    "${toolbox_root}/core/csrc/chaos_core.c" \
    -o "$native_library" \
    -lm

(
    cd -- "$toolbox_root"
    "$venv_python" -c "from core.native import library; library(); print('Native backend OK')"
    PATH="${venv_dir}/bin:${PATH}" bash scripts/build_macos.sh
)

collection_dir="${toolbox_root}/dist/Chaos Toolbox"
app_dir="${toolbox_root}/dist/Chaos Toolbox.app"

if [[ ! -d "$app_dir" ]]; then
    [[ -x "${collection_dir}/Chaos Toolbox" ]] ||
        die "PyInstaller did not create the expected collection: $collection_dir"

    rm -rf -- "$app_dir"
    mkdir -p -- "${app_dir}/Contents/MacOS" "${app_dir}/Contents/Resources"
    cp -R "${collection_dir}/." "${app_dir}/Contents/MacOS/"

    plist="${app_dir}/Contents/Info.plist"
    plutil -create xml1 "$plist"
    plutil -insert CFBundleName -string "Chaos Toolbox" "$plist"
    plutil -insert CFBundleDisplayName -string "Chaos Toolbox" "$plist"
    plutil -insert CFBundleIdentifier -string "org.fyskode.chaostoolbox" "$plist"
    plutil -insert CFBundleExecutable -string "Chaos Toolbox" "$plist"
    plutil -insert NSHighResolutionCapable -bool true "$plist"
fi

startup_executable="${app_dir}/Contents/MacOS/Chaos Toolbox"
[[ -x "$startup_executable" ]] ||
    die "The .app does not contain its startup executable: $startup_executable"
file "$startup_executable" | grep -q "$host_arch" ||
    die "The packaged executable does not contain the native architecture: $host_arch"

runtime_resources="$(
    find "${app_dir}/Contents" -type d -path '*/resources/bundled' -print -quit
)"
if [[ -n "$runtime_resources" ]]; then
    runtime_root="$(dirname -- "$(dirname -- "$runtime_resources")")"
elif [[ -d "${app_dir}/Contents/Frameworks" ]]; then
    runtime_root="${app_dir}/Contents/Frameworks"
else
    runtime_root="${app_dir}/Contents/MacOS/_internal"
fi
mkdir -p -- "${runtime_root}/core/bin"
cp -f -- "$native_library" "${runtime_root}/core/bin/libchaos_core.dylib"
[[ -f "${runtime_root}/core/bin/libchaos_core.dylib" ]] ||
    die "The packaged app does not contain libchaos_core.dylib."
file "${runtime_root}/core/bin/libchaos_core.dylib" | grep -q "$host_arch" ||
    die "The packaged native library does not contain architecture: $host_arch"

app_version="$(
    cd -- "$toolbox_root"
    "$venv_python" -c "from core.app_metadata import APP_VERSION; print(APP_VERSION)"
)"
plist="${app_dir}/Contents/Info.plist"
if [[ -f "$plist" ]]; then
    plutil -replace CFBundleShortVersionString -string "$app_version" "$plist" 2>/dev/null ||
        plutil -insert CFBundleShortVersionString -string "$app_version" "$plist"
    plutil -replace CFBundleVersion -string "$app_version" "$plist" 2>/dev/null ||
        plutil -insert CFBundleVersion -string "$app_version" "$plist"
fi

# Ad-hoc signing is sufficient for a local benchmark artifact. Public
# distribution still requires an Apple Developer identity and notarization.
codesign --force --deep --sign - "$app_dir"
codesign --verify --deep --strict "$app_dir"

self_test_json="$(mktemp "${TMPDIR:-/tmp}/chaos-toolbox-self-test.XXXXXX")"
trap 'rm -f -- "$self_test_json"' EXIT
"$startup_executable" --self-test-output "$self_test_json"
"$venv_python" -c \
    "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); assert d['status']=='ok' and d['all_finite']" \
    "$self_test_json"
rm -f -- "$self_test_json"
trap - EXIT
export CHAOS_PACKAGED_SELF_TEST="passed"

dmg_path="${toolbox_root}/dist/chaos-toolbox-v${app_version}-macos.dmg"
rm -f -- "$dmg_path"
dmg_staging="$(mktemp -d "${TMPDIR:-/tmp}/chaos-toolbox-dmg.XXXXXX")"
trap 'rm -rf -- "$dmg_staging"' EXIT
cp -R -- "$app_dir" "${dmg_staging}/Chaos Toolbox.app"
ln -s /Applications "${dmg_staging}/Applications"
hdiutil create \
    -volname "Chaos Toolbox ${app_version}" \
    -srcfolder "$dmg_staging" \
    -ov \
    -format UDZO \
    "$dmg_path"
hdiutil verify "$dmg_path"
rm -rf -- "$dmg_staging"
trap - EXIT

if [[ -z "$output_dir" ]]; then
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    if [[ "$(basename -- "$(dirname -- "$protocol_dir")")" == "supplementary" ]]; then
        results_root="${protocol_dir}/../benchmark_results"
    else
        results_root="${protocol_dir}/results"
    fi
    output_dir="${results_root}/macos-16gb/${timestamp}"
fi
[[ ! -e "$output_dir" ]] || die "Benchmark output already exists: $output_dir"

"$venv_python" "$benchmark_script" \
    --toolbox-root "$toolbox_root" \
    --machine-profile "$profile_path" \
    --output-dir "$output_dir" \
    --startup-mode exe \
    --executable "$startup_executable" \
    --installer-artifact "$dmg_path"

for required_json in \
    run_manifest.json \
    startup_raw.json \
    calculations_raw.json \
    summary.json \
    benchmark_result.json
do
    [[ -f "${output_dir}/${required_json}" ]] ||
        die "Required benchmark JSON was not created: ${output_dir}/${required_json}"
done

printf 'macOS app: %s\n' "$app_dir"
printf 'macOS DMG: %s\n' "$dmg_path"
printf 'Benchmark JSON directory: %s\n' "$output_dir"
