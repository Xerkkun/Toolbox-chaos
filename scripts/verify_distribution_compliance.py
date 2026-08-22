from __future__ import annotations

import argparse
from email.parser import Parser
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
from pathlib import Path, PurePosixPath
import platform
import re
import sys
import tarfile
import tomllib
import zipfile
import zlib

from packaging.requirements import InvalidRequirement, Requirement


ROOT = Path(__file__).resolve().parents[1]
LEGACY_QT_BINDING = 'PyQt' + '6'
REQUIRED_NOTICE_BASENAMES = {
    'LICENSE',
    'NOTICE.md',
    'THIRD_PARTY_NOTICES.md',
    'LGPL-3.0-only.txt',
    'GPL-3.0-only.txt',
    'Chromium-BSD-3-Clause.txt',
    'QtWebEngine-Third-Party-NOTICE.txt',
    'Qt-PySide-6.11.1-Corresponding-Source.txt',
    'Qt-6.11.1-Security-Inventory.txt',
}
PEP639_LICENSE_PATTERNS = {
    'LICENSE',
    'NOTICE.md',
    'THIRD_PARTY_NOTICES.md',
    'LICENSES/*.txt',
}
PEP639_LICENSE_FILES = {
    'LICENSE',
    'NOTICE.md',
    'THIRD_PARTY_NOTICES.md',
    'LICENSES/LGPL-3.0-only.txt',
    'LICENSES/GPL-3.0-only.txt',
    'LICENSES/Chromium-BSD-3-Clause.txt',
    'LICENSES/QtWebEngine-Third-Party-NOTICE.txt',
    'LICENSES/Qt-PySide-6.11.1-Corresponding-Source.txt',
    'LICENSES/Qt-6.11.1-Security-Inventory.txt',
}
EXCLUDED_OPTIONAL_QT_COMPONENT = re.compile(
    r'(^|/)(?:lib)?qt6?(?:svgwidgets|core5compat|xml)(?:[./]|$)|'
    r'(^|/)qml/qt5compat(?:/|$)',
    re.IGNORECASE,
)
EXCLUDED_UNUSED_PYQTGRAPH_COMPONENT = re.compile(
    r'(^|/)opengl(?:/|$)|^opengl(?:\.|$)|'
    r'(^|[/.])pyqtgraph[/.]opengl(?:[/.]|$)|'
    r'(^|/)pyqtgraph/qt(?:/[^/]+)*/[^/]+\.pyi$|'
    r'(^|[/.])(?:numba[/.]np[/.]ufunc[/.])?tbbpool(?:[._/-]|$)',
    re.IGNORECASE,
)
REQUIRED_NUMBA_THREADING_COMPONENT = re.compile(
    r'(^|/)workqueue(?:[._/-]|$)',
    re.IGNORECASE,
)
EXCLUDED_WEBENGINE_DEBUG_COMPONENT = re.compile(
    r'(^|/)pyside6/qt/.+\.debug$|'
    r'(^|/)[^/]*qtwebengine[^/]*\.debug$',
    re.IGNORECASE,
)
EXCLUDED_GPL_ONLY_QT_COMPONENT = re.compile(
    r'(^|/)(?:lib)?qt6?(?:canvas3d|charts|coap|datavisualization|graphs|grpc|httpserver|'
    r'lottieanimation|bodymovin|mqtt|networkauth|qmlcompiler|quick3d|'
    r'quicktimeline|virtualkeyboard|waylandcompositor)[a-z0-9]*(?:[._/-]|$)|'
    r'(^|/)qml/(?:qtcharts|qtdatavisualization|qtgraphs|qtquick3d(?:/|$)|qtquick/timeline(?:/|$)|'
    r'qtquick/virtualkeyboard(?:/|$)|qtwayland/compositor(?:/|$))|'
    r'(^|/)plugins/(?:platforminputcontexts/qtvirtualkeyboard|'
    r'qmltooling/qmldbg_quick3d)',
    re.IGNORECASE,
)
TRUSTED_BIBLIOGRAPHY_URLS = {
    'https://sprott.physics.wisc.edu/fractals/booktext/SABOOK.HTM',
    'https://doi.org/10.1103/PhysRevE.50.R647',
    'https://doi.org/10.1007/978-3-030-75821-9',
}
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
TEXT_SUFFIXES = {
    '.cfg', '.ini', '.json', '.md', '.py', '.pyi', '.ps1', '.rst',
    '.sh', '.spec', '.toml', '.txt', '.yaml', '.yml',
}
RELEASE_PYTHON_VERSION = (3, 14, 6)
RELEASE_RUNTIME_PINS = {
    'contourpy': '1.3.3',
    'cycler': '0.12.1',
    'fonttools': '4.63.0',
    'hidden-attractors-fo': '1.2.0',
    'kiwisolver': '1.5.0',
    'llvmlite': '0.49.0',
    'matplotlib': '3.11.1',
    'numba': '0.67.0',
    'numpy': '2.5.2',
    'packaging': '26.3',
    'pillow': '12.3.0',
    'pyparsing': '3.3.2',
    'pyqtgraph': '0.14.0',
    'pyside6-addons': '6.11.1',
    'pyside6-essentials': '6.11.1',
    'python-dateutil': '2.9.0.post0',
    'pyyaml': '6.0.3',
    'scipy': '1.18.0',
    'shiboken6': '6.11.1',
    'six': '1.17.0',
}
RELEASE_PLATFORM_PINS = {
    'colorama': ('0.4.6', 'sys_platform == "win32"'),
}
LOCAL_FILE_URI = re.compile(
    r'file' + r':///' + r'(?:[a-z]:/(?:users)/|(?:users|home)/)',
    re.IGNORECASE,
)


class ComplianceError(RuntimeError):
    pass


def canonical_name(value: str) -> str:
    return re.sub(r'[-_.]+', '-', value).lower()


def _is_legacy_distribution(value: str) -> bool:
    name = canonical_name(value)
    legacy = canonical_name(LEGACY_QT_BINDING)
    return name == legacy or name.startswith(f'{legacy}-')


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ComplianceError(message)


def _requirement_name(value: str, *, source: str) -> str | None:
    stripped = value.strip()
    if (
        not stripped
        or stripped.startswith('#')
        or stripped.startswith('-r ')
        or stripped.startswith('-c ')
    ):
        return None
    try:
        return canonical_name(Requirement(stripped).name)
    except InvalidRequirement as exc:
        raise ComplianceError(f'Invalid requirement in {source}: {stripped!r}') from exc


def _release_pin_versions() -> dict[str, str]:
    constraint_path = ROOT / 'requirements-release.txt'
    _require(constraint_path.is_file(), 'requirements-release.txt is missing.')
    qt_names = {'pyside6-essentials', 'pyside6-addons', 'shiboken6'}
    required_names = set(RELEASE_RUNTIME_PINS) | set(RELEASE_PLATFORM_PINS)
    pins: dict[str, str] = {}
    declared: set[str] = set()
    for raw in constraint_path.read_text(encoding='utf-8').splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            continue
        try:
            requirement = Requirement(stripped)
        except InvalidRequirement as exc:
            raise ComplianceError(
                f'Invalid requirement in {constraint_path}: {stripped!r}'
            ) from exc
        name = canonical_name(requirement.name)
        if name not in required_names:
            continue
        _require(name not in declared, f'Duplicate official runtime pin: {name}')
        declared.add(name)
        specifier = str(requirement.specifier)
        _require(
            re.fullmatch(r'==[^,;\s]+', specifier) is not None,
            f'{requirement.name} must use one exact release pin, got {specifier!r}.',
        )
        version = specifier[2:]
        expected_version = (
            RELEASE_RUNTIME_PINS[name]
            if name in RELEASE_RUNTIME_PINS
            else RELEASE_PLATFORM_PINS[name][0]
        )
        _require(
            version == expected_version,
            f'{requirement.name} must remain pinned to {expected_version}, '
            f'got {version}.',
        )
        if name in RELEASE_RUNTIME_PINS:
            _require(
                requirement.marker is None,
                f'{requirement.name} is a cross-platform runtime pin and '
                'must not use an environment marker.',
            )
            pins[name] = version
        else:
            expected_marker = RELEASE_PLATFORM_PINS[name][1]
            _require(
                str(requirement.marker) == expected_marker,
                f'{requirement.name} must use marker {expected_marker!r}.',
            )
            if requirement.marker.evaluate():
                pins[name] = version

    missing = sorted(required_names - declared)
    _require(not missing, f'Official release constraints omit exact pins: {missing}')
    qt_pins = {name: pins[name] for name in sorted(qt_names)}
    _require(
        len(set(qt_pins.values())) == 1,
        f'Essentials, Addons, and Shiboken release pins differ: {qt_pins}',
    )
    _require(
        pins['hidden-attractors-fo'] == '1.2.0',
        'The validated Hidden Attractors FO release pin must remain 1.2.0.',
    )
    return pins


def _build_pin_versions() -> dict[str, str]:
    constraint_path = ROOT / 'requirements-release.txt'
    expected = {
        'pyinstaller': '6.22.0',
        'pyinstaller-hooks-contrib': '2026.6',
    }
    pins: dict[str, str] = {}
    for raw in constraint_path.read_text(encoding='utf-8').splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            continue
        try:
            requirement = Requirement(stripped)
        except InvalidRequirement as exc:
            raise ComplianceError(
                f'Invalid requirement in {constraint_path}: {stripped!r}'
            ) from exc
        name = canonical_name(requirement.name)
        if name not in expected:
            continue
        specifier = str(requirement.specifier)
        _require(
            specifier == f'=={expected[name]}',
            f'{requirement.name} must remain pinned to {expected[name]}, '
            f'got {specifier!r}.',
        )
        _require(name not in pins, f'Duplicate official build pin: {name}')
        pins[name] = expected[name]
    missing = sorted(expected.keys() - pins.keys())
    _require(not missing, f'Official release constraints omit build pins: {missing}')
    return pins


def _bootstrap_pin_version() -> str:
    bootstrap_path = ROOT / 'requirements-bootstrap.txt'
    _require(bootstrap_path.is_file(), 'requirements-bootstrap.txt is missing.')
    requirements = [
        Requirement(raw.strip())
        for raw in bootstrap_path.read_text(encoding='utf-8').splitlines()
        if raw.strip() and not raw.lstrip().startswith('#')
    ]
    _require(
        len(requirements) == 1 and canonical_name(requirements[0].name) == 'pip',
        'requirements-bootstrap.txt must contain only the reviewed pip pin.',
    )
    specifier = str(requirements[0].specifier)
    _require(
        specifier == '==26.2.1',
        f'The official build bootstrap requires pip==26.2.1, got {specifier!r}.',
    )
    return '26.2.1'


def _notice_source_paths() -> dict[str, Path]:
    return {
        'LICENSE': ROOT / 'LICENSE',
        'NOTICE.md': ROOT / 'NOTICE.md',
        'THIRD_PARTY_NOTICES.md': ROOT / 'THIRD_PARTY_NOTICES.md',
        'LGPL-3.0-only.txt': ROOT / 'LICENSES' / 'LGPL-3.0-only.txt',
        'GPL-3.0-only.txt': ROOT / 'LICENSES' / 'GPL-3.0-only.txt',
        'Chromium-BSD-3-Clause.txt': (
            ROOT / 'LICENSES' / 'Chromium-BSD-3-Clause.txt'
        ),
        'QtWebEngine-Third-Party-NOTICE.txt': (
            ROOT / 'LICENSES' / 'QtWebEngine-Third-Party-NOTICE.txt'
        ),
        'Qt-PySide-6.11.1-Corresponding-Source.txt': (
            ROOT / 'LICENSES' / 'Qt-PySide-6.11.1-Corresponding-Source.txt'
        ),
        'Qt-6.11.1-Security-Inventory.txt': (
            ROOT / 'LICENSES' / 'Qt-6.11.1-Security-Inventory.txt'
        ),
    }


def _scan_text_for_legacy_binding(text: str, *, source: str) -> None:
    token = re.escape(LEGACY_QT_BINDING)
    patterns = (
        rf'(?im)^\s*(?:from|import)\s+{token}\b',
        rf'(?im)^Requires-Dist:\s*{token}(?:[-_.][A-Za-z0-9]+)?\b',
        rf'(?im)\bpip(?:3)?\s+install[^\r\n]*\b{token}(?:[-_.][A-Za-z0-9]+)?\b',
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise ComplianceError(f'Legacy Qt binding reference found in distributable content: {source}')


def _verify_pep639_metadata(content: bytes, *, source: str) -> None:
    parsed = Parser().parsestr(content.decode('utf-8', errors='replace'))
    metadata_version = parsed.get('Metadata-Version', '')
    try:
        metadata_version_parts = tuple(
            int(part) for part in metadata_version.split('.')
        )
    except ValueError:
        metadata_version_parts = ()
    _require(
        metadata_version_parts >= (2, 4),
        f'{source} must use Core Metadata >=2.4 for PEP 639; '
        f'got {metadata_version!r}.',
    )
    _require(
        parsed.get('License-Expression') == 'MIT',
        f'{source} must declare License-Expression: MIT.',
    )
    declared = {
        PurePosixPath(value.replace('\\', '/')).as_posix()
        for value in parsed.get_all('License-File', [])
    }
    missing = sorted(PEP639_LICENSE_FILES - declared)
    _require(
        not missing,
        f'{source} omits PEP 639 License-File entries: {missing}',
    )


def _verify_license_files() -> None:
    required = {
        ROOT / 'LICENSE': ('MIT License', 'Permission is hereby granted'),
        ROOT / 'LICENSES' / 'LGPL-3.0-only.txt': (
            'GNU LESSER GENERAL PUBLIC LICENSE',
            'Version 3, 29 June 2007',
        ),
        ROOT / 'LICENSES' / 'GPL-3.0-only.txt': (
            'GNU GENERAL PUBLIC LICENSE',
            'Version 3, 29 June 2007',
        ),
        ROOT / 'LICENSES' / 'Chromium-BSD-3-Clause.txt': (
            'Copyright 2015 The Chromium Authors',
            'Redistributions in binary form must reproduce',
        ),
        ROOT / 'LICENSES' / 'QtWebEngine-Third-Party-NOTICE.txt': (
            'Qt WebEngine 6.11.1',
            'qtwebengine_resources.pak',
        ),
        ROOT / 'LICENSES' / 'Qt-PySide-6.11.1-Corresponding-Source.txt': (
            'Resolved Qt for Python version: 6.11.1',
            '252acef8c5ae68074d91cadba2ee4a83465051bbb970dd26e8f0daa0f3904e03',
            '6ffd9835bb0dd2c56f061d62f1616bb1707cfc0202b80e3165d6be087f3965e2',
        ),
        ROOT / 'LICENSES' / 'Qt-6.11.1-Security-Inventory.txt': (
            'CVE-2026-8168-qtsvg-6.11',
            'PySide6.QtSvgWidgets',
            'trusted-input risk',
        ),
    }
    for path, markers in required.items():
        _require(path.is_file(), f'Required license file is missing: {path}')
        text = path.read_text(encoding='utf-8')
        for marker in markers:
            _require(marker in text, f'{path} does not contain expected marker: {marker}')

    third_party = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
    for marker in (
        'PySide6-Essentials', 'PySide6-Addons', 'Shiboken6', 'LGPLv3',
        'Qt WebEngine', 'Chromium-BSD-3-Clause.txt',
        'QtWebEngine-Third-Party-NOTICE.txt',
    ):
        _require(marker in third_party, f'THIRD_PARTY_NOTICES.md is missing {marker!r}.')


def _is_link_like(path: Path) -> bool:
    is_junction = getattr(path, 'is_junction', lambda: False)
    return path.is_symlink() or bool(is_junction())


def _verify_png_resource(path: Path) -> None:
    _require(path.suffix.casefold() == '.png', f'Only PNG is allowed: {path}')
    _require(path.is_file() and not _is_link_like(path), f'Unsafe PNG path: {path}')
    data = path.read_bytes()
    _require(
        len(PNG_SIGNATURE) < len(data) <= 64 * 1024 * 1024,
        f'PNG size is outside the reviewed limit: {path}',
    )
    _require(data.startswith(PNG_SIGNATURE), f'PNG signature mismatch: {path}')

    offset = len(PNG_SIGNATURE)
    width = height = 0
    compressed = bytearray()
    seen_ihdr = seen_iend = False
    while offset < len(data):
        _require(offset + 12 <= len(data), f'Truncated PNG chunk: {path}')
        length = int.from_bytes(data[offset:offset + 4], 'big')
        chunk_type = data[offset + 4:offset + 8]
        chunk_end = offset + 12 + length
        _require(chunk_end <= len(data), f'Truncated PNG payload: {path}')
        payload = data[offset + 8:offset + 8 + length]
        expected_crc = int.from_bytes(data[offset + 8 + length:chunk_end], 'big')
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        _require(actual_crc == expected_crc, f'PNG checksum mismatch: {path}')
        if chunk_type == b'IHDR':
            _require(not seen_ihdr and length == 13, f'Invalid PNG IHDR: {path}')
            width = int.from_bytes(payload[0:4], 'big')
            height = int.from_bytes(payload[4:8], 'big')
            _require(
                0 < width and 0 < height and width * height <= 64_000_000,
                f'PNG dimensions are outside the reviewed limit: {path}',
            )
            seen_ihdr = True
        elif chunk_type == b'IDAT':
            compressed.extend(payload)
        elif chunk_type == b'IEND':
            _require(length == 0, f'Invalid PNG IEND: {path}')
            seen_iend = True
            offset = chunk_end
            break
        offset = chunk_end

    _require(seen_ihdr and seen_iend and compressed, f'Incomplete PNG: {path}')
    _require(offset == len(data), f'PNG contains trailing data: {path}')
    decoded_limit = min(256 * 1024 * 1024, width * height * 16 + height + 1024)
    try:
        inflater = zlib.decompressobj()
        decoded = inflater.decompress(bytes(compressed), decoded_limit + 1)
        _require(
            not inflater.unconsumed_tail and len(decoded) <= decoded_limit,
            f'PNG decompression exceeds the reviewed limit: {path}',
        )
        decoded += inflater.flush(max(1, decoded_limit + 1 - len(decoded)))
    except zlib.error as exc:
        raise ComplianceError(f'PNG stream cannot be decoded: {path}') from exc
    _require(
        inflater.eof and not inflater.unconsumed_tail and len(decoded) <= decoded_limit,
        f'PNG decompression is incomplete or exceeds the reviewed limit: {path}',
    )


def _verify_trusted_runtime_resources() -> None:
    bundled = ROOT / 'resources' / 'bundled'
    sprott_root = bundled / 'sprott'
    thumbnail_root = sprott_root / 'examples' / 'thumbnails'
    examples_path = sprott_root / 'examples' / 'synthetic_examples.json'
    payload = json.loads(examples_path.read_text(encoding='utf-8'))
    examples = payload.get('examples')
    _require(isinstance(examples, list) and examples, 'Synthetic examples are missing.')

    referenced: set[str] = set()
    for entry in examples:
        _require(isinstance(entry, dict), 'Synthetic example metadata must be objects.')
        raw = entry.get('thumbnail')
        _require(isinstance(raw, str), 'Synthetic example thumbnail path is missing.')
        relative = PurePosixPath(raw)
        _require(
            not relative.is_absolute()
            and '..' not in relative.parts
            and relative.parts[:2] == ('examples', 'thumbnails')
            and relative.suffix.casefold() == '.png',
            f'Untrusted thumbnail path: {raw!r}',
        )
        candidate = sprott_root.joinpath(*relative.parts)
        try:
            candidate.resolve(strict=True).relative_to(thumbnail_root.resolve(strict=True))
        except (OSError, ValueError) as exc:
            raise ComplianceError(f'Thumbnail escapes its trusted root: {raw!r}') from exc
        _verify_png_resource(candidate)
        referenced.add(relative.as_posix())

    actual = {
        path.relative_to(sprott_root).as_posix()
        for path in thumbnail_root.iterdir()
        if path.is_file()
    }
    _require(actual == referenced, 'Bundled thumbnail inventory differs from metadata.')

    image_pattern = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
    url_pattern = re.compile(r'https?://[^\s<>)]+', re.IGNORECASE)
    for markdown in bundled.rglob('*.md'):
        _require(not _is_link_like(markdown), f'Bundled Markdown is linked: {markdown}')
        text = markdown.read_text(encoding='utf-8')
        urls = {match.rstrip('.,;') for match in url_pattern.findall(text)}
        unknown_urls = sorted(urls - TRUSTED_BIBLIOGRAPHY_URLS)
        _require(not unknown_urls, f'Bundled Markdown has unreviewed URLs: {unknown_urls}')
        _require('file:' not in text.casefold(), f'Bundled Markdown uses file URI: {markdown}')
        _require(re.search(r'(?i)\.svg\b', text) is None, f'Bundled Markdown names SVG: {markdown}')
        for raw_target in image_pattern.findall(text):
            target = raw_target.strip()
            relative = PurePosixPath(target)
            _require(
                ':' not in target
                and not relative.is_absolute()
                and '..' not in relative.parts
                and relative.suffix.casefold() == '.png',
                f'Bundled Markdown has an unsafe image target: {target!r}',
            )
            candidate = markdown.parent.joinpath(*relative.parts)
            try:
                candidate.resolve(strict=True).relative_to(bundled.resolve(strict=True))
            except (OSError, ValueError) as exc:
                raise ComplianceError(
                    f'Bundled Markdown image escapes the resource root: {target!r}'
                ) from exc
            _verify_png_resource(candidate)

    image_security = (ROOT / 'core' / 'image_security.py').read_text(encoding='utf-8')
    gallery = (ROOT / 'core' / 'sprott' / 'gallery.py').read_text(encoding='utf-8')
    markdown_ui = (ROOT / 'ui' / 'sprott_explorer_tab.py').read_text(encoding='utf-8')
    for marker in ('from PIL import Image', 'def validate_png_file', 'def confined_png', 'image.verify()'):
        _require(marker in image_security, f'Runtime PNG security contract omits {marker!r}.')
    _require(
        'confined_png(entry_dir' in gallery and 'validate_png_file(render_path)' in gallery,
        'User gallery does not enforce confined, decoded PNG inputs.',
    )
    _require(
        'return confined_png(asset_root, src).as_uri()' in markdown_ui,
        'Markdown images do not enforce the confined PNG boundary.',
    )


def verify_source_contract() -> None:
    pyproject_path = ROOT / 'pyproject.toml'
    project_doc = tomllib.loads(pyproject_path.read_text(encoding='utf-8'))
    project = project_doc.get('project', {})

    dependency_groups = {
        'runtime': project.get('dependencies', []),
        **project.get('optional-dependencies', {}),
    }
    dependency_names: dict[str, set[str]] = {}
    for group, requirements in dependency_groups.items():
        names: set[str] = set()
        for raw in requirements:
            name = _requirement_name(raw, source=f'pyproject.toml:{group}')
            if name is not None:
                names.add(name)
                _require(
                    not _is_legacy_distribution(name),
                    f'Legacy Qt binding declared in pyproject.toml:{group}: {raw}',
                )
        dependency_names[group] = names

    _require(
        'pyside6-essentials' in dependency_names.get('runtime', set()),
        'PySide6-Essentials must be a normal runtime dependency.',
    )
    _require(
        'pyside6-addons' in dependency_names.get('runtime', set()),
        'PySide6-Addons must be a normal runtime dependency for QtSvg/QtPdf.',
    )
    _require(
        'pyside6-addons' in dependency_names.get('webengine', set()),
        'PySide6-Addons must be declared by the webengine extra.',
    )
    _require(
        'cyclonedx-bom' in dependency_names.get('build', set()),
        'The build extra must provide cyclonedx-bom.',
    )

    release_pins = _release_pin_versions()
    _build_pin_versions()
    _bootstrap_pin_version()
    qt_versions = {
        release_pins[name]
        for name in ('pyside6-essentials', 'pyside6-addons', 'shiboken6')
    }
    qt_version = next(iter(qt_versions))
    source_manifest = (
        ROOT / 'LICENSES' / 'Qt-PySide-6.11.1-Corresponding-Source.txt'
    ).read_text(encoding='utf-8')
    _require(
        f'Resolved Qt for Python version: {qt_version}' in source_manifest,
        'The corresponding-source manifest does not match the Qt release pins.',
    )
    _verify_trusted_runtime_resources()

    for requirement_file in ROOT.glob('requirements*.txt'):
        for raw in requirement_file.read_text(encoding='utf-8').splitlines():
            name = _requirement_name(raw, source=str(requirement_file))
            if name is not None:
                _require(
                    not _is_legacy_distribution(name),
                    f'Legacy Qt binding declared in {requirement_file}: {raw}',
                )

    setuptools = project_doc.get('tool', {}).get('setuptools', {})
    license_files = set(project.get('license-files', []))
    _require(
        license_files == PEP639_LICENSE_PATTERNS,
        'PEP 639 project.license-files must contain the reviewed license set: '
        f'{sorted(PEP639_LICENSE_PATTERNS)}.',
    )
    _require(
        'license-files' not in setuptools,
        'Legacy tool.setuptools.license-files must not shadow PEP 639 metadata.',
    )

    data_files = setuptools.get('data-files', {})
    packaged = {
        PurePosixPath(item.replace('\\', '/')).name
        for entries in data_files.values()
        for item in entries
    }
    _require(
        REQUIRED_NOTICE_BASENAMES <= packaged,
        f'Wheel data-files omit notices: {sorted(REQUIRED_NOTICE_BASENAMES - packaged)}',
    )

    _verify_license_files()

    scan_files = [
        ROOT / 'pyproject.toml',
        *ROOT.glob('requirements*.txt'),
        ROOT / 'run.ps1',
        ROOT / 'run-webengine.ps1',
        ROOT / 'run-linux.sh',
        ROOT / 'run-macos.command',
    ]
    scan_dirs = (
        ROOT / 'core',
        ROOT / 'ui',
        ROOT / 'packaging',
        ROOT / 'scripts',
        ROOT / '.github' / 'workflows',
        ROOT / 'resources' / 'bundled',
    )
    for directory in scan_dirs:
        if directory.exists():
            scan_files.extend(
                path for path in directory.rglob('*')
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
            )
    for path in scan_files:
        if not path.is_file():
            continue
        _scan_text_for_legacy_binding(
            path.read_text(encoding='utf-8', errors='replace'),
            source=str(path),
        )


def verify_installed_environment(*, require_webengine: bool = False) -> None:
    installed_pip = metadata.version('pip')
    expected_pip = _bootstrap_pin_version()
    _require(
        installed_pip == expected_pip,
        f'Build bootstrap pip drift: expected {expected_pip}, got {installed_pip}.',
    )
    distributions = {
        canonical_name(dist.metadata.get('Name', ''))
        for dist in metadata.distributions()
        if dist.metadata.get('Name')
    }
    legacy = sorted(name for name in distributions if _is_legacy_distribution(name))
    _require(not legacy, f'Legacy Qt distributions installed in build environment: {legacy}')

    try:
        legacy_spec = importlib.util.find_spec(LEGACY_QT_BINDING)
    except (ImportError, ModuleNotFoundError, ValueError):
        legacy_spec = None
    _require(legacy_spec is None, f'{LEGACY_QT_BINDING} is importable in the build environment.')

    required = {'pyside6-essentials', 'pyside6-addons', 'shiboken6'}
    missing = sorted(required - distributions)
    _require(not missing, f'Required PySide6 distributions are not installed: {missing}')
    _require(importlib.util.find_spec('PySide6') is not None, 'PySide6 is not importable.')
    if require_webengine:
        _require(
            importlib.util.find_spec('PySide6.QtWebEngineWidgets') is not None,
            'PySide6.QtWebEngineWidgets is not importable.',
        )


def verify_installed_release_pins() -> None:
    current_python = sys.version_info[:3]
    _require(
        current_python == RELEASE_PYTHON_VERSION,
        'Official release Python drift: expected '
        f'{".".join(map(str, RELEASE_PYTHON_VERSION))}, got '
        f'{".".join(map(str, current_python))}.',
    )
    expected = _release_pin_versions()
    expected['pip'] = _bootstrap_pin_version()
    mismatches: list[str] = []
    for distribution_name, expected_version in sorted(expected.items()):
        try:
            actual_version = metadata.version(distribution_name)
        except metadata.PackageNotFoundError:
            actual_version = '<missing>'
        if actual_version != expected_version:
            mismatches.append(
                f'{distribution_name}: expected {expected_version}, got {actual_version}'
            )
    _require(
        not mismatches,
        'Installed build/runtime versions do not match release pins: '
        + '; '.join(mismatches),
    )


def verify_installed_build_pins() -> None:
    expected = _build_pin_versions()
    mismatches: list[str] = []
    for distribution_name, expected_version in sorted(expected.items()):
        try:
            actual_version = metadata.version(distribution_name)
        except metadata.PackageNotFoundError:
            actual_version = '<missing>'
        if actual_version != expected_version:
            mismatches.append(
                f'{distribution_name}: expected {expected_version}, got {actual_version}'
            )
    _require(
        not mismatches,
        'Installed executable-build tools do not match release pins: '
        + '; '.join(mismatches),
    )


def _runtime_metadata_versions() -> dict[str, str]:
    pending: list[tuple[str, bool]] = [
        ('chaos-toolbox', True),
        ('PySide6-Addons', True),
        ('pyinstaller', False),
    ]
    resolved: dict[str, str] = {}
    expanded: set[str] = set()
    while pending:
        requested, recursive = pending.pop()
        try:
            distribution = metadata.distribution(requested)
        except metadata.PackageNotFoundError as exc:
            raise ComplianceError(
                f'Runtime metadata closure cannot resolve {requested!r}.'
            ) from exc

        declared_name = distribution.metadata.get('Name') or requested
        name = canonical_name(declared_name)
        version = distribution.version
        previous = resolved.get(name)
        _require(
            previous is None or previous == version,
            f'Runtime metadata closure resolves conflicting versions for '
            f'{name}: {previous!r} and {version!r}.',
        )
        resolved[name] = version
        if not recursive or name in expanded:
            continue
        expanded.add(name)
        for raw_requirement in distribution.requires or []:
            try:
                requirement = Requirement(raw_requirement)
            except InvalidRequirement as exc:
                raise ComplianceError(
                    f'Invalid installed requirement for {declared_name}: '
                    f'{raw_requirement!r}'
                ) from exc
            if requirement.marker is None or requirement.marker.evaluate():
                pending.append((requirement.name, True))
    return resolved


def _entry_has_legacy_name(name: str) -> bool:
    return any(_is_legacy_distribution(part) for part in PurePosixPath(name).parts)


def _verify_entries(entries: list[tuple[str, bytes | None]], *, source: str) -> None:
    names = [name.replace('\\', '/') for name, _ in entries]
    legacy_names = sorted(name for name in names if _entry_has_legacy_name(name))
    _require(not legacy_names, f'Legacy Qt files found in {source}: {legacy_names[:10]}')

    direct_url_names = sorted(
        name for name in names
        if PurePosixPath(name).name.lower() == 'direct_url.json'
    )
    _require(
        not direct_url_names,
        f'{source} contains local installation provenance: '
        f'{direct_url_names[:10]}',
    )
    stale_record_names = sorted(
        name for name, content in entries
        if PurePosixPath(name).name.lower() == 'record'
        and content is not None
        and 'direct_url.json' in content.decode('utf-8', errors='replace')
    )
    _require(
        not stale_record_names,
        f'{source} contains RECORD metadata for omitted local provenance: '
        f'{stale_record_names[:10]}',
    )

    basenames = {PurePosixPath(name).name for name in names}
    missing = REQUIRED_NOTICE_BASENAMES - basenames
    _require(not missing, f'{source} omits required notices: {sorted(missing)}')

    for basename, expected_path in _notice_source_paths().items():
        expected = expected_path.read_bytes()
        candidates = [
            content
            for name, content in entries
            if PurePosixPath(name).name == basename and content is not None
        ]
        _require(
            any(content == expected for content in candidates),
            f'{source} does not preserve the exact source notice {basename}.',
        )

    for name, content in entries:
        if content is None:
            continue
        path = PurePosixPath(name)
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {'METADATA', 'PKG-INFO'}:
            continue
        if len(content) > 2_000_000:
            continue
        text = content.decode('utf-8', errors='replace')
        _require(
            LOCAL_FILE_URI.search(text) is None,
            f'{source}:{name} contains a local file URI.',
        )
        _scan_text_for_legacy_binding(
            text,
            source=f'{source}:{name}',
        )


def verify_artifact(path: Path) -> None:
    path = path.resolve()
    _require(path.exists(), f'Artifact does not exist: {path}')
    if path.is_dir():
        entries: list[tuple[str, bytes | None]] = []
        for item in path.rglob('*'):
            if not item.is_file():
                continue
            relative = item.relative_to(path).as_posix()
            content = None
            if (
                item.suffix.lower() in TEXT_SUFFIXES
                or item.name in {'METADATA', 'PKG-INFO', 'RECORD'}
                or item.name in REQUIRED_NOTICE_BASENAMES
            ):
                content = item.read_bytes()
            entries.append((relative, content))
        _verify_entries(entries, source=str(path))
        excluded_optional_qt = sorted(
            name for name, _ in entries
            if (
                EXCLUDED_OPTIONAL_QT_COMPONENT.search(name.replace('\\', '/'))
                or EXCLUDED_GPL_ONLY_QT_COMPONENT.search(name.replace('\\', '/'))
            )
        )
        _require(
            not excluded_optional_qt,
            'Frozen bundle contains optional or GPL-only Qt components excluded '
            'by release policy: '
            f'{excluded_optional_qt[:10]}',
        )
        excluded_pyqtgraph = sorted(
            name for name, _ in entries
            if (
                EXCLUDED_UNUSED_PYQTGRAPH_COMPONENT.search(
                    name.replace('\\', '/')
                )
                or EXCLUDED_WEBENGINE_DEBUG_COMPONENT.search(
                    name.replace('\\', '/')
                )
            )
        )
        _require(
            not excluded_pyqtgraph,
            'Frozen bundle contains unused graphics/Numba/WebEngine debug components: '
            f'{excluded_pyqtgraph[:10]}',
        )

        found_metadata: dict[str, set[str]] = {}
        for name, content in entries:
            if PurePosixPath(name).name not in {'METADATA', 'PKG-INFO'}:
                continue
            if content is None:
                continue
            parsed = Parser().parsestr(content.decode('utf-8', errors='replace'))
            declared_name = parsed.get('Name')
            declared_version = parsed.get('Version')
            if (
                declared_name
                and canonical_name(declared_name) == 'chaos-toolbox'
                and content is not None
            ):
                _verify_pep639_metadata(
                    content, source=f'{path}:{name}'
                )
            if declared_name and declared_version:
                found_metadata.setdefault(
                    canonical_name(declared_name), set()
                ).add(declared_version)
        expected_metadata = _runtime_metadata_versions()
        if 'numba' in expected_metadata:
            numba_threading_components = sorted(
                name for name, _ in entries
                if REQUIRED_NUMBA_THREADING_COMPONENT.search(
                    name.replace('\\', '/')
                )
            )
            _require(
                numba_threading_components,
                f'{path} omits the portable Numba workqueue fallback after '
                'excluding tbbpool.',
            )
        missing_metadata = sorted(expected_metadata.keys() - found_metadata.keys())
        _require(
            not missing_metadata,
            f'{path} omits runtime distribution metadata: {missing_metadata}',
        )
        mismatched_metadata = {
            name: {'expected': expected, 'found': sorted(found_metadata[name])}
            for name, expected in sorted(expected_metadata.items())
            if name in found_metadata and found_metadata[name] != {expected}
        }
        _require(
            not mismatched_metadata,
            f'{path} contains runtime metadata version drift: '
            f'{mismatched_metadata}',
        )
        python_licenses = [
            content
            for name, content in entries
            if '/licenses/python/' in f"/{name.lower()}"
            and PurePosixPath(name).name.lower() in {'license', 'license.txt'}
            and content is not None
        ]
        _require(
            any(b'PYTHON SOFTWARE FOUNDATION LICENSE' in item for item in python_licenses),
            f'{path} omits the exact Python runtime license.',
        )
        _require(
            any(PurePosixPath(name).name == 'qtwebengine_resources.pak' for name, _ in entries),
            f'{path} omits required Qt WebEngine runtime resources.',
        )
        return

    lower = path.name.lower()
    if lower.endswith(('.whl', '.zip')):
        with zipfile.ZipFile(path) as archive:
            entries = []
            for info in archive.infolist():
                if info.is_dir():
                    continue
                content = None
                pure = PurePosixPath(info.filename)
                if (
                    pure.suffix.lower() in TEXT_SUFFIXES
                    or pure.name in {'METADATA', 'PKG-INFO', 'WHEEL', 'RECORD'}
                    or pure.name in REQUIRED_NOTICE_BASENAMES
                ):
                    content = archive.read(info)
                entries.append((info.filename, content))
        _verify_entries(entries, source=str(path))
        if lower.endswith('.whl'):
            metadata_entries = [
                content
                for name, content in entries
                if name.endswith('.dist-info/METADATA') and content is not None
            ]
            _require(metadata_entries, f'{path} omits wheel METADATA.')
            chaos_metadata = [
                item for item in metadata_entries
                if canonical_name(
                    Parser().parsestr(
                        item.decode('utf-8', errors='replace')
                    ).get('Name', '')
                ) == 'chaos-toolbox'
            ]
            _require(
                chaos_metadata,
                f'{path} METADATA does not identify chaos-toolbox.',
            )
            for content in chaos_metadata:
                _verify_pep639_metadata(content, source=f'{path}:METADATA')
            _require(
                any(name.endswith('.dist-info/WHEEL') for name, _ in entries),
                f'{path} omits the WHEEL metadata file.',
            )
        return

    if lower.endswith(('.tar.gz', '.tgz', '.tar')):
        with tarfile.open(path, mode='r:*') as archive:
            entries = []
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                content = None
                pure = PurePosixPath(member.name)
                if (
                    pure.suffix.lower() in TEXT_SUFFIXES
                    or pure.name in {'METADATA', 'PKG-INFO', 'WHEEL', 'RECORD'}
                    or pure.name in REQUIRED_NOTICE_BASENAMES
                ):
                    extracted = archive.extractfile(member)
                    content = extracted.read() if extracted is not None else b''
                entries.append((member.name, content))
        _verify_entries(entries, source=str(path))
        pkg_info = [
            content
            for name, content in entries
            if PurePosixPath(name).name == 'PKG-INFO' and content is not None
        ]
        _require(pkg_info, f'{path} omits PKG-INFO.')
        chaos_pkg_info = [
            item for item in pkg_info
            if canonical_name(
                Parser().parsestr(
                    item.decode('utf-8', errors='replace')
                ).get('Name', '')
            ) == 'chaos-toolbox'
        ]
        _require(
            chaos_pkg_info,
            f'{path} PKG-INFO does not identify chaos-toolbox.',
        )
        for content in chaos_pkg_info:
            _verify_pep639_metadata(content, source=f'{path}:PKG-INFO')
        _require(
            any(PurePosixPath(name).name == 'pyproject.toml' for name, _ in entries),
            f'{path} omits pyproject.toml.',
        )
        return

    raise ComplianceError(
        f'Artifact format cannot be inspected directly: {path}. '
        'Validate the unpacked PyInstaller bundle before wrapping it in an installer.'
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _bundle_distribution_components(bundle: Path) -> list[dict]:
    components: dict[tuple[str, str], dict] = {}
    for metadata_path in bundle.rglob('METADATA'):
        if not metadata_path.parent.name.lower().endswith('.dist-info'):
            continue
        parsed = Parser().parsestr(
            metadata_path.read_text(encoding='utf-8', errors='replace')
        )
        name = parsed.get('Name')
        version = parsed.get('Version')
        if not name or not version:
            continue
        canonical = canonical_name(name)
        components[(canonical, version)] = {
            'type': 'library',
            'bom-ref': f'pkg:pypi/{canonical}@{version}',
            'name': name,
            'version': version,
            'purl': f'pkg:pypi/{canonical}@{version}',
        }
    return [components[key] for key in sorted(components)]


def write_bundle_sbom(bundle: Path, output: Path) -> None:
    bundle = bundle.resolve()
    _require(bundle.is_dir(), f'Bundle directory does not exist: {bundle}')
    verify_artifact(bundle)

    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))[
        'project'
    ]
    application = {
        'type': 'application',
        'bom-ref': f"pkg:pypi/chaos-toolbox@{project['version']}",
        'name': project['name'],
        'version': project['version'],
        'purl': f"pkg:pypi/chaos-toolbox@{project['version']}",
    }
    components = [
        component
        for component in _bundle_distribution_components(bundle)
        if canonical_name(component.get('name', '')) != 'chaos-toolbox'
    ]
    components.append(
        {
            'type': 'framework',
            'bom-ref': f'pkg:generic/python@{platform.python_version()}',
            'name': 'Python',
            'version': platform.python_version(),
            'purl': f'pkg:generic/python@{platform.python_version()}',
        }
    )

    for item in sorted(
        (candidate for candidate in bundle.rglob('*') if candidate.is_file()),
        key=lambda candidate: candidate.relative_to(bundle).as_posix(),
    ):
        relative = item.relative_to(bundle).as_posix()
        sha256 = _sha256_file(item)
        components.append(
            {
                'type': 'file',
                'bom-ref': f'file:sha256:{sha256}:{relative}',
                'name': relative,
                'hashes': [{'alg': 'SHA-256', 'content': sha256}],
                'properties': [
                    {'name': 'toolbox:relative-path', 'value': relative}
                ],
            }
        )

    payload = {
        '$schema': 'https://cyclonedx.org/schema/bom-1.6.schema.json',
        'bomFormat': 'CycloneDX',
        'specVersion': '1.6',
        'version': 1,
        'metadata': {
            'component': application,
            'properties': [
                {'name': 'toolbox:platform', 'value': sys.platform},
                {'name': 'toolbox:machine', 'value': platform.machine()},
            ],
        },
        'components': components,
    }
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
        newline='\n',
    )
    verify_sbom(output, bundle=bundle)


def verify_sbom(path: Path, *, bundle: Path | None = None) -> None:
    payload = json.loads(path.read_text(encoding='utf-8'))
    _require(payload.get('bomFormat') == 'CycloneDX', f'{path} is not a CycloneDX BOM.')
    _require(payload.get('specVersion') in {'1.6', '1.7'}, f'{path} uses an unsupported CycloneDX version.')

    components = list(payload.get('components', []))
    main_component = payload.get('metadata', {}).get('component')
    if isinstance(main_component, dict):
        components.append(main_component)
    seen_refs: set[str] = set()
    duplicate_refs: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            continue
        bom_ref = component.get('bom-ref')
        if not isinstance(bom_ref, str) or not bom_ref:
            continue
        if bom_ref in seen_refs:
            duplicate_refs.add(bom_ref)
        seen_refs.add(bom_ref)
    _require(
        not duplicate_refs,
        f'Duplicate bom-ref values in {path}: {sorted(duplicate_refs)}',
    )
    names = {
        canonical_name(component.get('name', ''))
        for component in components
        if isinstance(component, dict) and component.get('name')
    }
    legacy = sorted(name for name in names if _is_legacy_distribution(name))
    _require(not legacy, f'Legacy Qt components found in SBOM: {legacy}')
    required = {'chaos-toolbox', 'pyside6-essentials', 'pyside6-addons', 'shiboken6'}
    if bundle is not None:
        required |= _runtime_metadata_versions().keys()
    missing = sorted(required - names)
    _require(not missing, f'SBOM omits required runtime components: {missing}')

    if bundle is None:
        return

    bundle = bundle.resolve()
    recorded: dict[str, str] = {}
    for component in components:
        if not isinstance(component, dict) or component.get('type') != 'file':
            continue
        properties = {
            item.get('name'): item.get('value')
            for item in component.get('properties', [])
            if isinstance(item, dict)
        }
        relative = properties.get('toolbox:relative-path')
        hashes = {
            item.get('alg'): item.get('content')
            for item in component.get('hashes', [])
            if isinstance(item, dict)
        }
        if relative and hashes.get('SHA-256'):
            recorded[relative] = hashes['SHA-256']

    actual = {
        item.relative_to(bundle).as_posix(): _sha256_file(item)
        for item in bundle.rglob('*')
        if item.is_file()
    }
    _require(
        recorded.keys() == actual.keys(),
        'Bundle SBOM file inventory differs from the packaged bundle: '
        f"missing={sorted(actual.keys() - recorded.keys())[:10]}, "
        f"extra={sorted(recorded.keys() - actual.keys())[:10]}",
    )
    altered = sorted(
        relative
        for relative, digest in actual.items()
        if recorded.get(relative) != digest
    )
    _require(not altered, f'Bundle SBOM hashes differ for files: {altered[:10]}')

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Verify PySide6 distribution, notices, artifacts, and CycloneDX SBOM.'
    )
    parser.add_argument('--check-installed', action='store_true')
    parser.add_argument('--check-release-pins', action='store_true')
    parser.add_argument('--check-build-pins', action='store_true')
    parser.add_argument('--require-webengine', action='store_true')
    parser.add_argument('--artifact', action='append', type=Path, default=[])
    parser.add_argument('--sbom', action='append', type=Path, default=[])
    parser.add_argument(
        '--write-bundle-sbom',
        action='append',
        nargs=2,
        metavar=('BUNDLE', 'OUTPUT'),
        default=[],
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        verify_source_contract()
        if args.check_installed:
            verify_installed_environment(require_webengine=args.require_webengine)
        if args.check_release_pins:
            verify_installed_release_pins()
        if args.check_build_pins:
            verify_installed_build_pins()
        for artifact in args.artifact:
            verify_artifact(artifact)
        for bundle_value, output_value in args.write_bundle_sbom:
            write_bundle_sbom(Path(bundle_value), Path(output_value))
        for sbom in args.sbom:
            verify_sbom(sbom)
    except (ComplianceError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'DISTRIBUTION COMPLIANCE FAILED: {exc}')
        return 1
    print('Distribution compliance OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
