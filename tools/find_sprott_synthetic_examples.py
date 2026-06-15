from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.sprott import decode_code
from core.sprott.search import classify_candidate, generate_random_code, quick_lyapunov_estimate, simulate_candidate
from core.sprott.visual import SprottVisualConfig, trajectory_stats, visual_preset


def default_output_dir() -> Path:
    return REPO_ROOT / 'external' / 'sprott_candidate_examples'


def recommended_visual_for_code(code: str) -> dict:
    decoded = decode_code(code)
    if decoded.kind == 'flow':
        config = visual_preset('Color por profundidad')
        config.projection = '3D x-y-z' if decoded.dimension >= 3 else 'x-y'
        config.color_by = 'z'
        config.max_points = 26000
        return config.to_dict()
    if decoded.dimension >= 4:
        return visual_preset('Mapa 4D').to_dict()
    if decoded.dimension == 3:
        return visual_preset('Color por profundidad').to_dict()
    if decoded.dimension == 2:
        return visual_preset('Alta densidad').to_dict()
    config = visual_preset('Didactico')
    config.projection = 'n-x'
    return config.to_dict()


def _lyapunov_value(code: str) -> float | None:
    try:
        estimate = quick_lyapunov_estimate(code, steps=700)
    except Exception:
        return None
    value = getattr(estimate, 'value', None)
    try:
        if value is None or not np.isfinite(float(value)):
            return None
        return float(value)
    except Exception:
        return None


def candidate_record(
    code: str,
    *,
    seed: int | None = None,
    iterations: int = 3600,
    transient: int = 500,
    h: float = 0.01,
    method: str = 'rk4',
    divergence_threshold: float = 1e9,
) -> dict:
    decoded = decode_code(code)
    result = simulate_candidate(
        code,
        n_iter=iterations,
        transient=transient,
        h=h,
        method=method,
        divergence_threshold=divergence_threshold,
        backend='c',
    )
    classification = classify_candidate(result['post_transient'], divergence_threshold=divergence_threshold)
    stats = trajectory_stats(result['post_transient'])
    digest = hashlib.sha1(code.encode('utf-8')).hexdigest()[:8]
    example_id = f"candidate_{decoded.family_letter.lower()}_{digest}"
    return {
        'id': example_id,
        'name': f'Generated {decoded.dimension}D {decoded.kind} candidate',
        'source': 'generated candidate review',
        'category': f"{decoded.dimension}D {decoded.kind}",
        'code': code,
        'family': decoded.family_letter,
        'kind': decoded.kind,
        'dimension': decoded.dimension,
        'order': decoded.order,
        'seed': seed,
        'expected_status': classification.get('state', ''),
        'classification': classification,
        'stats': stats,
        'quick_lyapunov': _lyapunov_value(code),
        'learning_goal': 'Review this generated candidate and decide whether it deserves a curated visual lesson.',
        'visual_intent': 'Initial recommendation generated from kind and dimension; edit before promotion.',
        'parameters': {
            'kind': decoded.kind,
            'dimension': decoded.dimension,
            'order': decoded.order,
            'iterations': iterations,
            'transient': transient,
            'h': h,
            'method': method,
            'divergence_threshold': divergence_threshold,
        },
        'visual': recommended_visual_for_code(code),
    }


def candidate_passes(record: dict, *, min_finite: int = 512, min_spread: float = 0.02) -> bool:
    state = record.get('classification', {}).get('state') or record.get('expected_status')
    if state != 'candidate_chaotic':
        return False
    stats = record.get('stats', {})
    if int(stats.get('finite_count', 0)) < min_finite:
        return False
    ranges = stats.get('ranges', [])
    if not ranges:
        return False
    widest = max(float(hi) - float(lo) for lo, hi in ranges)
    return widest >= min_spread


def render_candidate_thumbnail(record: dict, output_dir: str | Path) -> Path:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt6.QtWidgets import QApplication
    from ui.sprott_canvases import Sprott2DCanvas

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    params = record.get('parameters', {})
    result = simulate_candidate(
        record['code'],
        n_iter=int(params.get('iterations', 3600)),
        transient=int(params.get('transient', 500)),
        h=float(params.get('h', 0.01)),
        method=str(params.get('method', 'rk4')),
        divergence_threshold=float(params.get('divergence_threshold', 1e9)),
        backend='c',
    )
    app = QApplication.instance() or QApplication([])
    canvas = Sprott2DCanvas()
    canvas.plot_trajectory(
        result['post_transient'],
        SprottVisualConfig.from_dict(record.get('visual', {})),
        title=record.get('name', record['code']),
    )
    path = output / f"{record['id']}.png"
    canvas.export_thumbnail(path)
    canvas.deleteLater()
    app.processEvents()
    return path


def find_candidates(
    *,
    kind: str = 'map',
    dimension: int = 3,
    order: int = 2,
    attempts: int = 80,
    seed: int = 1,
    count: int = 8,
    iterations: int = 3600,
    transient: int = 500,
    h: float = 0.01,
    method: str = 'rk4',
    divergence_threshold: float = 1e9,
) -> list[dict]:
    rng = np.random.default_rng(seed)
    records: list[dict] = []
    for attempt in range(1, int(attempts) + 1):
        code = generate_random_code(kind=kind, dimension=dimension, order=order, rng=rng)
        record = candidate_record(
            code,
            seed=seed,
            iterations=iterations,
            transient=transient,
            h=h,
            method=method,
            divergence_threshold=divergence_threshold,
        )
        record['attempt'] = attempt
        if candidate_passes(record):
            records.append(record)
        if len(records) >= int(count):
            break
    return records


def write_candidate_package(records: list[dict], output_dir: str | Path, *, render_thumbnails: bool = True) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if render_thumbnails:
        thumb_dir = output / 'thumbnails'
        for record in records:
            path = render_candidate_thumbnail(record, thumb_dir)
            record['thumbnail'] = str(path.relative_to(output)).replace('\\', '/')
    data = {
        'schema': 1,
        'description': 'Generated Sprott-style synthetic candidates for review. Not public curated assets until promoted.',
        'candidates': records,
    }
    target = output / 'candidates.json'
    with target.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Find generated Sprott-style synthetic examples for review.')
    parser.add_argument('--kind', default='map', choices=['map', 'flow'])
    parser.add_argument('--dimension', type=int, default=3)
    parser.add_argument('--order', type=int, default=2)
    parser.add_argument('--attempts', type=int, default=80)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--count', type=int, default=8)
    parser.add_argument('--iterations', type=int, default=3600)
    parser.add_argument('--transient', type=int, default=500)
    parser.add_argument('--h', type=float, default=0.01)
    parser.add_argument('--method', default='rk4', choices=['rk4', 'euler'])
    parser.add_argument('--divergence-threshold', type=float, default=1e9)
    parser.add_argument('--output-dir', default=str(default_output_dir()))
    parser.add_argument('--no-thumbnails', action='store_true')
    args = parser.parse_args(argv)
    records = find_candidates(
        kind=args.kind,
        dimension=args.dimension,
        order=args.order,
        attempts=args.attempts,
        seed=args.seed,
        count=args.count,
        iterations=args.iterations,
        transient=args.transient,
        h=args.h,
        method=args.method,
        divergence_threshold=args.divergence_threshold,
    )
    target = write_candidate_package(records, args.output_dir, render_thumbnails=not args.no_thumbnails)
    print(target)
    print(f'accepted={len(records)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
