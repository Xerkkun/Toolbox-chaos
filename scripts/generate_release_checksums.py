from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import re
import sys
from typing import Iterable


PLATFORM_ASSET_PATTERN = re.compile(
    r'^chaos-toolbox-v(?P<version>\d+\.\d+\.\d+)-'
    r'(?P<platform>windows|macos|linux)-'
    r'(?P<architecture>x64|arm64)'
    r'(?P<suffix>-setup\.exe|\.dmg|\.deb)$',
    re.IGNORECASE,
)
PUBLIC_ASSET_PATTERNS = (
    PLATFORM_ASSET_PATTERN,
    re.compile(r'^chaos_toolbox-\d+\.\d+\.\d+-.+\.whl$', re.IGNORECASE),
    re.compile(r'^chaos_toolbox-\d+\.\d+\.\d+\.tar\.gz$', re.IGNORECASE),
    re.compile(r'^chaos-toolbox-v\d+\.\d+\.\d+-.+\.cdx\.json$', re.IGNORECASE),
    re.compile(r'^qt-everywhere-src-\d+\.\d+\.\d+\.tar\.xz$', re.IGNORECASE),
    re.compile(
        r'^pyside-setup-everywhere-src-\d+\.\d+\.\d+\.tar\.xz$',
        re.IGNORECASE,
    ),
)


class ReleaseChecksumError(RuntimeError):
    pass


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def discover_release_assets(input_root: Path, *, version: str) -> list[Path]:
    root = Path(input_root).resolve()
    if not root.is_dir():
        raise ReleaseChecksumError(f'Input root does not exist: {root}')
    discovered = [
        path
        for path in root.rglob('*')
        if path.is_file()
        and any(pattern.fullmatch(path.name) for pattern in PUBLIC_ASSET_PATTERNS)
    ]
    expected_tokens = (f'-v{version}-', f'_{version}', f'-{version}')
    mismatched = [
        path.name
        for path in discovered
        if not any(token in path.name for token in expected_tokens)
        and not re.search(r'-(?:everywhere-src-)?\d+\.\d+\.\d+\.tar\.xz$', path.name)
    ]
    if mismatched:
        raise ReleaseChecksumError(
            f'Assets do not match release version {version}: {sorted(mismatched)}'
        )
    if not discovered:
        raise ReleaseChecksumError('No public release assets were found.')
    return discovered


def write_sha256_manifest(
    assets: Iterable[Path],
    output: Path,
    *,
    required_platforms: Iterable[str] = (),
) -> list[Path]:
    selected = sorted((Path(path).resolve() for path in assets), key=lambda path: path.name.lower())
    names: dict[str, Path] = {}
    for path in selected:
        if not path.is_file():
            raise ReleaseChecksumError(f'Release asset does not exist: {path}')
        key = path.name.lower()
        if key in names:
            raise ReleaseChecksumError(
                f'Duplicate release asset basename: {path.name} '
                f'({names[key]} and {path})'
            )
        names[key] = path

    available_platforms = {
        match.group('platform').lower()
        for path in selected
        if (match := PLATFORM_ASSET_PATTERN.fullmatch(path.name))
    }
    missing = {
        str(platform).strip().lower()
        for platform in required_platforms
        if str(platform).strip().lower() not in available_platforms
    }
    if missing:
        raise ReleaseChecksumError(
            f'Missing required platform installers: {sorted(missing)}'
        )

    target = Path(output).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'{_file_sha256(path)}  {path.name}' for path in selected]
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    return selected


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Generate the consolidated SHA256SUMS for GitHub Release assets.'
    )
    parser.add_argument('--input-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--version', required=True)
    parser.add_argument(
        '--require-platform',
        action='append',
        choices=('windows', 'macos', 'linux'),
        default=[],
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        assets = discover_release_assets(args.input_root, version=args.version)
        selected = write_sha256_manifest(
            assets,
            args.output,
            required_platforms=args.require_platform,
        )
    except ReleaseChecksumError as exc:
        print(f'[FAIL] {exc}', file=sys.stderr)
        return 1
    print(f'[OK] Wrote {args.output} for {len(selected)} release assets.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
