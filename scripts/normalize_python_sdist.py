from __future__ import annotations

import argparse
import copy
import gzip
import io
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile


class SdistNormalizationError(RuntimeError):
    pass


def source_date_epoch() -> int:
    raw = os.environ.get('SOURCE_DATE_EPOCH', '')
    if not raw.isascii() or not raw.isdecimal():
        raise SdistNormalizationError(
            'SOURCE_DATE_EPOCH must be a non-negative integer.'
        )
    return int(raw)


def _validate_member(member: tarfile.TarInfo) -> None:
    path = PurePosixPath(member.name)
    if path.is_absolute() or not path.parts or '..' in path.parts:
        raise SdistNormalizationError(
            f'Unsafe sdist member path: {member.name!r}'
        )
    if not (member.isfile() or member.isdir()):
        raise SdistNormalizationError(
            f'Unsupported sdist member type: {member.name!r}'
        )


def _normalized_mode(member: tarfile.TarInfo) -> int:
    if member.isdir():
        return 0o755
    return 0o755 if member.mode & 0o111 else 0o644


def normalize_sdist(path: Path, *, epoch: int) -> None:
    path = path.resolve(strict=True)
    if not path.name.endswith('.tar.gz'):
        raise SdistNormalizationError(
            f'Expected one .tar.gz source distribution, got {path.name!r}.'
        )

    temporary_path: Path | None = None
    try:
        with tarfile.open(path, mode='r:gz') as source:
            members = source.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)):
                raise SdistNormalizationError('The sdist contains duplicate paths.')
            for member in members:
                _validate_member(member)

            with tempfile.NamedTemporaryFile(
                mode='wb',
                dir=path.parent,
                prefix=f'.{path.name}.',
                suffix='.tmp',
                delete=False,
            ) as raw_output:
                temporary_path = Path(raw_output.name)
                with gzip.GzipFile(
                    filename='',
                    mode='wb',
                    compresslevel=9,
                    fileobj=raw_output,
                    mtime=epoch,
                ) as gzip_output:
                    with tarfile.open(
                        fileobj=gzip_output,
                        mode='w',
                        format=tarfile.PAX_FORMAT,
                    ) as destination:
                        for member in sorted(members, key=lambda item: item.name):
                            normalized = copy.copy(member)
                            normalized.uid = 0
                            normalized.gid = 0
                            normalized.uname = ''
                            normalized.gname = ''
                            normalized.mtime = epoch
                            normalized.mode = _normalized_mode(member)
                            normalized.pax_headers = {}

                            payload = None
                            if member.isfile():
                                extracted = source.extractfile(member)
                                if extracted is None:
                                    raise SdistNormalizationError(
                                        f'Cannot read sdist member: {member.name!r}'
                                    )
                                with extracted:
                                    payload = io.BytesIO(extracted.read())
                            destination.addfile(normalized, payload)

        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Normalize a Python sdist for byte-for-byte comparison.'
    )
    parser.add_argument('sdist', type=Path)
    args = parser.parse_args()
    normalize_sdist(args.sdist, epoch=source_date_epoch())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
