from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.sprott.catalog import examples_path
from tools.generate_sprott_example_thumbnails import thumbnail_relative_path


SYNTHETIC_SOURCE = 'synthetic educational example'


def _load_document(path: str | Path) -> dict:
    target = Path(path)
    with target.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {'schema': 2, 'examples': data}
    return data


def _write_document(path: str | Path, data: dict) -> None:
    target = Path(path)
    with target.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def load_candidates(path: str | Path) -> list[dict]:
    with Path(path).open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    return data.get('candidates', data if isinstance(data, list) else [])


def promote_candidate_record(record: dict, *, example_id: str | None = None) -> dict:
    required = ['code', 'parameters', 'visual', 'learning_goal', 'visual_intent']
    missing = [key for key in required if key not in record or record.get(key) in ({}, '', None)]
    if missing:
        raise ValueError(f"Candidate {record.get('id', record.get('code', '<unknown>'))} is missing: {', '.join(missing)}")
    promoted_id = example_id or str(record.get('id') or f"synthetic_{record['code'].lower()}")
    if not promoted_id.startswith('synthetic_'):
        promoted_id = f'synthetic_{promoted_id}'
    return {
        'id': promoted_id,
        'name': record.get('name', promoted_id.replace('_', ' ').title()),
        'source': SYNTHETIC_SOURCE,
        'category': record.get('category', 'Generated candidate'),
        'code': record['code'],
        'equations': record.get('equations', 'Generated polynomial code; use Codigos > Decodificar to inspect all coefficients.'),
        'notes': record.get('notes', 'Promoted from external generated-candidate review.'),
        'learning_goal': record['learning_goal'],
        'visual_intent': record['visual_intent'],
        'expected_status': record.get('expected_status') or record.get('classification', {}).get('state', ''),
        'thumbnail': thumbnail_relative_path(promoted_id),
        'parameters': record['parameters'],
        'visual': record['visual'],
    }


def upsert_examples(document: dict, promoted: list[dict]) -> dict:
    document.setdefault('schema', 2)
    examples = list(document.get('examples', []))
    positions = {item.get('id'): idx for idx, item in enumerate(examples)}
    for item in promoted:
        if item['id'] in positions:
            examples[positions[item['id']]] = item
        else:
            examples.append(item)
    document['examples'] = examples
    return document


def promote_candidates(
    *,
    candidates_file: str | Path,
    ids: list[str],
    examples_file: str | Path | None = None,
    dry_run: bool = False,
) -> list[dict]:
    candidates = load_candidates(candidates_file)
    selected = [item for item in candidates if not ids or item.get('id') in ids or item.get('code') in ids]
    if ids and len(selected) != len(ids):
        found = {item.get('id') for item in selected} | {item.get('code') for item in selected}
        missing = [item for item in ids if item not in found]
        raise ValueError(f'Candidate ids/codes not found: {", ".join(missing)}')
    promoted = [promote_candidate_record(item) for item in selected]
    if not dry_run:
        target = Path(examples_file) if examples_file else examples_path()
        document = _load_document(target)
        upsert_examples(document, promoted)
        _write_document(target, document)
    return promoted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Promote reviewed generated candidates into the public synthetic example catalog.')
    parser.add_argument('--candidates', required=True, help='Path to external candidates.json.')
    parser.add_argument('--ids', nargs='*', default=[], help='Candidate ids or codes to promote. Omit to promote all.')
    parser.add_argument('--examples', default=str(examples_path()), help='Path to synthetic_examples.json.')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    promoted = promote_candidates(
        candidates_file=args.candidates,
        ids=args.ids,
        examples_file=args.examples,
        dry_run=args.dry_run,
    )
    for item in promoted:
        print(f"{item['id']} | {item['code']} | {item['visual_intent']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
