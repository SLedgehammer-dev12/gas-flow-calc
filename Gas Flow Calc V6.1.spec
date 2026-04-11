# -*- mode: python ; coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(SPEC)))

from release_metadata import get_versioned_exe_stem


APP_EXE_STEM = get_versioned_exe_stem()
PYTHON_DLLS_DIR = os.path.join(sys.base_prefix, "DLLs")
SSL_RUNTIME_BINARIES = []
for dll_name in ("_ssl.pyd", "libssl-3.dll", "libcrypto-3.dll"):
    dll_path = os.path.join(PYTHON_DLLS_DIR, dll_name)
    if os.path.isfile(dll_path):
        SSL_RUNTIME_BINARIES.append((dll_path, "."))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=SSL_RUNTIME_BINARIES,
    datas=[],
    hiddenimports=[
        'unicodedata',
        'ssl',
        '_ssl',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends._backend_tk',
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
    name=APP_EXE_STEM,
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
