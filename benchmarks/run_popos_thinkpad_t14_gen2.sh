#!/usr/bin/env bash
set -euo pipefail

protocol_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
profile_path="${protocol_dir}/popos-thinkpad-t14-gen2.json"
benchmark_script="${protocol_dir}/run_benchmarks.py"
toolbox_root="${TOOLBOX_CHAOS_ROOT:-}"
output_dir=""
check_only=0

export PYTHONUTF8=1
export CHAOS_MP_START_METHOD="${CHAOS_MP_START_METHOD:-forkserver}"
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
        "Builds the native Linux PyInstaller bundle and a local .deb, then runs" \
        "the unchanged benchmark protocol with the Pop!_OS ThinkPad profile."
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

read_dmi_value() {
    local path="$1"
    [[ -r "$path" ]] || die "Cannot read DMI identity from: $path"
    tr -d '\000\r\n' < "$path"
}

assert_target_machine() {
    local vendor product_name product_version identity
    vendor="$(read_dmi_value /sys/class/dmi/id/sys_vendor)"
    product_name="$(read_dmi_value /sys/class/dmi/id/product_name)"
    product_version="$(read_dmi_value /sys/class/dmi/id/product_version)"
    identity="${product_name} ${product_version}"

    [[ "${vendor,,}" == *lenovo* ]] ||
        die "This profile requires a Lenovo ThinkPad T14 Gen 2; DMI vendor is: $vendor"
    [[ "${identity,,}" == *"thinkpad t14 gen 2"* ]] ||
        die "This profile requires a ThinkPad T14 Gen 2; DMI identifies: $identity"

    printf 'DMI identity: %s / %s\n' "$vendor" "$identity"
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

[[ "$(uname -s)" == "Linux" ]] || die "This script must run on Linux."
if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${ID:-}" in
        pop|pop_os)
            ;;
        *)
            die "Expected Pop!_OS; /etc/os-release reports ID=${ID:-unknown}."
            ;;
    esac
fi

if [[ -z "$toolbox_root" ]]; then
    toolbox_root="$(discover_toolbox_root)" ||
        die "Toolbox chaos was not found. Pass --toolbox-root or define TOOLBOX_CHAOS_ROOT."
fi
toolbox_root="$(cd -- "$toolbox_root" && pwd -P)"
is_toolbox_root "$toolbox_root" || die "Not a Toolbox chaos checkout: $toolbox_root"

require_command python3
assert_target_machine
host_arch="$(uname -m)"
python_arch="$(python3 -c 'import platform; print(platform.machine())')"
python_bits="$(python3 -c 'import struct; print(struct.calcsize("P") * 8)')"
[[ "$host_arch" == "x86_64" && "$python_arch" == "x86_64" && "$python_bits" == "64" ]] ||
    die "This Pop!_OS profile requires native x86_64 Python; host=${host_arch}, Python=${python_arch}/${python_bits}-bit."
export CHAOS_MACHINE_IDENTITY_VERIFIED="popos-os-release-and-linux-dmi"

venv_dir="${toolbox_root}/.venv-benchmark-popos"
venv_python="${venv_dir}/bin/python"
check_python="$(command -v python3)"
if [[ -x "$venv_python" ]]; then
    check_python="$venv_python"
fi

if ((check_only)); then
    [[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]] ||
        die "A logged-in graphical session is required for first-paint startup timing."
    "$check_python" -c "import json, numpy, PySide6; json.load(open(r'${profile_path}', encoding='utf-8'))"
    "$check_python" "$benchmark_script" \
        --toolbox-root "$toolbox_root" \
        --machine-profile "$profile_path" \
        --startup-mode source \
        --check-config
    printf 'Check-only completed; no environment, bundle, DEB or result directory was created.\n'
    exit 0
fi

[[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]] ||
    die "Run from the normal logged-in Pop!_OS desktop; no graphical display was detected."

if command -v apt-get >/dev/null 2>&1; then
    apt_prefix=()
    if [[ "$(id -u)" -ne 0 ]]; then
        require_command sudo
        apt_prefix=(sudo)
    fi
    "${apt_prefix[@]}" apt-get update
    "${apt_prefix[@]}" apt-get install -y \
        python3-venv \
        python3-pip \
        build-essential \
        patchelf \
        dpkg-dev \
        fakeroot \
        libglib2.0-0 \
        libgl1 \
        libegl1 \
        libdbus-1-3 \
        libx11-6 \
        libxkbcommon-x11-0 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render-util0 \
        libxcb-xinerama0
fi

require_command cc
require_command dpkg-deb
require_command file
export CHAOS_NATIVE_COMPILER="$(cc --version | sed -n '1p')"
export CHAOS_NATIVE_CFLAGS="-O3 -shared -fPIC -std=c11 -lm"

python3 -m venv "$venv_dir"
"$venv_python" -m pip install --upgrade pip
"$venv_python" -m pip install -r "${toolbox_root}/requirements-build.txt"

native_dir="${toolbox_root}/core/bin"
native_library="${native_dir}/libchaos_core.so"
mkdir -p -- "$native_dir"
cc -O3 -shared -fPIC -std=c11 \
    "${toolbox_root}/core/csrc/chaos_core.c" \
    -o "$native_library" \
    -lm

(
    cd -- "$toolbox_root"
    "$venv_python" -c "from core.native import library; library(); print('Native backend OK')"
    PATH="${venv_dir}/bin:${PATH}" bash scripts/build_linux.sh
)

bundle_dir="${toolbox_root}/dist/Chaos Toolbox"
startup_executable="${bundle_dir}/Chaos Toolbox"
[[ -x "$startup_executable" ]] ||
    die "PyInstaller did not create the expected Linux bundle: $startup_executable"
file "$startup_executable" | grep -q "x86-64" ||
    die "The packaged executable is not x86-64."

runtime_resources="$(
    find "$bundle_dir" -type d -path '*/resources/bundled' -print -quit
)"
if [[ -n "$runtime_resources" ]]; then
    runtime_root="$(dirname -- "$(dirname -- "$runtime_resources")")"
else
    runtime_root="${bundle_dir}/_internal"
fi
mkdir -p -- "${runtime_root}/core/bin"
cp -f -- "$native_library" "${runtime_root}/core/bin/libchaos_core.so"
[[ -f "${runtime_root}/core/bin/libchaos_core.so" ]] ||
    die "The packaged Linux bundle does not contain libchaos_core.so."
file "${runtime_root}/core/bin/libchaos_core.so" | grep -q "x86-64" ||
    die "The packaged native library is not x86-64."

self_test_json="$(mktemp "${TMPDIR:-/tmp}/chaos-toolbox-self-test.XXXXXX")"
trap 'rm -f -- "$self_test_json"' EXIT
"$startup_executable" --self-test-output "$self_test_json"
"$venv_python" -c \
    "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); assert d['status']=='ok' and d['all_finite']" \
    "$self_test_json"
rm -f -- "$self_test_json"
trap - EXIT
export CHAOS_PACKAGED_SELF_TEST="passed"

app_version="$(
    cd -- "$toolbox_root"
    "$venv_python" -c "from core.app_metadata import APP_VERSION; print(APP_VERSION)"
)"
architecture="$(dpkg --print-architecture 2>/dev/null || true)"
if [[ -z "$architecture" ]]; then
    case "$(uname -m)" in
        x86_64) architecture="amd64" ;;
        aarch64|arm64) architecture="arm64" ;;
        *) architecture="$(uname -m)" ;;
    esac
fi

staging_root="${toolbox_root}/build/deb/chaos-toolbox"
case "$staging_root" in
    "${toolbox_root}/build/deb/"*)
        ;;
    *)
        die "Refusing to replace unsafe DEB staging path: $staging_root"
        ;;
esac
rm -rf -- "$staging_root"
mkdir -p -- \
    "${staging_root}/DEBIAN" \
    "${staging_root}/usr/lib/chaos-toolbox" \
    "${staging_root}/usr/bin" \
    "${staging_root}/usr/share/applications" \
    "${staging_root}/usr/share/icons/hicolor/scalable/apps"
cp -a "${bundle_dir}/." "${staging_root}/usr/lib/chaos-toolbox/"
ln -s "/usr/lib/chaos-toolbox/Chaos Toolbox" "${staging_root}/usr/bin/chaos-toolbox"
cp -- "${toolbox_root}/packaging/linux/chaos-toolbox.desktop" \
    "${staging_root}/usr/share/applications/chaos-toolbox.desktop"
sed -i 's|^Exec=.*|Exec=/usr/bin/chaos-toolbox|' \
    "${staging_root}/usr/share/applications/chaos-toolbox.desktop"
cp -- "${toolbox_root}/resources/bundled/icons/chaos-toolbox.svg" \
    "${staging_root}/usr/share/icons/hicolor/scalable/apps/chaos-toolbox.svg"

installed_size="$(du -sk "${staging_root}/usr" | awk '{print $1}')"
control_file="${staging_root}/DEBIAN/control"
{
    printf 'Package: chaos-toolbox\n'
    printf 'Version: %s\n' "$app_version"
    printf 'Section: science\n'
    printf 'Priority: optional\n'
    printf 'Architecture: %s\n' "$architecture"
    printf 'Maintainer: Maria Fernanda Moreno Lopez\n'
    printf 'Installed-Size: %s\n' "$installed_size"
    printf 'Depends: libc6, libglib2.0-0, libgl1, libegl1, libdbus-1-3, libx11-6, libxkbcommon-x11-0, libxcb-cursor0\n'
    printf 'Description: Desktop toolbox for chaotic systems and nonlinear dynamics\n'
    printf ' Reproducible numerical exploration, visualization and diagnostics.\n'
} > "$control_file"
chmod 0755 "${staging_root}/DEBIAN"
chmod 0644 "$control_file"

deb_path="${toolbox_root}/dist/chaos-toolbox_${app_version}_${architecture}.deb"
rm -f -- "$deb_path"
dpkg-deb --build --root-owner-group "$staging_root" "$deb_path"
dpkg-deb --info "$deb_path" >/dev/null

if [[ -z "$output_dir" ]]; then
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    if [[ "$(basename -- "$(dirname -- "$protocol_dir")")" == "supplementary" ]]; then
        results_root="${protocol_dir}/../benchmark_results"
    else
        results_root="${protocol_dir}/results"
    fi
    output_dir="${results_root}/popos-thinkpad-t14-gen2/${timestamp}"
fi
[[ ! -e "$output_dir" ]] || die "Benchmark output already exists: $output_dir"

"$venv_python" "$benchmark_script" \
    --toolbox-root "$toolbox_root" \
    --machine-profile "$profile_path" \
    --output-dir "$output_dir" \
    --startup-mode exe \
    --executable "$startup_executable" \
    --installer-artifact "$deb_path"

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

printf 'Linux bundle: %s\n' "$bundle_dir"
printf 'DEB package: %s\n' "$deb_path"
printf 'Benchmark JSON directory: %s\n' "$output_dir"
