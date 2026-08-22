from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from threading import Event

import pytest

import core.update_checker as update_checker_module
from core.update_checker import (
    UpdateCheckError,
    UpdateDownloadError,
    UpdateInfo,
    check_for_updates,
    download_verified_update,
    parse_sha256_manifest,
    verify_update_before_launch,
)
from scripts.generate_release_checksums import (
    ReleaseChecksumError,
    discover_release_assets,
    write_sha256_manifest,
)


RELEASE_API_URL = (
    'https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest'
)
RELEASE_BASE_URL = (
    'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.2.0/'
)
INSTALLER_NAME = 'chaos-toolbox-v0.2.0-windows-x64-setup.exe'


def _release_payload(*, prerelease: bool = False, tag: str = 'v0.2.0') -> dict:
    return {
        'tag_name': tag,
        'draft': False,
        'prerelease': prerelease,
        'published_at': '2026-08-21T12:00:00Z',
        'html_url': 'https://github.com/Xerkkun/toolbox-chaos/releases/tag/v0.2.0',
        'body': 'Actualizador integrado y mejoras de interfaz.',
        'assets': [
            {
                'name': INSTALLER_NAME,
                'browser_download_url': RELEASE_BASE_URL + INSTALLER_NAME,
                'size': 1234,
            },
            {
                'name': 'SHA256SUMS',
                'browser_download_url': RELEASE_BASE_URL + 'SHA256SUMS',
                'size': 128,
            },
        ],
    }


def _update_info(*, expected_size: int | None = None) -> UpdateInfo:
    return UpdateInfo(
        installed_version='0.1.0',
        latest_version='0.2.0',
        published_at='2026-08-21',
        summary='Actualizador integrado.',
        release_notes_url=(
            'https://github.com/Xerkkun/toolbox-chaos/releases/tag/v0.2.0'
        ),
        download_url=RELEASE_BASE_URL + INSTALLER_NAME,
        asset_name=INSTALLER_NAME,
        asset_size=expected_size,
        checksum_url=RELEASE_BASE_URL + 'SHA256SUMS',
        checksum_asset_name='SHA256SUMS',
        update_available=True,
    )


def test_stable_release_selects_installer_and_checksum_manifest():
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url=RELEASE_API_URL,
        platform_tag='windows-x64',
        fetcher=lambda _url: _release_payload(),
    )
    assert info.update_available
    assert info.asset_name == INSTALLER_NAME
    assert info.asset_size == 1234
    assert info.checksum_asset_name == 'SHA256SUMS'
    assert info.checksum_url.endswith('/SHA256SUMS')


def test_release_asset_must_match_product_version_and_platform_exactly():
    payload = _release_payload()
    payload['assets'][0]['name'] = (
        'other-product-v0.2.0-windows-x64-setup.exe'
    )
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url=RELEASE_API_URL,
        platform_tag='windows-x64',
        fetcher=lambda _url: payload,
    )
    assert info.download_url is None
    assert info.asset_name is None

    payload = _release_payload()
    payload['assets'][0]['name'] = (
        'chaos-toolbox-v0.1.0-windows-x64-setup.exe'
    )
    with pytest.raises(UpdateCheckError, match='otra versión'):
        check_for_updates(
            installed_version='0.1.0',
            release_api_url=RELEASE_API_URL,
            platform_tag='windows-x64',
            fetcher=lambda _url: payload,
        )


@pytest.mark.parametrize(
    'asset_name',
    (
        'chaos-toolbox-v0.2.0-windows-x64.msi',
        'chaos-toolbox-v0.2.0-macos-arm64.pkg',
        'chaos-toolbox-v0.2.0-linux-x64.rpm',
        'chaos-toolbox-v0.2.0-linux-x64.AppImage',
    ),
)
def test_release_rejects_unimplemented_installer_formats(asset_name):
    platform_tag = '-'.join(asset_name.split('-')[-2:]).split('.')[0]
    if platform_tag == 'windows-x64':
        platform_tag = 'windows-x64'
    elif platform_tag == 'macos-arm64':
        platform_tag = 'macos-arm64'
    else:
        platform_tag = 'linux-x64'
    payload = _release_payload()
    payload['assets'][0]['name'] = asset_name
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url=RELEASE_API_URL,
        platform_tag=platform_tag,
        fetcher=lambda _url: payload,
    )
    assert info.asset_name is None
    assert info.download_url is None


def test_release_rejects_ambiguous_platform_installers():
    payload = _release_payload()
    payload['assets'].insert(
        1,
        {
            'name': INSTALLER_NAME,
            'browser_download_url': RELEASE_BASE_URL + INSTALLER_NAME + '?mirror=2',
            'size': 1234,
        },
    )
    with pytest.raises(UpdateCheckError, match='varios instaladores'):
        check_for_updates(
            installed_version='0.1.0',
            release_api_url=RELEASE_API_URL,
            platform_tag='windows-x64',
            fetcher=lambda _url: payload,
        )


@pytest.mark.parametrize(
    ('prerelease', 'tag'),
    ((True, 'v0.2.0'), (False, 'v0.2.0-rc1')),
)
def test_update_check_rejects_non_stable_releases(prerelease, tag):
    with pytest.raises(UpdateCheckError, match='prerelease|preliminar'):
        check_for_updates(
            installed_version='0.1.0',
            release_api_url=RELEASE_API_URL,
            platform_tag='windows-x64',
            fetcher=lambda _url: _release_payload(
                prerelease=prerelease, tag=tag
            ),
        )


def test_parse_sha256_manifest_supports_standard_and_sidecar_formats():
    digest = 'a' * 64
    assert parse_sha256_manifest(
        f'{digest}  {INSTALLER_NAME}\n', INSTALLER_NAME
    ) == digest
    assert parse_sha256_manifest(
        f'SHA256 ({INSTALLER_NAME}) = {digest.upper()}\n', INSTALLER_NAME
    ) == digest
    assert parse_sha256_manifest(
        digest, INSTALLER_NAME, allow_bare_digest=True
    ) == digest


def test_verified_download_is_atomic_and_rechecked_before_launch(tmp_path):
    payload = b'verified installer bytes'
    digest = sha256(payload).hexdigest()
    info = _update_info(expected_size=len(payload))

    def downloader(
        _url: str,
        destination: Path,
        _maximum: int,
        _cancel_event: Event | None,
        _deadline: float,
    ) -> int:
        destination.write_bytes(payload)
        return len(payload)

    verified = download_verified_update(
        info=info,
        destination_dir=tmp_path,
        manifest_fetcher=lambda _url: (
            f'{digest}  {INSTALLER_NAME}\n'.encode('utf-8')
        ),
        asset_downloader=downloader,
    )
    assert verified.path.read_bytes() == payload
    assert verified.sha256 == digest
    assert verify_update_before_launch(verified) == verified.path
    assert not list(tmp_path.glob('*.part'))
    assert not list(tmp_path.glob('.*.part'))

    verified.path.write_bytes(b'modified after verification')
    with pytest.raises(UpdateDownloadError, match='cambió'):
        verify_update_before_launch(verified)


def test_checksum_mismatch_discards_partial_and_preserves_previous_file(tmp_path):
    target = tmp_path / INSTALLER_NAME
    target.write_bytes(b'previous verified candidate')
    expected = b'expected bytes'
    digest = sha256(expected).hexdigest()

    def downloader(
        _url: str,
        destination: Path,
        _maximum: int,
        _cancel_event: Event | None,
        _deadline: float,
    ) -> int:
        payload = b'tampered bytes'
        destination.write_bytes(payload)
        return len(payload)

    with pytest.raises(UpdateDownloadError, match='SHA-256 falló'):
        download_verified_update(
            info=_update_info(),
            destination_dir=tmp_path,
            manifest_fetcher=lambda _url: (
                f'{digest}  {INSTALLER_NAME}\n'.encode('utf-8')
            ),
            asset_downloader=downloader,
        )
    assert target.read_bytes() == b'previous verified candidate'
    assert not list(tmp_path.glob('*.part'))
    assert not list(tmp_path.glob('.*.part'))


def test_download_honors_cancellation_and_total_deadline(tmp_path, monkeypatch):
    cancel_event = Event()
    cancel_event.set()
    with pytest.raises(UpdateDownloadError, match='cancelada'):
        download_verified_update(
            info=_update_info(),
            destination_dir=tmp_path,
            manifest_fetcher=lambda _url: b'',
            cancel_event=cancel_event,
        )

    ticks = iter((100.0, 101.0))
    monkeypatch.setattr(
        update_checker_module, 'monotonic', lambda: next(ticks)
    )
    with pytest.raises(UpdateDownloadError, match='tiempo total'):
        download_verified_update(
            info=_update_info(),
            destination_dir=tmp_path,
            manifest_fetcher=lambda _url: b'',
            deadline_seconds=0.5,
        )


def test_local_io_failures_are_wrapped_for_the_ui(tmp_path, monkeypatch):
    digest = sha256(b'installer').hexdigest()

    def deny_mkdir(*_args, **_kwargs):
        raise PermissionError('read-only destination')

    monkeypatch.setattr(update_checker_module.Path, 'mkdir', deny_mkdir)
    with pytest.raises(UpdateDownloadError, match='preparar o guardar'):
        download_verified_update(
            info=_update_info(),
            destination_dir=tmp_path,
            manifest_fetcher=lambda _url: (
                f'{digest}  {INSTALLER_NAME}\n'.encode('utf-8')
            ),
        )


def test_release_checksum_manifest_uses_exact_asset_basenames(tmp_path):
    input_root = tmp_path / 'downloaded-actions-artifacts'
    assets = {
        'windows/job/chaos-toolbox-v0.2.0-windows-x64-setup.exe': b'win',
        'macos/dist/chaos-toolbox-v0.2.0-macos-arm64.dmg': b'mac',
        'linux/dist/chaos-toolbox-v0.2.0-linux-x64.deb': b'linux',
        'python/dist/chaos_toolbox-0.2.0-py3-none-any.whl': b'wheel',
    }
    for relative, payload in assets.items():
        path = input_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    discovered = discover_release_assets(input_root, version='0.2.0')
    output = tmp_path / 'release' / 'SHA256SUMS'
    write_sha256_manifest(
        discovered,
        output,
        required_platforms=('windows', 'macos', 'linux'),
    )
    lines = output.read_text(encoding='utf-8').splitlines()
    manifest_names = [line.split('  ', 1)[1] for line in lines]
    assert manifest_names == sorted(
        (Path(name).name for name in assets), key=str.lower
    )
    assert all('/' not in name and '\\' not in name for name in manifest_names)


def test_release_checksum_manifest_requires_every_declared_platform(tmp_path):
    windows = tmp_path / 'chaos-toolbox-v0.2.0-windows-x64-setup.exe'
    windows.write_bytes(b'win')
    with pytest.raises(ReleaseChecksumError, match='macos'):
        write_sha256_manifest(
            [windows],
            tmp_path / 'SHA256SUMS',
            required_platforms=('windows', 'macos'),
        )


def test_release_workflow_prepares_manifest_without_automatic_publication():
    workflow = (
        Path(__file__).resolve().parents[1]
        / '.github'
        / 'workflows'
        / 'release.yml'
    ).read_text(encoding='utf-8')
    assert 'Generate SHA256SUMS for exact release asset names' in workflow
    assert '--require-platform windows' in workflow
    assert '--require-platform macos' in workflow
    assert '--require-platform linux' in workflow
    assert 'path: dist/release-manifest/SHA256SUMS' in workflow
    assert 'softprops/action-gh-release' not in workflow
    assert 'gh release create' not in workflow
