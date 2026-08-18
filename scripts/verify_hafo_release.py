"""Fail clearly until a compatible Hidden Attractors FO release is public."""
from __future__ import annotations

import json
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

from packaging.version import InvalidVersion, Version


PYPI_JSON_URL = 'https://pypi.org/pypi/hidden-attractors-fo/json'
MINIMUM_VERSION = Version('1.1')
MAXIMUM_VERSION = Version('2')
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def compatible_public_versions(payload: dict) -> list[Version]:
    versions: list[Version] = []
    releases = payload.get('releases', {})
    if not isinstance(releases, dict):
        return versions
    for raw_version, files in releases.items():
        if not files:
            continue
        try:
            version = Version(raw_version)
        except InvalidVersion:
            continue
        if MINIMUM_VERSION <= version < MAXIMUM_VERSION and not version.is_prerelease:
            versions.append(version)
    return sorted(set(versions))


def fetch_pypi_payload() -> dict:
    request = Request(PYPI_JSON_URL, headers={'User-Agent': 'chaos-toolbox-release-gate/1'})
    try:
        with urlopen(request, timeout=20) as response:
            length = response.headers.get('Content-Length')
            if length is not None and int(length) > MAX_RESPONSE_BYTES:
                raise RuntimeError('La respuesta de PyPI excede el límite de 2 MiB.')
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, URLError, ValueError) as exc:
        raise RuntimeError(f'No se pudo consultar el índice público de PyPI: {exc}') from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError('La respuesta de PyPI excede el límite de 2 MiB.')
    try:
        payload = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f'PyPI devolvió una respuesta inválida: {exc}') from exc
    if not isinstance(payload, dict):
        raise RuntimeError('PyPI devolvió una respuesta con estructura inválida.')
    return payload


def main() -> int:
    compatible = compatible_public_versions(fetch_pypi_payload())
    if not compatible:
        print(
            'RELEASE BLOCKED: hidden-attractors-fo>=1.1,<2 todavía no tiene una '
            'versión pública compatible en PyPI. No se sustituirá por 1.0 ni por '
            'un checkout hermano.',
            file=sys.stderr,
        )
        return 1
    print(f'HAFO_RELEASE_GATE_OK={compatible[-1]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
