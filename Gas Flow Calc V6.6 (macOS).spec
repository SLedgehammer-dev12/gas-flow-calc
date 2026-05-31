# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS — .app bundle

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(SPEC)))

from release_metadata import APP_NAME, APP_VERSION


APP_BUNDLE_NAME = f"{APP_NAME} V{APP_VERSION}"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'unicodedata',
        'ssl',
        '_ssl',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends._backend_tk',
        'pyaga8',
        'cryptography',
    ],
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
    a.binaries,
    a.datas,
    [],
    name=APP_BUNDLE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    [],
    name=APP_BUNDLE_NAME + ".app",
    icon=None,
    display_name=APP_NAME,
    version=APP_VERSION,
)
