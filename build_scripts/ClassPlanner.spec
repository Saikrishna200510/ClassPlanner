# -*- mode: python ; coding: utf-8 -*-
"""
ClassPlanner - PyInstaller Specification File
Cross-platform configuration for Windows, macOS, and Linux standalone executable builds.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Hidden imports needed for PySide6, reportlab, openpyxl, psycopg2, and sqlite3
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
    'psycopg2',
    'psycopg2.extras',
    'classplanner',
    'classplanner.config',
    'classplanner.auth',
    'classplanner.auth.auth_service',
    'classplanner.auth.models',
    'classplanner.database',
    'classplanner.database.db_manager',
    'classplanner.database.schema',
    'classplanner.database.sample_data',
    'classplanner.database.backup',
    'classplanner.database.supabase_sync',
    'classplanner.solver',
    'classplanner.solver.timetable_generator',
    'classplanner.solver.validator',
    'classplanner.exporters',
    'classplanner.exporters.pdf_exporter',
    'classplanner.exporters.excel_exporter',
    'classplanner.ui',
    'classplanner.ui.styles',
    'classplanner.ui.main_window',
    'classplanner.ui.dialogs',
    'classplanner.ui.widgets',
]

# Determine base root directory dynamically
spec_dir = os.path.dirname(os.path.abspath(SPEC)) if 'SPEC' in locals() else os.getcwd()
if os.path.basename(spec_dir) == 'build_scripts':
    root_dir = os.path.dirname(spec_dir)
else:
    root_dir = spec_dir

# Collect resources and reportlab data files
datas = [
    (os.path.join(root_dir, 'classplanner', 'resources'), 'classplanner/resources'),
    (os.path.join(root_dir, 'classplanner', 'database', 'supabase_multitenant.sql'), 'classplanner/database'),
] + collect_data_files('reportlab')

# Determine platform-specific icon
app_icon = None
if sys.platform == 'win32':
    app_icon = os.path.join(root_dir, 'classplanner', 'resources', 'icon.ico')
elif sys.platform == 'darwin':
    app_icon = os.path.join(root_dir, 'classplanner', 'resources', 'icon.icns')
else:
    app_icon = os.path.join(root_dir, 'classplanner', 'resources', 'icon.png')

a = Analysis(
    [os.path.join(root_dir, 'run.py')],
    pathex=[root_dir],
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

# On macOS, build a standard onedir bundle (COLLECT + BUNDLE) for native framework loading
if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ClassPlanner',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        icon=app_icon
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='ClassPlanner'
    )
    app = BUNDLE(
        coll,
        name='ClassPlanner.app',
        icon=app_icon,
        bundle_identifier='com.slit.classplanner',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': 'ClassPlanner',
            'CFBundleDisplayName': 'ClassPlanner',
            'CFBundleExecutable': 'ClassPlanner',
            'CFBundlePackageType': 'APPL',
            'CFBundleGetInfoString': 'ClassPlanner - Multi-College Automated Timetable Management System',
            'CFBundleIdentifier': 'com.slit.classplanner',
            'CFBundleVersion': '1.0.2',
            'CFBundleShortVersionString': '1.0.2',
            'NSHumanReadableCopyright': 'Copyright © 2026 SL IT Solutions. All rights reserved.',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '11.0',
        }
    )
else:
    # Standalone single executable for Windows & Linux
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
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=app_icon
    )
