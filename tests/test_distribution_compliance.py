from __future__ import annotations

import io
import json
from pathlib import Path
import tarfile
import zipfile

import pytest

import scripts.verify_distribution_compliance as compliance
from scripts.normalize_python_sdist import (
    SdistNormalizationError,
    normalize_sdist,
)
from scripts.verify_distribution_compliance import (
    ComplianceError,
    REQUIRED_NOTICE_BASENAMES,
    _notice_source_paths,
    verify_artifact,
    verify_installed_build_pins,
    verify_installed_release_pins,
    verify_sbom,
    verify_source_contract,
    write_bundle_sbom,
)


ROOT = Path(__file__).resolve().parents[1]


def test_source_distribution_contract_is_pyside6_only():
    verify_source_contract()
    constraints = (ROOT / 'requirements-release.txt').read_text(encoding='utf-8')
    assert 'PySide6-Essentials==6.11.1' in constraints
    assert 'PySide6-Addons==6.11.1' in constraints
    assert 'shiboken6==6.11.1' in constraints
    assert 'hidden-attractors-fo==1.2.0' in constraints
    for requirement in (
        'numpy==2.5.2',
        'scipy==1.18.0',
        'numba==0.67.0',
        'llvmlite==0.49.0',
        'matplotlib==3.11.1',
        'pyqtgraph==0.14.0',
        'PyYAML==6.0.3',
        'Pillow==12.3.0',
        'packaging==26.3',
    ):
        assert requirement in constraints
    assert 'PyInstaller==6.22.0' in constraints
    assert 'pyinstaller-hooks-contrib==2026.6' in constraints
    for requirement in (
        'build==1.4.0',
        'setuptools==84.0.0',
        'wheel==0.46.3',
        'twine==6.2.0',
        'cyclonedx-bom==7.3.1',
    ):
        assert requirement in constraints
    bootstrap = (ROOT / 'requirements-bootstrap.txt').read_text(encoding='utf-8')
    assert bootstrap.splitlines()[-1] == 'pip==26.2.1'
    requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    assert 'PySide6-Addons>=6.7' in requirements
    assert 'Pillow>=10' in requirements


def test_pyinstaller_and_inno_include_required_notices_and_metadata():
    spec = (ROOT / 'packaging' / 'pyinstaller' / 'chaos_toolbox.spec').read_text(
        encoding='utf-8'
    )
    for name in REQUIRED_NOTICE_BASENAMES:
        assert name in spec
    for distribution in (
        'chaos-toolbox',
        'hidden-attractors-fo',
        'PySide6-Addons',
        'pyinstaller',
    ):
        assert repr(distribution) in spec
    assert "copy_metadata('chaos-toolbox', recursive=True)" in spec
    assert "copy_metadata('hidden-attractors-fo', recursive=True)" in spec
    assert "copy_metadata('PySide6-Addons', recursive=True)" in spec
    assert "collect_all('hidden_attractors')" not in spec
    assert "collect_data_files('hidden_attractors')" in spec
    assert 'include_py_files=True' not in spec
    assert "Path(source).suffix.lower() not in {'.nbc', '.nbi', '.pyc'}" in spec
    assert "'__pycache__' not in Path(source).parts" in spec
    assert "hookspath=[str(ROOT / 'packaging' / 'pyinstaller' / 'hooks')]" in spec
    assert 'hidden_attractors.validation' not in spec
    assert "'PySide6.QtSvgWidgets'" in spec
    assert "'PySide6.QtCore5Compat'" in spec
    assert "'PySide6.QtXml'" in spec
    assert "'pyqtgraph.opengl'" in spec
    assert "'numba.np.ufunc.tbbpool'" in spec
    assert "'PyQt" + "6'" in spec
    assert 'Path(sys.base_prefix)' in spec
    assert "'LICENSES/Python'" in spec
    assert 'upx=False' in spec
    assert 'upx=True' not in spec
    assert 'PYQTGRAPH_BINDING_STUB' in spec
    assert 'EXCLUDED_QT_DEBUG_RESOURCE' in spec
    assert 'EXCLUDED_GPL_ONLY_QT_COMPONENT' in spec
    assert "validate_precompiled_library(native_library)" in spec
    for module in (
        'hidden_attractors.systems',
        'hidden_attractors.simulation',
        'hidden_attractors.analysis.spectral',
        'hidden_attractors.analysis.correlation_dimension',
        'hidden_attractors.analysis.permutation_entropy',
        'hidden_attractors.fractional.grunwald_letnikov',
        'hidden_attractors.fractional.multi_term_caputo',
        'hidden_attractors.fractional.tempered_convolution_quadrature',
        'hidden_attractors.fractional.tempered_fast_history',
    ):
        assert repr(module) in spec
    assert 'REQUIRED_HAFO_SOURCE_MODULES' in spec
    assert 'unexpected_hafo_pyz_modules' in spec
    assert 'HAFO modules must not be stored in the PyInstaller PYZ' in spec
    assert 'missing_hafo_python_sources' in spec
    assert 'HAFO external source collection gate OK' in spec
    assert 'HAFO wheel RECORD hash gate OK' in spec
    assert 'unexpected_hafo_cache_artifacts' in spec
    assert "{'direct_url.json', 'record'}" in spec
    assert 'Sanitized frozen metadata' in spec
    assert 'local direct_url metadata survived bundle sanitization' in spec

    hook = (
        ROOT / 'packaging' / 'pyinstaller' / 'hooks' / 'hook-hidden_attractors.py'
    ).read_text(encoding='utf-8')
    assert 'module_collection_mode = {"hidden_attractors": "py"}' in hook

    inno = (ROOT / 'packaging' / 'windows' / 'ChaosToolbox.iss').read_text(
        encoding='utf-8'
    )
    assert 'InfoBeforeFile=..\\..\\THIRD_PARTY_NOTICES.md' in inno
    assert 'recursesubdirs' in inno
    assert '[InstallDelete]' in inno
    assert 'Type: filesandordirs; Name: "{app}\\_internal"' in inno


def _valid_sbom() -> dict:
    return {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.6',
        'metadata': {
            'component': {
                'type': 'application',
                'name': 'chaos-toolbox',
                'version': '0.1.0',
            }
        },
        'components': [
            {'type': 'library', 'name': 'PySide6_Essentials', 'version': '6.11.1'},
            {'type': 'library', 'name': 'PySide6_Addons', 'version': '6.11.1'},
            {'type': 'library', 'name': 'shiboken6', 'version': '6.11.1'},
        ],
    }


def test_sbom_requires_pyside6_components_and_rejects_legacy_binding(tmp_path):
    path = tmp_path / 'runtime.cdx.json'
    payload = _valid_sbom()
    path.write_text(json.dumps(payload), encoding='utf-8')
    verify_sbom(path)

    payload['components'].append(
        {'type': 'library', 'name': 'PyQt' + '6', 'version': '6.9.1'}
    )
    path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(ComplianceError, match='Legacy Qt'):
        verify_sbom(path)


def test_archive_requires_real_metadata_exact_notices_and_rejects_legacy_import(
    tmp_path,
):
    archive = tmp_path / 'sample.whl'
    with zipfile.ZipFile(archive, 'w') as handle:
        for name, source in _notice_source_paths().items():
            handle.writestr(f'share/chaos-toolbox/{name}', source.read_bytes())
        handle.writestr(
            'chaos_toolbox-0.1.0.dist-info/METADATA',
            'Metadata-Version: 2.4\nName: chaos-toolbox\nVersion: 0.1.0\n',
        )
        handle.writestr(
            'chaos_toolbox-0.1.0.dist-info/WHEEL',
            'Wheel-Version: 1.0\nGenerator: regression-test\nRoot-Is-Purelib: false\n',
        )
        handle.writestr(
            'sample/module.py',
            'from ' + 'PyQt' + '6.QtCore import QObject\n',
        )
    with pytest.raises(ComplianceError, match='Legacy Qt'):
        verify_artifact(archive)


def test_archive_rejects_notice_with_only_the_right_filename(tmp_path):
    archive = tmp_path / 'sample.whl'
    with zipfile.ZipFile(archive, 'w') as handle:
        for name, source in _notice_source_paths().items():
            content = source.read_bytes()
            if name == 'NOTICE.md':
                content = b'not the source notice'
            handle.writestr(f'share/chaos-toolbox/{name}', content)
        handle.writestr(
            'chaos_toolbox-0.1.0.dist-info/METADATA',
            'Metadata-Version: 2.4\nName: chaos-toolbox\nVersion: 0.1.0\n',
        )
        handle.writestr(
            'chaos_toolbox-0.1.0.dist-info/WHEEL',
            'Wheel-Version: 1.0\n',
        )
    with pytest.raises(ComplianceError, match='exact source notice NOTICE.md'):
        verify_artifact(archive)


def test_artifact_rejects_local_installation_provenance(tmp_path):
    bundle = tmp_path / 'bundle'
    direct_url = bundle / 'sample-1.0.dist-info' / 'direct_url.json'
    direct_url.parent.mkdir(parents=True)
    direct_url.write_text(
        (
            '{"url":"file:'
            + '///'
            + 'C:'
            + '/'
            + 'Users/example/private/package.whl"}'
        ),
        encoding='utf-8',
    )

    with pytest.raises(ComplianceError, match='local installation provenance'):
        verify_artifact(bundle)


def test_artifact_rejects_record_for_omitted_local_provenance(tmp_path):
    bundle = tmp_path / 'bundle'
    record = bundle / 'sample-1.0.dist-info' / 'RECORD'
    record.parent.mkdir(parents=True)
    record.write_text(
        'sample-1.0.dist-info/direct_url.json,sha256=abc,12\n',
        encoding='utf-8',
    )

    with pytest.raises(
        ComplianceError,
        match='RECORD metadata for omitted local provenance',
    ):
        verify_artifact(bundle)


def test_release_workflow_generates_and_retains_validated_sbom():
    workflow = (ROOT / '.github' / 'workflows' / 'release.yml').read_text(
        encoding='utf-8'
    )
    assert (
        'python -m pip install -c requirements-release.txt build setuptools '
        'wheel twine cyclonedx-bom'
    ) in workflow
    assert 'SOURCE_DATE_EPOCH=%s\\n' in workflow
    assert 'git log -1 --pretty=%ct' in workflow
    assert workflow.count(
        'python -m build --no-isolation --sdist --wheel'
    ) == 2
    assert workflow.count('python scripts/normalize_python_sdist.py') == 2
    assert 'cmp -- "$artifact" "$counterpart"' in workflow
    assert 'python -m cyclonedx_py environment' in workflow
    assert '--output-reproducible' in workflow
    assert '--spec-version 1.6' in workflow
    assert '--sbom "$sbom"' in workflow
    assert '--write-bundle-sbom' in workflow or '--write-bundle-sbom' in (ROOT / 'scripts' / 'build_linux.sh').read_text(encoding='utf-8')
    assert 'python-environment.cdx.json' in workflow
    assert 'hdiutil attach -nobrowse -readonly' in workflow
    assert 'Start-Process -FilePath $installer' in workflow
    assert 'Qt-PySide-6.11.1-Corresponding-Source.txt' in workflow
    assert 'Qt-6.11.1-Security-Inventory.txt' in workflow
    assert 'qt-everywhere-src-6.11.1.tar.xz' in workflow
    assert 'pyside-setup-everywhere-src-6.11.1.tar.xz' in workflow
    assert 'compression-level: 0' in workflow
    assert 'ubuntu:24.04 bash -euo pipefail' in workflow
    assert 'linux-deb-self-test.json' in workflow
    assert '--check-build-pins' in workflow
    assert 'dist/python/*.cdx.json' in workflow
    assert workflow.count('retention-days: 90') >= 2
    assert workflow.count('python-version: "3.14.6"') == 4


def test_sdist_normalization_is_byte_reproducible(tmp_path):
    source_payload = {
        'chaos_toolbox-0.1.0/PKG-INFO': b'Name: chaos-toolbox\n',
        'chaos_toolbox-0.1.0/core/module.py': b'VALUE = 1\n',
    }
    outputs = []
    for index, archive_mtime in enumerate((1_700_000_001, 1_800_000_002)):
        archive = tmp_path / f'build-{index}.tar.gz'
        with tarfile.open(archive, mode='w:gz') as handle:
            for name, payload in source_payload.items():
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                member.mtime = archive_mtime
                handle.addfile(member, fileobj=io.BytesIO(payload))
        normalize_sdist(archive, epoch=1_785_796_570)
        outputs.append(archive.read_bytes())

        with tarfile.open(archive, mode='r:gz') as handle:
            assert all(member.mtime == 1_785_796_570 for member in handle)

    assert outputs[0] == outputs[1]


@pytest.mark.parametrize('member_type', (tarfile.SYMTYPE, tarfile.LNKTYPE))
def test_sdist_normalization_rejects_links(tmp_path, member_type):
    archive = tmp_path / 'linked-source.tar.gz'
    with tarfile.open(archive, mode='w:gz') as handle:
        member = tarfile.TarInfo('chaos_toolbox-0.1.0/unsafe-link')
        member.type = member_type
        member.linkname = '../../outside'
        handle.addfile(member)

    with pytest.raises(SdistNormalizationError, match='Unsupported sdist member'):
        normalize_sdist(archive, epoch=1_785_796_570)


def test_ci_checks_real_pyside6_distribution_names():
    workflow = (ROOT / '.github' / 'workflows' / 'ci.yml').read_text(
        encoding='utf-8'
    )
    assert '"PySide6-Essentials": (6, 7)' in workflow
    assert 'verify_distribution_compliance.py --check-installed' in workflow
    assert '.[test,webengine]' in workflow
    assert workflow.count('requirements-bootstrap.txt') >= 4


def test_build_pin_gate_rejects_installed_version_drift(monkeypatch):
    versions = {
        'pyinstaller': '6.22.0',
        'pyinstaller-hooks-contrib': '2026.5',
    }
    monkeypatch.setattr(
        compliance.metadata,
        'version',
        lambda name: versions[compliance.canonical_name(name)],
    )
    with pytest.raises(ComplianceError, match='build tools do not match'):
        verify_installed_build_pins()


def test_release_pin_gate_rejects_installed_version_drift(monkeypatch):
    versions = compliance._release_pin_versions()
    versions['pip'] = '26.2.1'
    versions['pyside6-addons'] = '6.11.2'

    monkeypatch.setattr(
        compliance.metadata,
        'version',
        lambda name: versions[compliance.canonical_name(name)],
    )
    with pytest.raises(ComplianceError, match='do not match release pins'):
        verify_installed_release_pins()


def test_bundle_sbom_hashes_every_packaged_file(tmp_path, monkeypatch):
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    for name, source in _notice_source_paths().items():
        destination = bundle / 'LICENSES' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())

    python_license = bundle / 'LICENSES' / 'Python' / 'LICENSE.txt'
    python_license.parent.mkdir(parents=True)
    python_license.write_text(
        'PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2\n',
        encoding='utf-8',
    )
    (bundle / 'qtwebengine_resources.pak').write_bytes(b'credits-resource')

    distributions = {
        'chaos_toolbox': 'chaos-toolbox',
        'hidden_attractors_fo': 'hidden-attractors-fo',
        'pyside6_essentials': 'PySide6-Essentials',
        'pyside6_addons': 'PySide6-Addons',
        'shiboken6': 'shiboken6',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'pyqtgraph': 'pyqtgraph',
        'pyyaml': 'PyYAML',
        'packaging': 'packaging',
        'pyinstaller': 'pyinstaller',
    }
    for directory_name, distribution_name in distributions.items():
        dist_info = bundle / f'{directory_name}-1.0.dist-info'
        dist_info.mkdir()
        metadata = (
            f'Metadata-Version: 2.4\n'
            f'Name: {distribution_name}\n'
            'Version: 1.0\n'
        )
        if distribution_name == 'chaos-toolbox':
            metadata += 'License-Expression: MIT\n'
            metadata += ''.join(
                f'License-File: {license_path}\n'
                for license_path in sorted(compliance.PEP639_LICENSE_FILES)
            )
        (dist_info / 'METADATA').write_text(
            metadata,
            encoding='utf-8',
        )
    monkeypatch.setattr(
        compliance,
        '_runtime_metadata_versions',
        lambda: {
            compliance.canonical_name(name): '1.0'
            for name in distributions.values()
        },
    )

    sbom = tmp_path / 'bundle.cdx.json'
    write_bundle_sbom(bundle, sbom)
    verify_sbom(sbom, bundle=bundle)

    (bundle / 'qtwebengine_resources.pak').write_bytes(b'changed')
    with pytest.raises(ComplianceError, match='hashes differ'):
        verify_sbom(sbom, bundle=bundle)


def test_optional_qt_artifact_filter_keeps_qtsvg_but_rejects_unused_surfaces():
    pattern = compliance.EXCLUDED_OPTIONAL_QT_COMPONENT
    assert pattern.search('PySide6/QtSvgWidgets.pyd')
    assert pattern.search('PySide6/QtCore5Compat.pyd')
    assert pattern.search('PySide6/QtXml.pyd')
    assert pattern.search('PySide6/Qt/lib/Qt6Core5Compat.dll')
    assert pattern.search('PySide6/Qt/qml/Qt5Compat/plugin.dll')
    assert not pattern.search('PySide6/QtSvg.pyd')
    assert not pattern.search('PySide6/Qt/lib/Qt6Svg.dll')


@pytest.mark.parametrize(
    'path',
    [
        'PySide6/Qt6Graphs.dll',
        'PySide6/Qt6Charts.dll',
        'PySide6/Qt6ChartsQml.dll',
        'PySide6/Qt6DataVisualization.dll',
        'PySide6/Qt6DataVisualizationQml.dll',
        'PySide6/Qt6Quick3D.dll',
        'PySide6/Qt6Quick3DRuntimeRender.dll',
        'PySide6/Qt6QuickTimeline.dll',
        'PySide6/Qt6QuickTimelineBlendTrees.dll',
        'PySide6/Qt6VirtualKeyboard.dll',
        'PySide6/Qt6VirtualKeyboardSettings.dll',
        'PySide6/qml/QtGraphs/graphsplugin.dll',
        'PySide6/qml/QtCharts/qtchartsqml2.dll',
        'PySide6/qml/QtDataVisualization/datavisualizationqml2.dll',
        'PySide6/qml/QtQuick3D/qquick3dplugin.dll',
        'PySide6/qml/QtQuick/Timeline/qtquicktimelineplugin.dll',
        'PySide6/qml/QtQuick/VirtualKeyboard/qtvkbplugin.dll',
    ],
)
def test_gpl_only_qt_modules_are_excluded_from_binary_release(path):
    assert compliance.EXCLUDED_GPL_ONLY_QT_COMPONENT.search(path)


def test_required_lgpl_qt_surfaces_are_not_overexcluded():
    pattern = compliance.EXCLUDED_GPL_ONLY_QT_COMPONENT
    for path in (
        'PySide6/Qt6Core.dll',
        'PySide6/Qt6Svg.dll',
        'PySide6/Qt6Quick.dll',
        'PySide6/Qt6Qml.dll',
        'PySide6/Qt6WebEngineCore.dll',
    ):
        assert not pattern.search(path)
