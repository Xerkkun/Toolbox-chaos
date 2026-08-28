# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from importlib.util import find_spec
import importlib.metadata as package_metadata
import base64
import hashlib
import re

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata


ROOT = Path(SPECPATH).resolve().parents[1]

EXCLUDED_OPTIONAL_QT_COMPONENT = re.compile(
    r'(^|/)(?:lib)?qt6?(?:svgwidgets|core5compat|xml)(?:[./]|$)|'
    r'(^|/)qml/qt5compat(?:/|$)',
    re.IGNORECASE,
)
PYQTGRAPH_BINDING_STUB = re.compile(
    r'(^|/)pyqtgraph/qt(?:/.*)?\.pyi$',
    re.IGNORECASE,
)
EXCLUDED_QT_DEBUG_RESOURCE = re.compile(
    r'(^|/)pyside6/resources/[^/]+[.]debug[.](?:pak|bin)$',
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

# Pre-build verification to ensure no Sprott original files are packaged
import sys
BANNED_FILES = {
    'BOOKFIGS.DIC', 'SELECTED.DIC', 'SPECIAL.DIC',
    'SADISK.ZIP', 'SA.EXE', 'SAWIN.EXE',
    'PROG28.BAS', 'PROG28QC.C', 'PROG28TC.CPP',
    'VBRUN200.DLL'
}
IGNORED_DIRS = {
    'external', '.git', '.venv', '.venv-build',
    '.venv-webengine', '__pycache__', '.pytest_cache',
    '.pytest_tmp', 'build'
}
found_banned = []
for path in ROOT.rglob('*'):
    if path.is_dir():
        continue
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        continue
    if any(p in IGNORED_DIRS for p in relative.parts[:-1]):
        continue
    if path.name.upper() in BANNED_FILES:
        found_banned.append(path)

if found_banned:
    print("CRITICAL: Found Sprott original files in the release path or repo root during PyInstaller build:")
    for fb in found_banned:
        print(f"  - {fb}")
    print("Aborting build. Please remove these files.")
    sys.exit(1)

from core.app_metadata import APP_VERSION

runtime_resources = ROOT / 'resources' / 'bundled'
if not runtime_resources.exists():
    print("CRITICAL: resources/bundled does not exist. Run scripts/prepare_runtime_resources.py before PyInstaller.")
    sys.exit(1)

if sys.platform.startswith('win'):
    native_library = ROOT / 'core' / 'bin' / 'chaos_core.dll'
elif sys.platform == 'darwin':
    native_library = ROOT / 'core' / 'bin' / 'libchaos_core.dylib'
else:
    native_library = ROOT / 'core' / 'bin' / 'libchaos_core.so'

if not native_library.exists():
    print(f"CRITICAL: Native backend is missing for {sys.platform}: {native_library}")
    print("Compile the platform library before running PyInstaller.")
    sys.exit(1)

from core.native import NativeChaosError, validate_precompiled_library

try:
    validate_precompiled_library(native_library)
except (NativeChaosError, OSError) as exc:
    print(f"CRITICAL: Native backend failed its ABI/export contract: {exc}")
    sys.exit(1)

binaries = [(str(native_library), 'core/bin')]

reviewed_python_license = ROOT / 'LICENSES' / 'Python' / 'LICENSE.txt'
python_license = next(
    (candidate for candidate in (
        Path(sys.base_prefix) / 'LICENSE.txt',
        Path(sys.base_prefix) / 'LICENSE',
        Path(sys.prefix) / 'LICENSE.txt',
        Path(sys.prefix) / 'LICENSE',
        reviewed_python_license,
    ) if candidate.is_file()),
    None,
)
if python_license is None:
    print(
        'CRITICAL: Python runtime license not found under the interpreter '
        'or in the reviewed CPython fallback.'
    )
    sys.exit(1)
if (
    python_license == reviewed_python_license
    and hashlib.sha256(python_license.read_bytes()).hexdigest()
    != 'b0e25a78cffb43f4d92de8b61ccfa1f1f98ecbc22330b54b5251e7b6ba010231'
):
    print('CRITICAL: Reviewed CPython 3.14.6 license hash mismatch.')
    sys.exit(1)

# HAFO's Numba ``cache=True`` dispatchers require physical modules instead of
# PYZ bytecode.  The focal hook selects PyInstaller's documented ``py`` module
# collection mode; this data list retains only non-Python package resources.
hafo_datas = [
    (source, destination)
    for source, destination in collect_data_files('hidden_attractors')
    if Path(source).suffix.lower() not in {'.nbc', '.nbi', '.pyc'}
    and '__pycache__' not in Path(source).parts
]
hafo_binaries = collect_dynamic_libs('hidden_attractors')
REQUIRED_HAFO_SOURCE_MODULES = (
    'hidden_attractors',
    'hidden_attractors.capabilities',
    'hidden_attractors.systems',
    'hidden_attractors.simulation',
    'hidden_attractors.analysis',
    'hidden_attractors.analysis.alignment_indices',
    'hidden_attractors.analysis.covariant_lyapunov',
    'hidden_attractors.analysis.spectral',
    'hidden_attractors.analysis.correlation_dimension',
    'hidden_attractors.analysis.permutation_entropy',
    'hidden_attractors.integrations.numba_kernels',
    'hidden_attractors.fractional',
    'hidden_attractors.fractional.convolution_quadrature',
    'hidden_attractors.fractional.grunwald_letnikov',
    'hidden_attractors.fractional.multi_term_caputo',
    'hidden_attractors.fractional.tempered_convolution_quadrature',
    'hidden_attractors.fractional.tempered_fast_history',
)
hafo_hiddenimports = list(REQUIRED_HAFO_SOURCE_MODULES)

# Fail closed if the installed HAFO package differs from its wheel RECORD.
hafo_distribution = package_metadata.distribution('hidden-attractors-fo')
if hafo_distribution.version != '1.2.0':
    print(
        'CRITICAL: frozen HAFO must be the reviewed 1.2.0 distribution, got '
        + hafo_distribution.version
    )
    sys.exit(1)
hafo_record_mismatches = []
hafo_record_checked = 0
recorded_hafo_paths = set()
for package_path in hafo_distribution.files or ():
    relative_path = str(package_path).replace('\\', '/')
    if relative_path.startswith('hidden_attractors/'):
        recorded_hafo_paths.add(relative_path)
    recorded_hash = package_path.hash
    if not relative_path.startswith('hidden_attractors/') or recorded_hash is None:
        continue
    if recorded_hash.mode != 'sha256':
        hafo_record_mismatches.append(relative_path + ':unsupported-hash')
        continue
    installed_path = Path(package_path.locate())
    if not installed_path.is_file():
        hafo_record_mismatches.append(relative_path + ':missing')
        continue
    actual_hash = base64.urlsafe_b64encode(
        hashlib.sha256(installed_path.read_bytes()).digest()
    ).rstrip(b'=').decode('ascii')
    hafo_record_checked += 1
    if actual_hash != recorded_hash.value:
        hafo_record_mismatches.append(relative_path + ':hash')
hafo_package_root = Path(hafo_distribution.locate_file('hidden_attractors'))
unrecorded_hafo_files = []
for installed_path in hafo_package_root.rglob('*'):
    if not installed_path.is_file():
        continue
    relative_parts = installed_path.relative_to(hafo_package_root).parts
    if (
        '__pycache__' in relative_parts
        or installed_path.suffix.lower() in {'.nbc', '.nbi', '.pyc'}
    ):
        continue
    relative_path = (
        Path('hidden_attractors')
        .joinpath(*relative_parts)
        .as_posix()
    )
    if relative_path not in recorded_hafo_paths:
        unrecorded_hafo_files.append(relative_path)
hafo_record_mismatches.extend(
    path + ':unrecorded' for path in sorted(unrecorded_hafo_files)
)
if hafo_record_mismatches or not hafo_record_checked:
    print(
        'CRITICAL: installed HAFO differs from wheel RECORD: '
        + ', '.join(hafo_record_mismatches or ['no hashed package files'])
    )
    sys.exit(1)
print(f'HAFO wheel RECORD hash gate OK: {hafo_record_checked} files')
binaries += hafo_binaries

datas = [
    (str(runtime_resources), 'resources/bundled'),
    (str(ROOT / 'pyproject.toml'), '.'),
    (str(ROOT / 'LICENSE'), '.'),
    (str(ROOT / 'NOTICE.md'), '.'),
    (str(ROOT / 'THIRD_PARTY_NOTICES.md'), '.'),
    (str(ROOT / 'LICENSES' / 'LGPL-3.0-only.txt'), 'LICENSES'),
    (str(ROOT / 'LICENSES' / 'GPL-3.0-only.txt'), 'LICENSES'),
    (str(ROOT / 'LICENSES' / 'Chromium-BSD-3-Clause.txt'), 'LICENSES'),
    (str(ROOT / 'LICENSES' / 'QtWebEngine-Third-Party-NOTICE.txt'), 'LICENSES'),
    (str(ROOT / 'LICENSES' / 'Qt-PySide-6.11.1-Corresponding-Source.txt'), 'LICENSES'),
    (str(ROOT / 'LICENSES' / 'Qt-6.11.1-Security-Inventory.txt'), 'LICENSES'),
    (str(python_license), 'LICENSES/Python'),
    (str(ROOT / 'AUTHORS.md'), '.'),
    (str(ROOT / 'RELEASE_NOTES.md'), '.'),
    (str(ROOT / 'packaging' / 'linux' / 'chaos-toolbox.desktop'), '.'),
    (str(ROOT / 'core' / 'csrc' / 'system_ids.def'), 'core/csrc'),
    (str(ROOT / 'docs' / 'installation.md'), 'docs'),
    (str(ROOT / 'docs' / 'user-guide.md'), 'docs'),
    (str(ROOT / 'docs' / 'troubleshooting.md'), 'docs'),
    (str(ROOT / 'docs' / 'license.md'), 'docs'),
    (str(ROOT / 'docs' / 'custom_systems.md'), 'docs'),
]
datas += hafo_datas
try:
    metadata_datas = []
    metadata_datas += copy_metadata('chaos-toolbox', recursive=True)
    metadata_datas += copy_metadata('hidden-attractors-fo', recursive=True)
    metadata_datas += copy_metadata('PySide6-Addons', recursive=True)
    metadata_datas += copy_metadata('pyinstaller')
except package_metadata.PackageNotFoundError as exc:
    print(
        'CRITICAL: build metadata is incomplete. Install the project and '
        'its build/WebEngine extras before running PyInstaller.'
    )
    raise SystemExit(1) from exc
seen_metadata = set()
omitted_local_metadata = []
for metadata_source, metadata_destination in metadata_datas:
    metadata_source = Path(metadata_source)
    metadata_destination = Path(metadata_destination)
    metadata_files = (
        sorted(path for path in metadata_source.rglob('*') if path.is_file())
        if metadata_source.is_dir()
        else [metadata_source]
    )
    for metadata_file in metadata_files:
        # PEP 610 direct_url.json records the local build path.  RECORD would
        # then advertise a file intentionally omitted from the frozen bundle,
        # so both are replaced by the bundle SBOM/inventory.
        if metadata_file.name.lower() in {'direct_url.json', 'record'}:
            omitted_local_metadata.append(str(metadata_file))
            continue
        relative_parent = (
            metadata_file.relative_to(metadata_source).parent
            if metadata_source.is_dir()
            else Path('.')
        )
        destination = metadata_destination / relative_parent
        metadata_entry = (str(metadata_file), destination.as_posix())
        if metadata_entry in seen_metadata:
            continue
        seen_metadata.add(metadata_entry)
        datas.append(metadata_entry)
print(
    'Sanitized frozen metadata: omitted '
    f'{len(omitted_local_metadata)} local-provenance/RECORD files.'
)

hiddenimports = [
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    *hafo_hiddenimports,
]
if find_spec('PySide6.QtWebEngineWidgets') is not None:
    hiddenimports.extend([
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
    ])


a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(ROOT / 'packaging' / 'pyinstaller' / 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6',
        'PySide6.QtSvgWidgets',
        'PySide6.QtCore5Compat',
        'PySide6.QtXml',
        'pyqtgraph.opengl',
        'numba.np.ufunc.tbbpool',
        'pytest',
        'IPython',
        'jedi',
        'notebook',
        'OpenGL',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)

# HAFO exposes these APIs through importlib-based lazy exports, which static
# PyInstaller analysis cannot discover.  The focal hidden imports make them
# reachable, while the hook must keep every HAFO module out of PYZ and collect
# its source externally for Numba's cache locator.
pure_module_names = {str(entry[0]) for entry in a.pure}
unexpected_hafo_pyz_modules = sorted(
    name for name in pure_module_names
    if name == 'hidden_attractors' or name.startswith('hidden_attractors.')
)
if unexpected_hafo_pyz_modules:
    print(
        'CRITICAL: HAFO modules must not be stored in the PyInstaller PYZ: '
        + ', '.join(unexpected_hafo_pyz_modules)
    )
    sys.exit(1)

hafo_source_destinations = {
    str(entry[0]).replace('\\', '/')
    for entry in a.datas
    if str(entry[0]).replace('\\', '/').startswith('hidden_attractors/')
    and str(entry[0]).lower().endswith('.py')
}
missing_hafo_python_sources = []
for module_name in REQUIRED_HAFO_SOURCE_MODULES:
    module_path = module_name.replace('.', '/')
    source_candidates = {
        f'{module_path}.py',
        f'{module_path}/__init__.py',
    }
    if not source_candidates.intersection(hafo_source_destinations):
        missing_hafo_python_sources.append(module_name)
if missing_hafo_python_sources:
    print(
        'CRITICAL: external HAFO Python sources are missing: '
        + ', '.join(missing_hafo_python_sources)
    )
    sys.exit(1)

unexpected_hafo_cache_artifacts = sorted(
    str(entry[0]).replace('\\', '/')
    for entry in a.datas
    if str(entry[0]).replace('\\', '/').startswith('hidden_attractors/')
    and (
        Path(str(entry[0])).suffix.lower() in {'.nbc', '.nbi', '.pyc'}
        or '__pycache__' in Path(str(entry[0])).parts
    )
)
if unexpected_hafo_cache_artifacts:
    print(
        'CRITICAL: pre-existing HAFO cache artifacts were collected: '
        + ', '.join(unexpected_hafo_cache_artifacts)
    )
    sys.exit(1)
print(
    'HAFO external source collection gate OK: '
    + ', '.join(sorted(REQUIRED_HAFO_SOURCE_MODULES))
)

# Hooks may add distribution metadata after the explicit datas list has been
# expanded.  Remove local-install provenance and its now-invalid RECORD again
# at the final TOC boundary, then verify that no direct_url entry survived.
sanitized_analysis_datas = []
omitted_analysis_metadata = []
for toc_entry in a.datas:
    destination = str(toc_entry[0]).replace('\\', '/')
    basename = Path(destination).name.lower()
    if basename == 'direct_url.json' or (
        basename == 'record' and '.dist-info/' in destination.lower()
    ):
        omitted_analysis_metadata.append(destination)
        continue
    sanitized_analysis_datas.append(toc_entry)
a.datas = sanitized_analysis_datas
if any(
    Path(str(entry[0])).name.lower() == 'direct_url.json'
    for entry in a.datas
):
    print('CRITICAL: local direct_url metadata survived bundle sanitization.')
    sys.exit(1)
if omitted_analysis_metadata:
    print('Excluded local-provenance metadata from final Analysis TOC:')
    for destination in sorted(omitted_analysis_metadata):
        print(f'  - {destination}')

# These optional Qt surfaces are not used by the application. QtSvg itself,
# qsvg, and qsvgicon remain because Matplotlib QtAgg requires them. GPL-only Qt
# modules collected transitively by broad QML hooks are also removed: the
# application neither imports nor exposes them. Artifact verification is
# fail-closed if any of these surfaces reappear.
excluded_optional_qt = []
for toc_name in ('binaries', 'datas'):
    retained_entries = []
    for toc_entry in getattr(a, toc_name):
        destination = str(toc_entry[0]).replace('\\', '/')
        if (
            EXCLUDED_OPTIONAL_QT_COMPONENT.search(destination)
            or EXCLUDED_GPL_ONLY_QT_COMPONENT.search(destination)
            or PYQTGRAPH_BINDING_STUB.search(destination)
            or EXCLUDED_QT_DEBUG_RESOURCE.search(destination)
        ):
            excluded_optional_qt.append(destination)
        else:
            retained_entries.append(toc_entry)
    setattr(a, toc_name, retained_entries)
if excluded_optional_qt:
    print('Excluded unused optional Qt components:')
    for destination in sorted(excluded_optional_qt):
        print(f'  - {destination}')

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Chaos Toolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Chaos Toolbox',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Chaos Toolbox.app',
        bundle_identifier='org.fyskode.chaostoolbox',
        info_plist={
            'CFBundleDisplayName': 'Chaos Toolbox',
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': True,
        },
    )
