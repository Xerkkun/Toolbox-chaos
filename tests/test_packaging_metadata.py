from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtWidgets import QApplication

from core.app_metadata import APP_AUTHOR_DISPLAY, APP_BRAND, APP_DEVELOPER, APP_LICENSE, APP_VERSION
from core.update_checker import (
    ReleaseAsset,
    check_for_updates,
    is_newer_version,
    parse_semver,
    select_asset,
)
from ui.main_window import MainWindow


def test_version_metadata_is_semver():
    assert parse_semver(APP_VERSION) == (0, 1, 0)
    assert APP_DEVELOPER == 'Maria Fernanda Moreno Lopez'
    assert APP_LICENSE == 'MIT'
    assert 'Maria Fernanda Moreno Lopez' in APP_AUTHOR_DISPLAY
    assert 'Fer Moreno' in APP_AUTHOR_DISPLAY
    assert APP_BRAND == 'Fyskode'


def test_update_version_comparison():
    assert is_newer_version('v0.1.1', '0.1.0')
    assert not is_newer_version('0.1.0', '0.1.0')
    assert not is_newer_version('0.0.9', '0.1.0')


def test_update_asset_selection_by_platform():
    assets = [
        ReleaseAsset('chaos-toolbox-v0.1.0-linux-x64.AppImage', 'https://example.invalid/linux'),
        ReleaseAsset('chaos-toolbox-v0.1.0-windows-x64-setup.exe', 'https://example.invalid/windows'),
    ]
    selected = select_asset(assets, 'windows-x64')
    assert selected is not None
    assert selected.browser_download_url.endswith('/windows')


def test_update_check_available_and_unavailable_with_mock_fetcher():
    payload = {
        'tag_name': 'v0.1.1',
        'published_at': '2026-06-14T00:00:00Z',
        'html_url': 'https://example.invalid/releases/v0.1.1',
        'body': 'Maintenance release.',
        'assets': [
            {
                'name': 'chaos-toolbox-v0.1.1-windows-x64-setup.exe',
                'browser_download_url': 'https://example.invalid/download',
            }
        ],
    }
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url='https://example.invalid/latest',
        platform_tag='windows-x64',
        fetcher=lambda _url: payload,
    )
    assert info.update_available
    assert info.download_url == 'https://example.invalid/download'

    payload['tag_name'] = 'v0.1.0'
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url='https://example.invalid/latest',
        platform_tag='windows-x64',
        fetcher=lambda _url: payload,
    )
    assert not info.update_available


def test_mainwindow_help_menu_contains_packaging_actions():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    help_act = next(act for act in window.menuBar().actions() if act.text() == 'Ayuda')
    actions = [
        action.text()
        for action in help_act.menu().actions()
        if action.text()
    ]
    assert 'Buscar actualizaciones' in actions
    assert 'Revisar actualizaciones automaticamente' in actions
    assert 'Acerca de' in actions
    window.deleteLater()
