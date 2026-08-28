from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from benchmarks.run_benchmarks import (
    CALCULATION_CASES,
    _array_signature,
    _percentiles,
)
from benchmarks.profile_lyapunov import _source_sha256
from core.performance_metrics import (
    power_status,
    process_memory_snapshot,
    total_physical_memory_bytes,
)


ROOT = Path(__file__).resolve().parents[1]


def test_thinkpad_t14s_gen3_profile_is_machine_readable():
    profile = json.loads(
        (ROOT / "benchmarks" / "windows-thinkpad-t14s-gen3.json").read_text(
            encoding="utf-8"
        )
    )
    assert profile["machine_id"] == "WINDOWS-THINKPAD-T14S-GEN3"
    assert profile["confirmed_family_label"] == "ThinkPad T14s Gen 3"
    assert profile["logical_processors"] == 16
    assert profile["installed_memory_gib"] == 16.0


def test_article_benchmark_cases_are_stable_and_unique():
    assert len(CALCULATION_CASES) == len(set(CALCULATION_CASES))
    assert CALCULATION_CASES == (
        "trajectory_100k",
        "fft_100k",
        "lyapunov_default",
        "bifurcation_default",
        "basin_60",
        "basin_200",
    )


def test_array_signature_records_shape_finiteness_and_digest():
    signature = _array_signature(np.array([1.0, 2.0]), np.eye(2))
    assert signature["shapes"] == [[2], [2, 2]]
    assert signature["total_values"] == 6
    assert signature["all_finite"] is True
    assert len(signature["sha256"]) == 64


def test_inclusive_quartiles_work_for_small_reproducible_samples():
    median, q1, q3 = _percentiles([1.0, 2.0, 3.0, 4.0, 5.0])
    assert median == 3.0
    assert q1 == 2.0
    assert q3 == 4.0


def test_current_process_memory_snapshot_has_nonnegative_values():
    snapshot = process_memory_snapshot()
    assert snapshot.rss_bytes is None or snapshot.rss_bytes > 0
    assert snapshot.peak_rss_bytes is None or snapshot.peak_rss_bytes > 0


def test_system_context_collectors_return_portable_shapes():
    total_memory = total_physical_memory_bytes()
    assert total_memory is None or total_memory > 0
    status = power_status()
    assert set(status) == {"ac_line", "battery_percent"}


def test_lyapunov_profile_baseline_records_protocol_hotspots_and_sources():
    payload = json.loads(
        (ROOT / 'benchmarks' / 'results' / 'lyapunov_profile_current.json').read_text(
            encoding='utf-8'
        )
    )
    assert payload['scope'].endswith('no speedup claim')
    assert payload['protocol']['warmups'] == 1
    assert payload['protocol']['measured_repetitions'] == 5
    assert len(payload['timings_seconds']['raw']) == 5
    assert payload['timings_seconds']['median'] > 0.0
    assert payload['result']['status'] == 'ok'
    assert payload['result']['convergence_shape'][1] == 3
    assert payload['cprofile_hotspots_by_cumulative_time']
    assert payload['source']['commit_status'] == 'clean'
    assert payload['source']['hash_policy'] == (
        'UTF-8 text normalized to LF before SHA-256'
    )
    assert 'core/diagnostics.py' in payload['source']['sha256']
    for relative_path, expected_digest in payload['source']['sha256'].items():
        actual_digest = _source_sha256(ROOT / relative_path)
        assert actual_digest == expected_digest, relative_path
