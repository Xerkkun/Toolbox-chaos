"""Reproducible baseline and cProfile snapshot for the integer QR diagnostic."""
from __future__ import annotations

import argparse
import cProfile
from datetime import datetime, timezone
import hashlib
import json
import os

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
os.environ.setdefault('NUMEXPR_NUM_THREADS', '1')

from pathlib import Path
import platform
import pstats
import statistics
import subprocess
import sys
from time import perf_counter

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'benchmarks' / 'results' / 'lyapunov_profile_current.json'
CONFIG = {
    'system_key': 'lorenz',
    'initial': [1.0, 1.0, 1.0],
    'parameters': [10.0, 28.0, 8.0 / 3.0],
    'step_size': 0.01,
    'measurement_time': 40.0,
    'burn_time': 5.0,
    'reorthonormalize_every': 10,
}
WARMUPS = 1
REPETITIONS = 5


def _source_sha256(path: Path) -> str:
    """Hash UTF-8 source text independently of checkout line endings."""

    source = path.read_text(encoding='utf-8')
    canonical = source.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def _git_value(*arguments: str) -> str | None:
    try:
        completed = subprocess.run(
            ['git', *arguments], cwd=ROOT, check=False,
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def _run_diagnostic():
    from core.diagnostics import integer_qr_benettin_lyapunov

    return integer_qr_benettin_lyapunov(
        CONFIG['system_key'], CONFIG['initial'], CONFIG['parameters'],
        CONFIG['step_size'], CONFIG['measurement_time'],
        t_burn=CONFIG['burn_time'],
        reorthonormalize_every=CONFIG['reorthonormalize_every'],
    )


def _portable_function_name(filename: str, line_number: int, function_name: str) -> str:
    path = Path(filename)
    if 'site-packages' in path.parts:
        index = path.parts.index('site-packages')
        label = Path(*path.parts[index + 1:]).as_posix()
    else:
        try:
            label = path.resolve().relative_to(ROOT).as_posix()
        except (OSError, ValueError):
            label = path.name
    return f'{label}:{line_number}:{function_name}'


def _profile_hotspots(limit: int = 15) -> tuple[list[dict], object]:
    profiler = cProfile.Profile()
    result = profiler.runcall(_run_diagnostic)
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line_number, function_name), values in stats.stats.items():
        primitive_calls, total_calls, own_seconds, cumulative_seconds, _callers = values
        rows.append({
            'function': _portable_function_name(filename, line_number, function_name),
            'primitive_calls': primitive_calls,
            'total_calls': total_calls,
            'own_seconds': own_seconds,
            'cumulative_seconds': cumulative_seconds,
        })
    rows.sort(key=lambda row: row['cumulative_seconds'], reverse=True)
    return rows[:limit], result


def build_payload() -> dict:
    for _ in range(WARMUPS):
        warmup_result = _run_diagnostic()
        if warmup_result.status != 'ok':
            raise RuntimeError(f'Lyapunov warm-up failed: {warmup_result.status}')

    durations = []
    measured_result = None
    for _ in range(REPETITIONS):
        started = perf_counter()
        measured_result = _run_diagnostic()
        durations.append(perf_counter() - started)
        if measured_result.status != 'ok':
            raise RuntimeError(f'Lyapunov measurement failed: {measured_result.status}')

    hotspots, profiled_result = _profile_hotspots()
    if profiled_result.status != 'ok' or measured_result is None:
        raise RuntimeError('The profiled Lyapunov calculation did not complete.')

    source_paths = [
        ROOT / 'core' / 'diagnostics.py',
        ROOT / 'core' / 'lorenz.py',
        ROOT / 'benchmarks' / 'profile_lyapunov.py',
    ]
    commit = _git_value('rev-parse', 'HEAD')
    porcelain = _git_value('status', '--porcelain=v1', '--untracked-files=no')
    convergence_bytes = np.asarray(measured_result.convergence, dtype='<f8').tobytes()
    return {
        'schema_version': 1,
        'scope': 'integer_qr_benettin_lyapunov baseline; no speedup claim',
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'configuration': CONFIG,
        'protocol': {
            'warmups': WARMUPS,
            'measured_repetitions': REPETITIONS,
            'profiled_repetitions': 1,
            'timer': 'time.perf_counter',
            'workers': 1,
            'thread_environment': {
                name: os.environ.get(name)
                for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
            },
        },
        'runtime': {
            'python': platform.python_version(),
            'implementation': platform.python_implementation(),
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'numpy': np.__version__,
        },
        'source': {
            'commit': commit,
            'commit_status': 'dirty' if porcelain else ('clean' if commit else 'unavailable'),
            'hash_policy': 'UTF-8 text normalized to LF before SHA-256',
            'sha256': {
                path.relative_to(ROOT).as_posix(): _source_sha256(path)
                for path in source_paths
            },
        },
        'timings_seconds': {
            'raw': durations,
            'median': statistics.median(durations),
            'minimum': min(durations),
            'maximum': max(durations),
        },
        'result': {
            'status': measured_result.status,
            'exponents': measured_result.exponents.tolist(),
            'convergence_shape': list(measured_result.convergence.shape),
            'convergence_sha256_float64_le': hashlib.sha256(convergence_bytes).hexdigest(),
        },
        'cprofile_hotspots_by_cumulative_time': hotspots,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_payload(), indent=2) + '\n', encoding='utf-8')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
