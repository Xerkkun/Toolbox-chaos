# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path(SPECPATH).resolve().parents[1]

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



a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[(str(ROOT / 'core' / 'bin' / 'chaos_core.dll'), 'core/bin')],
    datas=[(str(ROOT / 'assets'), 'assets')],
    hiddenimports=['PyQt6.QtPdf', 'PyQt6.QtPdfWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
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
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='Chaos Toolbox',
)
