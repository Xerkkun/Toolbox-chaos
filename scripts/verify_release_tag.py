"""Require a release workflow ref to match the project version exactly."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.app_metadata import APP_VERSION


class ReleaseTagError(ValueError):
    pass


def verify_release_tag(
    ref_name: str,
    ref_type: str,
    *,
    version: str = APP_VERSION,
) -> str:
    expected = f'v{version}'
    actual_name = str(ref_name).strip()
    actual_type = str(ref_type).strip().lower()
    if actual_type != 'tag':
        raise ReleaseTagError(
            f'La release debe ejecutarse desde un tag; ref_type={ref_type!r}.'
        )
    if actual_name != expected:
        raise ReleaseTagError(
            f'El tag {actual_name!r} no coincide con la versión del paquete '
            f'{version!r}; se requiere {expected!r}.'
        )
    return expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Verify that the release tag matches core.app_metadata.APP_VERSION.'
    )
    parser.add_argument(
        '--ref-name', default=os.environ.get('GITHUB_REF_NAME', '')
    )
    parser.add_argument(
        '--ref-type', default=os.environ.get('GITHUB_REF_TYPE', '')
    )
    args = parser.parse_args(argv)
    try:
        expected = verify_release_tag(args.ref_name, args.ref_type)
    except ReleaseTagError as exc:
        print(f'RELEASE_TAG_MISMATCH: {exc}', file=sys.stderr)
        return 1
    print(f'RELEASE_TAG_OK={expected}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
