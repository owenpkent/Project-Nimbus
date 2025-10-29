# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Project Nimbus Virtual Controller
This creates a standalone Windows executable with all dependencies bundled.
"""

import sys
from pathlib import Path

block_cipher = None

# Define the main script (use launcher.py for executable, not run.py)
main_script = 'launcher.py'

# Collect all QML files and resources
qml_datas = []
qml_path = Path('qml')
if qml_path.exists():
    for qml_file in qml_path.rglob('*.qml'):
        qml_datas.append((str(qml_file), str(qml_file.parent)))

# Add logo
logo_datas = [('logo.png', '.')]

# Add controller config template
config_datas = [('controller_config.json', '.')]

# Combine all data files
datas = qml_datas + logo_datas + config_datas

# Hidden imports for PySide6 and other dependencies
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickControls2',
    'numpy',
    'pyvjoy',
    'src.qt_qml_app',
    'src.qt_main',
    'src.bridge',
    'src.config',
    'src.vjoy_interface',
    'src.qt_dialogs',
    'src.qt_widgets',
]

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Project-Nimbus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Set to None for now - can add .ico file later
)
