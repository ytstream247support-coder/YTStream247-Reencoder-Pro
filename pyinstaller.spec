# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Collect app data files (FFmpeg is packaged as sidecar by installer scripts)
datas = [
    ('assets/lang', 'assets/lang'),
    ('assets/icons', 'assets/icons'),
]

# QtAwesome bundles icon font files that PyInstaller needs to find
from PyInstaller.utils.hooks import collect_data_files
datas += collect_data_files('qtawesome')

# Note: FFmpeg executables are intentionally NOT bundled into the executable.
# Official installers package them as ffmpeg-apps/ next to the app binary.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['qtawesome'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YTStream247Reencoder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=(os.environ.get('PYI_TARGET_ARCH', '').strip() or None),
    codesign_identity=None,
    entitlements_file=None,
    icon=(
        'assets/icons/icon.ico'
        if Path('assets/icons/icon.ico').exists()
        else ('icon.ico' if Path('icon.ico').exists() else None)
    ),
    version='version_info.txt',
)

