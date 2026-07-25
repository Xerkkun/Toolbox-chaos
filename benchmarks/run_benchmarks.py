from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Callable

import numpy as np


SCRIPT_PATH = Path(__file__).resolve()
PROTOCOL_DIR = SCRIPT_PATH.parent
SUPPLEMENTARY_DIR = PROTOCOL_DIR.parent
DEFAULT_MACHINE_PROFILE = PROTOCOL_DIR / "windows-thinkpad-t14s-gen3.json"
DEFAULT_RESULTS_ROOT = (
    SUPPLEMENTARY_DIR / "benchmark_results"
    if SUPPLEMENTARY_DIR.name.lower() == "supplementary"
    else PROTOCOL_DIR / "results"
)

CALCULATION_CASES = (
    "trajectory_100k",
    "fft_100k",
    "lyapunov_default",
    "bifurcation_default",
    "basin_60",
    "basin_200",
)

_FFT_INPUT: tuple[np.ndarray, np.ndarray] | None = None


def _find_toolbox_root(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    if os.environ.get("TOOLBOX_CHAOS_ROOT"):
        candidates.append(Path(os.environ["TOOLBOX_CHAOS_ROOT"]))

    for parent in SCRIPT_PATH.parents:
        candidates.extend(
            (
                parent,
                parent / "Toolbox chaos",
                parent / "Toolbox-chaos",
            )
        )

    checked: list[str] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        rendered = str(resolved)
        if rendered in checked:
            continue
        checked.append(rendered)
        if (
            (resolved / "core" / "lorenz.py").is_file()
            and (resolved / "main.py").is_file()
        ):
            return resolved

    raise FileNotFoundError(
        "No se encontró el repositorio Toolbox chaos. Usa --toolbox-root "
        "o define TOOLBOX_CHAOS_ROOT. Rutas revisadas: "
        + ", ".join(checked)
    )


def _configure_toolbox_root(explicit: Path | None) -> Path:
    toolbox_root = _find_toolbox_root(explicit)
    if str(toolbox_root) not in sys.path:
        sys.path.insert(0, str(toolbox_root))
    os.environ["TOOLBOX_CHAOS_ROOT"] = str(toolbox_root)
    return toolbox_root


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_size(path: Path) -> int | None:
    if not path.exists():
        return None
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _portable_artifact_path(path: Path) -> str:
    for parent in (path, *path.parents):
        if parent.suffix.lower() == ".app":
            relative = path.relative_to(parent)
            return (Path(parent.name) / relative).as_posix()
    if path.parent.name == "Chaos Toolbox":
        return (Path(path.parent.name) / path.name).as_posix()
    return path.name


def _portable_command(command: list[str]) -> list[str]:
    rendered: list[str] = []
    for argument in command:
        candidate = Path(argument)
        rendered.append(candidate.name if candidate.is_absolute() else argument)
    return rendered


def _safe_slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return normalized.lower() or "machine"


def _decode_command_output(payload: bytes) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        if platform.system() == "Windows":
            try:
                import ctypes

                encoding = f"cp{ctypes.windll.kernel32.GetOEMCP()}"
            except (AttributeError, OSError):
                encoding = "mbcs"
            return payload.decode(encoding, errors="replace")
        return payload.decode(errors="replace")


def _json_command(command: list[str], timeout_seconds: float = 15.0) -> object | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    stdout = _decode_command_output(completed.stdout).strip()
    if completed.returncode != 0 or not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def _text_command(command: list[str], timeout_seconds: float = 15.0) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    stdout = _decode_command_output(completed.stdout).strip()
    if completed.returncode != 0 or not stdout:
        return None
    return stdout


def _power_mode_inventory() -> dict[str, object]:
    system = platform.system()
    inventory: dict[str, object] = {"collector_system": system}
    if system == "Windows":
        inventory["active_scheme"] = _text_command(
            ["powercfg.exe", "/getactivescheme"]
        )
    elif system == "Darwin":
        inventory["battery_status"] = _text_command(["pmset", "-g", "batt"])
        inventory["power_settings"] = _text_command(["pmset", "-g", "custom"])
    elif system == "Linux":
        inventory["active_profile"] = _text_command(["powerprofilesctl", "get"])
        supplies: dict[str, str] = {}
        power_supply_root = Path("/sys/class/power_supply")
        if power_supply_root.is_dir():
            for supply in power_supply_root.iterdir():
                type_path = supply / "type"
                online_path = supply / "online"
                try:
                    supply_type = type_path.read_text(encoding="utf-8").strip()
                    online = online_path.read_text(encoding="utf-8").strip()
                except OSError:
                    continue
                if supply_type in {"Mains", "USB", "USB_C"}:
                    supplies[supply.name] = online
        inventory["ac_supplies"] = supplies
    return inventory


def _platform_hardware_inventory() -> dict[str, object]:
    """Collect non-identifying hardware details using native read-only tools."""

    system = platform.system()
    inventory: dict[str, object] = {"collector_system": system}
    if system == "Windows":
        script = (
            "$ErrorActionPreference='Stop';"
            "$cs=Get-CimInstance Win32_ComputerSystem;"
            "$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1;"
            "$os=Get-CimInstance Win32_OperatingSystem;"
            "[pscustomobject]@{manufacturer=$cs.Manufacturer;"
            "model=$cs.Model;system_family=$cs.SystemFamily;"
            "processor=$cpu.Name;physical_cores=$cpu.NumberOfCores;"
            "logical_processors=$cpu.NumberOfLogicalProcessors;"
            "memory_bytes=[int64]$cs.TotalPhysicalMemory;"
            "os_caption=$os.Caption;os_version=$os.Version;"
            "os_build=$os.BuildNumber}|ConvertTo-Json -Compress"
        )
        payload = _json_command(
            ["powershell", "-NoProfile", "-Command", script]
        )
        if isinstance(payload, dict):
            inventory["windows_cim"] = payload
        else:
            try:
                import winreg

                def registry_values(
                    key_path: str, value_names: tuple[str, ...]
                ) -> dict[str, object]:
                    values: dict[str, object] = {}
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        key_path,
                        0,
                        winreg.KEY_READ,
                    ) as key:
                        for value_name in value_names:
                            try:
                                values[value_name] = winreg.QueryValueEx(
                                    key, value_name
                                )[0]
                            except FileNotFoundError:
                                pass
                    return values

                inventory["windows_registry_bios"] = registry_values(
                    r"HARDWARE\DESCRIPTION\System\BIOS",
                    (
                        "SystemManufacturer",
                        "SystemProductName",
                        "SystemFamily",
                        "BIOSVersion",
                        "BIOSReleaseDate",
                    ),
                )
                inventory["windows_registry_cpu"] = registry_values(
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                    ("ProcessorNameString", "Identifier"),
                )
                inventory["windows_registry_os"] = registry_values(
                    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                    (
                        "ProductName",
                        "DisplayVersion",
                        "CurrentBuildNumber",
                        "UBR",
                    ),
                )
            except (ImportError, OSError):
                inventory["windows_registry_fallback"] = "unavailable"
    elif system == "Darwin":
        payload = _json_command(
            ["system_profiler", "SPHardwareDataType", "-json"]
        )
        if isinstance(payload, dict):
            entries = payload.get("SPHardwareDataType")
            if isinstance(entries, list) and entries:
                source = entries[0]
                if isinstance(source, dict):
                    allowed = {
                        "_name",
                        "machine_model",
                        "machine_name",
                        "chip_type",
                        "number_processors",
                        "number_cores",
                        "physical_memory",
                    }
                    inventory["macos_system_profiler"] = {
                        key: source[key] for key in allowed if key in source
                    }
    elif system == "Linux":
        os_release_path = Path("/etc/os-release")
        if os_release_path.is_file():
            os_release: dict[str, str] = {}
            for raw_line in os_release_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                if "=" not in raw_line or raw_line.lstrip().startswith("#"):
                    continue
                key, value = raw_line.split("=", 1)
                os_release[key] = value.strip().strip('"')
            inventory["os_release"] = {
                key: os_release[key]
                for key in ("NAME", "VERSION", "ID", "ID_LIKE", "VERSION_ID")
                if key in os_release
            }
        payload = _json_command(["lscpu", "--json"])
        if isinstance(payload, dict):
            fields: dict[str, str] = {}
            for item in payload.get("lscpu", []):
                if not isinstance(item, dict):
                    continue
                field = str(item.get("field", "")).rstrip(":")
                if field in {
                    "Architecture",
                    "CPU(s)",
                    "Model name",
                    "Core(s) per socket",
                    "Socket(s)",
                    "Thread(s) per core",
                }:
                    fields[field] = str(item.get("data", ""))
            inventory["linux_lscpu"] = fields
    return inventory


def _artifact_manifest(path: Path | None, *, bundle_parent: bool = False) -> dict:
    if path is None:
        return {"path": None, "sha256": None, "size_bytes": None}
    resolved = path.expanduser().resolve()
    size = None
    if resolved.is_file():
        if bundle_parent:
            bundle_root = resolved.parent
            for parent in resolved.parents:
                if parent.suffix.lower() == ".app":
                    bundle_root = parent
                    break
            size = _tree_size(bundle_root)
        else:
            size = resolved.stat().st_size
    elif resolved.is_dir():
        size = _tree_size(resolved)
    elif bundle_parent and resolved.parent.exists():
        size = _tree_size(resolved.parent)
    return {
        "path": _portable_artifact_path(resolved),
        "sha256": _sha256_file(resolved),
        "size_bytes": size,
    }


def _dependency_versions() -> dict[str, str | None]:
    distributions = {
        "numpy": "numpy",
        "PyQt6": "PyQt6",
        "matplotlib": "matplotlib",
        "pyqtgraph": "pyqtgraph",
        "PyYAML": "PyYAML",
        "PyInstaller": "pyinstaller",
    }
    versions: dict[str, str | None] = {}
    for label, distribution in distributions.items():
        try:
            versions[label] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            versions[label] = None
    return versions


def _source_fingerprints(toolbox_root: Path) -> dict[str, str | None]:
    relative_paths = (
        "main.py",
        "core/lorenz.py",
        "core/diagnostics.py",
        "core/native.py",
        "core/csrc/chaos_core.c",
        "pyproject.toml",
    )
    return {
        relative_path: _sha256_file(toolbox_root / relative_path)
        for relative_path in relative_paths
    }


def _runtime_manifest(
    machine_profile: Path,
    startup_target: Path | None,
    installer_artifact: Path | None,
    toolbox_root: Path,
) -> dict:
    from core.app_metadata import APP_VERSION
    from core.performance_metrics import power_status, total_physical_memory_bytes

    profile = json.loads(machine_profile.read_text(encoding="utf-8"))
    declared_identity_status = profile.get("identity_status")
    identity_method = os.environ.get("CHAOS_MACHINE_IDENTITY_VERIFIED")
    if identity_method:
        profile["declared_identity_status"] = declared_identity_status
        profile["identity_status"] = "verified_at_runtime"
        profile["identity_verification"] = {
            "status": "verified",
            "method": identity_method,
        }
    else:
        profile["identity_verification"] = {
            "status": "not_verified",
            "method": None,
        }
    profile["software"] = {
        "toolbox_version": APP_VERSION,
        "dependency_versions": _dependency_versions(),
        "source_fingerprints": _source_fingerprints(toolbox_root),
        "source_commit_recorded": False,
    }
    profile["runtime"] = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "python_executable": Path(sys.executable).name,
        "logical_processors_detected": os.cpu_count(),
        "total_physical_memory_bytes": total_physical_memory_bytes(),
        "power_status": power_status(),
        "power_mode_inventory": _power_mode_inventory(),
        "packaged_self_test": os.environ.get("CHAOS_PACKAGED_SELF_TEST"),
        "chaos_workers": 1,
        "native_build": {
            "compiler": os.environ.get("CHAOS_NATIVE_COMPILER"),
            "flags": os.environ.get("CHAOS_NATIVE_CFLAGS"),
        },
        "hardware_inventory": _platform_hardware_inventory(),
    }
    profile["startup_artifact"] = _artifact_manifest(
        startup_target, bundle_parent=True
    )
    profile["installer_artifact"] = _artifact_manifest(installer_artifact)
    return profile


def _array_signature(*arrays: np.ndarray) -> dict[str, object]:
    digest = hashlib.sha256()
    shapes = []
    finite = True
    total_values = 0
    checksum = 0.0
    for value in arrays:
        array = np.ascontiguousarray(np.asarray(value))
        digest.update(array.tobytes())
        shapes.append(list(array.shape))
        total_values += int(array.size)
        if np.issubdtype(array.dtype, np.number):
            finite = finite and bool(np.all(np.isfinite(array)))
            checksum += float(np.sum(array, dtype=np.float64))
    return {
        "shapes": shapes,
        "total_values": total_values,
        "all_finite": finite,
        "numeric_checksum": checksum,
        "sha256": digest.hexdigest(),
    }


def _case_trajectory_100k() -> dict:
    from core.lorenz import simulate_system

    t, states = simulate_system(
        "lorenz", [1.0, 1.0, 1.0], [10.0, 28.0, 8.0 / 3.0], 0.01, 1000.0, "rk4"
    )
    return _array_signature(t, states)


def _case_fft_100k() -> dict:
    global _FFT_INPUT

    from core.diagnostics import normalized_fft
    from core.lorenz import simulate_system

    if _FFT_INPUT is None:
        _FFT_INPUT = simulate_system(
            "lorenz",
            [1.0, 1.0, 1.0],
            [10.0, 28.0, 8.0 / 3.0],
            0.01,
            1000.0,
            "rk4",
        )
    t, states = _FFT_INPUT
    frequencies, spectrum = normalized_fft(t, states)
    return _array_signature(frequencies, spectrum)


def _case_lyapunov_default() -> dict:
    from core.diagnostics import integer_qr_benettin_lyapunov

    result = integer_qr_benettin_lyapunov(
        "lorenz",
        [1.0, 1.0, 1.0],
        [10.0, 28.0, 8.0 / 3.0],
        0.01,
        40.0,
        t_burn=5.0,
        reorthonormalize_every=10,
    )
    signature = _array_signature(
        result.exponents, result.times, result.convergence
    )
    signature["diagnostic_status"] = result.status
    return signature


def _case_bifurcation_default() -> dict:
    from core.lorenz import bifurcation_poincare_lorenz

    parameter, events = bifurcation_poincare_lorenz(
        1.0,
        1.0,
        1.0,
        10.0,
        8.0 / 3.0,
        0.0,
        80.0,
        350,
        0.01,
        80.0,
        120.0,
        250,
        False,
        "rk4",
    )
    return _array_signature(parameter, events)


def _basin(size: int) -> dict:
    from core.lorenz import compute_basin_plane_z_lorenz_xiong

    result = compute_basin_plane_z_lorenz_xiong(
        10.0,
        28.0,
        8.0 / 3.0,
        1.0,
        -60.0,
        60.0,
        -60.0,
        60.0,
        size,
        size,
        0.02,
        18.0,
        2.0,
        1.0e3,
        "rk4",
    )
    return _array_signature(result)


def _case_basin_60() -> dict:
    return _basin(60)


def _case_basin_200() -> dict:
    return _basin(200)


CASE_FUNCTIONS: dict[str, Callable[[], dict]] = {
    "trajectory_100k": _case_trajectory_100k,
    "fft_100k": _case_fft_100k,
    "lyapunov_default": _case_lyapunov_default,
    "bifurcation_default": _case_bifurcation_default,
    "basin_60": _case_basin_60,
    "basin_200": _case_basin_200,
}


def _run_calculation_worker(case_name: str, output_path: Path) -> int:
    from core.performance_metrics import process_memory_snapshot

    os.environ["CHAOS_WORKERS"] = "1"
    function = CASE_FUNCTIONS[case_name]
    function()  # one untimed warm-up under the same numerical contract
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    result_signature = function()
    wall_end = time.perf_counter_ns()
    cpu_end = time.process_time_ns()
    memory = process_memory_snapshot()
    payload = {
        "schema_version": 1,
        "status": "ok",
        "case": case_name,
        "wall_seconds": (wall_end - wall_start) / 1_000_000_000,
        "cpu_seconds": (cpu_end - cpu_start) / 1_000_000_000,
        "peak_rss_bytes": memory.peak_rss_bytes,
        "rss_after_bytes": memory.rss_bytes,
        "result": result_signature,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def _startup_command(
    mode: str,
    executable: Path | None,
    toolbox_root: Path,
) -> tuple[list[str], Path | None]:
    if mode in {"auto", "exe"}:
        candidates = (
            [executable]
            if executable
            else [
                toolbox_root / "dist" / "Chaos Toolbox" / "Chaos Toolbox.exe",
                toolbox_root
                / "dist"
                / "Chaos Toolbox.app"
                / "Contents"
                / "MacOS"
                / "Chaos Toolbox",
                toolbox_root / "dist" / "Chaos Toolbox" / "Chaos Toolbox",
            ]
        )
        for candidate in candidates:
            if candidate and candidate.is_file():
                return [str(candidate)], candidate
        if mode == "exe":
            rendered = ", ".join(str(item) for item in candidates if item)
            raise FileNotFoundError(
                f"Packaged executable not found. Checked: {rendered}"
            )
    return [sys.executable, str(toolbox_root / "main.py")], None


def _terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def _run_startup_trials(
    command: list[str],
    output_dir: Path,
    runs: int,
    timeout_seconds: float,
    toolbox_root: Path,
) -> list[dict]:
    records = []
    work_dir = output_dir / ".work"
    work_dir.mkdir(parents=True, exist_ok=True)
    for sequence in range(0, runs + 1):
        is_warmup = sequence == 0
        ready_label = "warmup" if is_warmup else f"{sequence:02d}"
        ready_path = work_dir / f"startup_ready_{ready_label}.json"
        if ready_path.exists():
            ready_path.unlink()
        start_ns = time.perf_counter_ns()
        environment = os.environ.copy()
        environment.update(
            {
                "CHAOS_BENCHMARK_READY_FILE": str(ready_path),
                "CHAOS_BENCHMARK_START_NS": str(start_ns),
                "CHAOS_BENCHMARK_EXIT_AFTER_READY": "1",
                "CHAOS_WORKERS": "1",
            }
        )
        process = subprocess.Popen(command, cwd=toolbox_root, env=environment)
        deadline = time.monotonic() + timeout_seconds
        payload = None
        while time.monotonic() < deadline:
            if ready_path.is_file():
                try:
                    payload = json.loads(ready_path.read_text(encoding="utf-8"))
                    break
                except (OSError, json.JSONDecodeError):
                    pass
            if process.poll() is not None and not ready_path.exists():
                break
            time.sleep(0.01)
        _terminate_process(process)
        if payload is None:
            payload = {
                "schema_version": 1,
                "status": "timeout" if time.monotonic() >= deadline else "failed",
                "startup_seconds": None,
                "memory_at_ready": {},
            }
        payload.update(
            {
                "repetition": sequence,
                "command": _portable_command(command),
                "process_returncode": process.returncode,
            }
        )
        if is_warmup:
            if payload.get("status") != "ready":
                shutil.rmtree(work_dir, ignore_errors=True)
                raise RuntimeError(
                    "The unmeasured startup warm-up did not reach first paint."
                )
            continue
        records.append(payload)
    shutil.rmtree(work_dir, ignore_errors=True)
    return records


def _run_calculation_trials(
    output_dir: Path,
    cases: list[str],
    runs: int,
    timeout_seconds: float,
    toolbox_root: Path,
) -> list[dict]:
    records = []
    work_dir = output_dir / ".work"
    work_dir.mkdir(parents=True, exist_ok=True)
    for case_name in cases:
        for repetition in range(1, runs + 1):
            result_path = work_dir / f"{case_name}_{repetition:02d}.json"
            if result_path.exists():
                result_path.unlink()
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "--worker",
                case_name,
                "--worker-output",
                str(result_path),
            ]
            environment = os.environ.copy()
            environment["CHAOS_WORKERS"] = "1"
            try:
                completed = subprocess.run(
                    command,
                    cwd=toolbox_root,
                    env=environment,
                    timeout=timeout_seconds,
                    check=False,
                )
                if result_path.is_file():
                    payload = json.loads(result_path.read_text(encoding="utf-8"))
                else:
                    payload = {
                        "schema_version": 1,
                        "status": "failed",
                        "case": case_name,
                        "wall_seconds": None,
                        "cpu_seconds": None,
                        "peak_rss_bytes": None,
                        "rss_after_bytes": None,
                        "error": f"worker return code {completed.returncode}",
                    }
            except subprocess.TimeoutExpired:
                payload = {
                    "schema_version": 1,
                    "status": "timeout",
                    "case": case_name,
                    "wall_seconds": None,
                    "cpu_seconds": None,
                    "peak_rss_bytes": None,
                    "rss_after_bytes": None,
                    "error": f"timeout after {timeout_seconds} seconds",
                }
            payload["repetition"] = repetition
            records.append(payload)
    shutil.rmtree(work_dir, ignore_errors=True)
    return records


def _write_csv(path: Path, records: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def _percentiles(values: list[float]) -> tuple[float, float, float]:
    median = statistics.median(values)
    if len(values) == 1:
        return median, values[0], values[0]
    quartiles = statistics.quantiles(values, n=4, method="inclusive")
    return median, quartiles[0], quartiles[2]


def _summarize_startup(records: list[dict]) -> list[dict]:
    ok = [item for item in records if item.get("status") == "ready"]
    values = [float(item["startup_seconds"]) for item in ok]
    if not values:
        return []
    median, q1, q3 = _percentiles(values)
    rss_values = [
        int(item.get("memory_at_ready", {}).get("rss_bytes"))
        for item in ok
        if item.get("memory_at_ready", {}).get("rss_bytes") is not None
    ]
    peak_values = [
        int(item.get("memory_at_ready", {}).get("peak_rss_bytes"))
        for item in ok
        if item.get("memory_at_ready", {}).get("peak_rss_bytes") is not None
    ]
    return [
        {
            "case": "startup_to_first_paint",
            "successful_runs": len(values),
            "median_wall_seconds": median,
            "q1_wall_seconds": q1,
            "q3_wall_seconds": q3,
            "min_wall_seconds": min(values),
            "max_wall_seconds": max(values),
            "median_cpu_seconds": None,
            "median_cpu_utilization_percent": None,
            "median_rss_mib": (
                statistics.median(rss_values) / (1024 * 1024)
                if rss_values
                else None
            ),
            "median_peak_rss_mib": (
                statistics.median(peak_values) / (1024 * 1024)
                if peak_values
                else None
            ),
        }
    ]


def _summarize_calculations(records: list[dict]) -> list[dict]:
    summary = []
    for case_name in CALCULATION_CASES:
        matching = [
            item
            for item in records
            if item.get("case") == case_name and item.get("status") == "ok"
        ]
        values = [float(item["wall_seconds"]) for item in matching]
        if not values:
            continue
        median, q1, q3 = _percentiles(values)
        peak_values = [
            int(item["peak_rss_bytes"])
            for item in matching
            if item.get("peak_rss_bytes") is not None
        ]
        rss_values = [
            int(item["rss_after_bytes"])
            for item in matching
            if item.get("rss_after_bytes") is not None
        ]
        cpu_values = [
            float(item["cpu_seconds"])
            for item in matching
            if item.get("cpu_seconds") is not None
        ]
        utilization_values = [
            100.0 * float(item["cpu_seconds"]) / float(item["wall_seconds"])
            for item in matching
            if item.get("cpu_seconds") is not None
            and item.get("wall_seconds") not in {None, 0}
        ]
        summary.append(
            {
                "case": case_name,
                "successful_runs": len(values),
                "median_wall_seconds": median,
                "q1_wall_seconds": q1,
                "q3_wall_seconds": q3,
                "min_wall_seconds": min(values),
                "max_wall_seconds": max(values),
                "median_cpu_seconds": (
                    statistics.median(cpu_values) if cpu_values else None
                ),
                "median_cpu_utilization_percent": (
                    statistics.median(utilization_values)
                    if utilization_values
                    else None
                ),
                "median_rss_mib": (
                    statistics.median(rss_values) / (1024 * 1024)
                    if rss_values
                    else None
                ),
                "median_peak_rss_mib": (
                    statistics.median(peak_values) / (1024 * 1024)
                    if peak_values
                    else None
                ),
            }
        )
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproducible startup and numerical benchmarks for Toolbox Chaos."
    )
    parser.add_argument(
        "--toolbox-root",
        type=Path,
        help=(
            "Ruta al repositorio Toolbox chaos. Si se omite, se usa "
            "TOOLBOX_CHAOS_ROOT o se buscan directorios hermanos."
        ),
    )
    parser.add_argument("--machine-profile", type=Path, default=DEFAULT_MACHINE_PROFILE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--startup-mode", choices=("auto", "exe", "source"), default="auto")
    parser.add_argument("--executable", type=Path)
    parser.add_argument(
        "--installer-artifact",
        type=Path,
        help="Instalador o paquete (.exe, .dmg, .deb) cuyo hash se registrará.",
    )
    parser.add_argument("--startup-runs", type=int, default=10)
    parser.add_argument("--calculation-runs", type=int, default=5)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--calculation-timeout", type=float, default=300.0)
    parser.add_argument("--skip-startup", action="store_true")
    parser.add_argument("--skip-calculations", action="store_true")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Valida rutas e importaciones sin ejecutar ni escribir resultados.",
    )
    parser.add_argument("--case", action="append", choices=CALCULATION_CASES)
    parser.add_argument("--worker", choices=CALCULATION_CASES, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    toolbox_root = _configure_toolbox_root(args.toolbox_root)
    machine_profile = args.machine_profile.expanduser().resolve()
    if args.worker:
        if args.worker_output is None:
            raise SystemExit("--worker-output is required with --worker")
        return _run_calculation_worker(args.worker, args.worker_output)

    profile_data = json.loads(machine_profile.read_text(encoding="utf-8"))
    if not isinstance(profile_data, dict):
        raise SystemExit("Machine profile must contain a JSON object.")
    expected_system = profile_data.get("expected_system")
    detected_system = platform.system()
    if (
        not args.check_config
        and expected_system
        and str(expected_system) != detected_system
    ):
        raise SystemExit(
            "The selected machine profile expects "
            f"{expected_system}, but this computer reports {detected_system}."
        )
    installer_artifact = (
        args.installer_artifact.expanduser().resolve()
        if args.installer_artifact
        else None
    )

    if args.check_config:
        from core.lorenz import SYSTEM_REGISTRY
        from core.performance_metrics import total_physical_memory_bytes

        command, startup_target = _startup_command(
            args.startup_mode,
            args.executable,
            toolbox_root,
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "toolbox_root": str(toolbox_root),
                    "machine_profile": str(machine_profile),
                    "startup_command": command,
                    "startup_artifact": (
                        str(startup_target) if startup_target else None
                    ),
                    "installer_artifact": (
                        str(installer_artifact) if installer_artifact else None
                    ),
                    "machine_id": profile_data.get("machine_id"),
                    "expected_system": profile_data.get("expected_system"),
                    "detected_system": platform.system(),
                    "system_match": (
                        not profile_data.get("expected_system")
                        or profile_data.get("expected_system") == platform.system()
                    ),
                    "registered_systems": len(SYSTEM_REGISTRY),
                    "physical_memory_detected": (
                        total_physical_memory_bytes() is not None
                    ),
                    "default_output_parent": str(
                        DEFAULT_RESULTS_ROOT
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.startup_runs < 1 or args.calculation_runs < 1:
        raise SystemExit("Run counts must be positive.")
    if args.skip_startup and args.skip_calculations:
        raise SystemExit(
            "At least one phase must run; do not combine "
            "--skip-startup and --skip-calculations."
        )
    os.environ["CHAOS_WORKERS"] = "1"
    for variable in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[variable] = "1"
    os.environ.setdefault(
        "CHAOS_MP_START_METHOD",
        "spawn" if platform.system() in {"Windows", "Darwin"} else "forkserver",
    )
    command, startup_target = _startup_command(
        args.startup_mode,
        args.executable,
        toolbox_root,
    )
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else DEFAULT_RESULTS_ROOT
        / _safe_slug(str(profile_data.get("machine_id", platform.system())))
        / _utc_timestamp()
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    manifest = _runtime_manifest(
        machine_profile,
        startup_target,
        installer_artifact,
        toolbox_root,
    )
    selected_cases = args.case or list(CALCULATION_CASES)
    manifest["protocol"] = {
        "schema_version": 1,
        "benchmark_script_sha256": _sha256_file(SCRIPT_PATH),
        "startup_definition": "process launch to first main-window paint event",
        "startup_execution": (
            "packaged_native_artifact" if startup_target else "source_python"
        ),
        "calculation_execution": "source_python_worker_same_checkout",
        "startup_enabled": not args.skip_startup,
        "calculations_enabled": not args.skip_calculations,
        "startup_warmups": 1,
        "startup_runs": args.startup_runs,
        "calculation_runs": args.calculation_runs,
        "calculation_warmups_per_worker": 1,
        "startup_timeout_seconds": args.startup_timeout,
        "calculation_timeout_seconds": args.calculation_timeout,
        "workers": 1,
        "thread_environment": {
            name: os.environ.get(name)
            for name in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
            )
        },
        "cases": selected_cases,
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    startup_records = []
    if not args.skip_startup:
        startup_records = _run_startup_trials(
            command,
            output_dir,
            args.startup_runs,
            args.startup_timeout,
            toolbox_root,
        )
        (output_dir / "startup_raw.json").write_text(
            json.dumps(startup_records, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        startup_flat = []
        for item in startup_records:
            memory = item.get("memory_at_ready", {})
            startup_flat.append(
                {
                    "repetition": item.get("repetition"),
                    "status": item.get("status"),
                    "startup_seconds": item.get("startup_seconds"),
                    "rss_at_ready_bytes": memory.get("rss_bytes"),
                    "peak_rss_at_ready_bytes": memory.get("peak_rss_bytes"),
                    "pid": item.get("pid"),
                }
            )
        _write_csv(
            output_dir / "startup_raw.csv",
            startup_flat,
            [
                "repetition",
                "status",
                "startup_seconds",
                "rss_at_ready_bytes",
                "peak_rss_at_ready_bytes",
                "pid",
            ],
        )

    calculation_records = []
    if not args.skip_calculations:
        calculation_records = _run_calculation_trials(
            output_dir,
            selected_cases,
            args.calculation_runs,
            args.calculation_timeout,
            toolbox_root,
        )
        (output_dir / "calculations_raw.json").write_text(
            json.dumps(calculation_records, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_csv(
            output_dir / "calculations_raw.csv",
            calculation_records,
            [
                "case",
                "repetition",
                "status",
                "wall_seconds",
                "cpu_seconds",
                "peak_rss_bytes",
                "rss_after_bytes",
                "error",
            ],
        )

    summary = _summarize_startup(startup_records) + _summarize_calculations(
        calculation_records
    )
    _write_csv(
        output_dir / "summary.csv",
        summary,
        [
            "case",
            "successful_runs",
            "median_wall_seconds",
            "q1_wall_seconds",
            "q3_wall_seconds",
            "min_wall_seconds",
            "max_wall_seconds",
            "median_cpu_seconds",
            "median_cpu_utilization_percent",
            "median_rss_mib",
            "median_peak_rss_mib",
        ],
    )
    startup_ok = args.skip_startup or (
        len(startup_records) == args.startup_runs
        and all(item.get("status") == "ready" for item in startup_records)
    )
    expected_calculation_records = len(selected_cases) * args.calculation_runs
    calculations_ok = args.skip_calculations or (
        len(calculation_records) == expected_calculation_records
        and all(item.get("status") == "ok" for item in calculation_records)
    )
    run_ok = startup_ok and calculations_ok
    summary_payload = {
        "schema_version": 1,
        "status": "ok" if run_ok else "partial",
        "machine_id": profile_data.get("machine_id"),
        "captured_at_utc": manifest["runtime"]["captured_at_utc"],
        "results": summary,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    consolidated_payload = {
        "schema_version": 1,
        "status": "ok" if run_ok else "partial",
        "manifest": manifest,
        "startup_records": startup_records,
        "calculation_records": calculation_records,
        "summary": summary,
    }
    consolidated_path = output_dir / "benchmark_result.json"
    consolidated_path.write_text(
        json.dumps(
            consolidated_payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "ok" if run_ok else "partial",
                "output_dir": str(output_dir),
                "result_json": str(consolidated_path),
            },
            ensure_ascii=False,
        )
    )
    return 0 if run_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
