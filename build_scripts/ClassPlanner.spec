# -*- mode: python ; coding: utf-8 -*-
"""
ClassPlanner - PyInstaller Specification File
Cross-platform configuration for Windows, macOS, and Linux standalone executable builds.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Hidden imports needed for PySide6, reportlab, openpyxl, and sqlite3
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.platypus',
    'reportlab.lib.styles',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'sqlite3',
    'hashlib',
]

datas = collect_data_files('reportlab')

a = Analysis(
    ['../run.py'],
    pathex=['..'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'torch'],
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
    name='ClassPlanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI without console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)

# For macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ClassPlanner.app',
        icon=None,
        bundle_identifier='edu.college.classplanner',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': 'ClassPlanner',
            'CFBundleDisplayName': 'ClassPlanner',
            'CFBundleGetInfoString': 'ClassPlanner Automated College Timetable Generator',
            'CFBundleIdentifier': 'edu.college.classplanner',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        }
    )

