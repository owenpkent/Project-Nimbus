# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Project Nimbus Virtual Controller
This creates a standalone Windows executable with all dependencies bundled.
"""

import sys
from pathlib import Path

# Version info - keep in sync with src/__init__.py
VERSION = "1.0.1"
VERSION_TUPLE = (1, 0, 1, 0)

block_cipher = None

# Define the main script (use launcher.py for executable, not run.py)
# Get the project root directory (parent of build_tools)
SPEC_DIR = Path(__file__).parent if '__file__' in dir() else Path.cwd()
PROJECT_ROOT = SPEC_DIR.parent if SPEC_DIR.name == 'build_tools' else SPEC_DIR
main_script = str(PROJECT_ROOT / 'build_tools' / 'launcher.py')

# Collect all QML files and resources
qml_datas = []
qml_path = PROJECT_ROOT / 'qml'
if qml_path.exists():
    for qml_file in qml_path.rglob('*.qml'):
        rel_path = qml_file.relative_to(PROJECT_ROOT)
        qml_datas.append((str(qml_file), str(rel_path.parent)))

# Add logo
logo_datas = [(str(PROJECT_ROOT / 'logo.png'), '.')]

# Add controller config template
config_datas = [(str(PROJECT_ROOT / 'controller_config.json'), '.')]

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
    version=str(PROJECT_ROOT / 'build_tools' / 'version_info.txt'),  # Windows version resource
)
