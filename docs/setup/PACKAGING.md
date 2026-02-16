# Packaging Guide — Windows Build & Installer

> **Last updated**: February 2026  
> **Version**: 1.2.1  
> **Author**: Owen Kent

Comprehensive guide for building, packaging, and distributing Project Nimbus as a standalone Windows executable with installer.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Build](#quick-build)
4. [PyInstaller Configuration](#pyinstaller-configuration)
5. [NSIS Installer Configuration](#nsis-installer-configuration)
6. [Code Signing](#code-signing)
7. [Installer UX Flow](#installer-ux-flow)
8. [Troubleshooting](#troubleshooting)
9. [Release Checklist](#release-checklist)

---

## Overview

Project Nimbus uses:
- **PyInstaller** — Bundles Python + PySide6 QML into a single `.exe`
- **NSIS** — Creates a Windows installer with shortcuts, uninstall, version detection
- **EV Code Signing** — SHA-256 signed with hardware token for instant SmartScreen trust

### Output Files

| File | Description | Size |
|------|-------------|------|
| `dist/Project-Nimbus.exe` | Standalone executable | ~165 MB |
| `dist/Project-Nimbus-Setup-X.Y.Z.exe` | NSIS installer | ~166 MB |

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Runtime |
| PyInstaller | 6.x | Executable bundler |
| NSIS | 3.x | Installer creator |
| Windows SDK | 10.x | signtool.exe for code signing |
| SafeNet Client | Latest | EV certificate USB token driver |

### Install Build Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Verify NSIS is installed
"C:\Program Files (x86)\NSIS\makensis.exe" /VERSION
```

---

## Quick Build

```powershell
# 1. Build executable
venv\Scripts\pyinstaller.exe build_tools\Project-Nimbus.spec --noconfirm

# 2. Build installer
& "C:\Program Files (x86)\NSIS\makensis.exe" build_tools\installer.nsi

# 3. Sign both files
cmd /c build_tools\sign_exe.bat
```

Output will be in `dist/`.

---

## PyInstaller Configuration

### Spec File: `build_tools/Project-Nimbus.spec`

Key configuration:

```python
# Entry point
main_script = PROJECT_ROOT / 'build_tools' / 'launcher.py'

# Add project root to path so 'src' package is found
pathex=[str(PROJECT_ROOT)]

# Bundle QML files, logo, profiles, and src package
datas = qml_datas + logo_datas + config_datas + profile_datas + src_datas

# Hidden imports for PySide6 and project modules
hiddenimports = [
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickControls2',
    'numpy', 'pyvjoy',
    'src.qt_qml_app', 'src.bridge', 'src.config', ...
]

# Single-file executable (no console window)
console=False

# Windows manifest for UIAccess
manifest=str(PROJECT_ROOT / 'build_tools' / 'Project-Nimbus.manifest')
```

### Launcher Script: `build_tools/launcher.py`

The launcher is a simplified entry point that:
1. Handles frozen vs development mode paths
2. Imports and runs `src.qt_qml_app.main()`
3. Shows a Qt error dialog if startup fails (no console available)

### Data Files Bundled

| Data | Destination | Purpose |
|------|-------------|---------|
| `qml/**/*.qml` | `qml/` | QML UI components |
| `logo.png` | `.` | Splash screen logo |
| `profiles/*.json` | `profiles/` | Default profile templates |
| `controller_config.json` | `.` | Default config |

### Common PyInstaller Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `No module named 'src'` | Project root not in pathex | Add `pathex=[str(PROJECT_ROOT)]` |
| QML files not found | datas not including qml dir | Use `rglob('*.qml')` pattern |
| Hidden import errors | PySide6 modules not detected | Add to `hiddenimports` list |
| DLL not found | numpy/PySide6 DLLs missing | PyInstaller usually handles this automatically |

---

## NSIS Installer Configuration

### Script: `build_tools/installer.nsi`

Key features:
- **Wizard UI** — Not one-click; shows Welcome, Directory, Shortcuts, Install, Finish pages
- **Admin elevation** — UAC prompt for admin password
- **Running app detection** — Checks if Project-Nimbus.exe is running, offers to close it
- **Previous version detection** — Checks BOTH HKCU and HKLM registries
- **Shortcut options** — Custom page with checkboxes for Desktop and Start Menu
- **BringToFront** — Ensures installer window appears after UAC elevation

### Registry Keys

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\project-nimbus-virtual-controller
  - DisplayName
  - DisplayVersion
  - Publisher
  - UninstallString
  - InstallLocation
  - DisplayIcon
  - EstimatedSize
```

### Install Locations

| Mode | Path | Registry |
|------|------|----------|
| Per-user (default) | `%LOCALAPPDATA%\Programs\Project Nimbus\` | HKCU |
| Per-machine | `C:\Program Files\Project Nimbus\` | HKLM |

### Shortcuts Created

Based on user checkbox selection:
- `%DESKTOP%\Project Nimbus.lnk`
- `%SMPROGRAMS%\Project Nimbus\Project Nimbus.lnk`
- `%SMPROGRAMS%\Project Nimbus\Uninstall Project Nimbus.lnk`

### NSIS Best Practices (from experience)

| Do | Don't |
|----|-------|
| Use `BringToFront` in `.onInit` | Put MessageBox in `.onInit` with admin elevation (runs twice) |
| Check both HKCU and HKLM for old versions | Only check one registry hive |
| Use custom page for shortcut options | Rely on MUI's unreliable shortcut checkbox |
| Always prompt before removing old version | Silently remove without asking |
| Keep GUID stable across versions | Change GUID (breaks upgrade detection) |

---

## Code Signing

### Why EV Signing?

| Type | SmartScreen | Cost |
|------|-------------|------|
| Unsigned | Blocked | Free |
| Standard OV | Warning for weeks/months | ~$200/yr |
| **EV (Extended Validation)** | **Immediate trust** | ~$400/yr |

### Setup

1. **EV Certificate** — Purchase from Sectigo, DigiCert, or GlobalSign
2. **Hardware Token** — SafeNet USB token with certificate installed
3. **SafeNet Client** — Install driver software
4. **Windows SDK** — For signtool.exe

### Signing Script: `build_tools/sign_exe.bat`

```batch
set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
set TIMESTAMP_URL=http://timestamp.digicert.com

%SIGNTOOL% sign /tr %TIMESTAMP_URL% /td sha256 /fd sha256 /a "dist\Project-Nimbus.exe"
%SIGNTOOL% verify /pa "dist\Project-Nimbus.exe"
```

### Verifying Signatures

```powershell
# Quick check
(Get-AuthenticodeSignature "dist\Project-Nimbus.exe").Status

# Detailed check
signtool verify /pa /v "dist\Project-Nimbus-Setup-1.2.1.exe"
```

---

## Installer UX Flow

```
1. User runs Project-Nimbus-Setup-X.Y.Z.exe
2. UAC admin password prompt
3. Installer window appears (BringToFront ensures visibility)
4. If app is running → "Close it?" dialog
5. If old version found (HKCU or HKLM) → "Remove old version?" dialog
6. Welcome page → Next
7. Choose install directory → Next
8. Shortcut options page (Desktop ☑, Start Menu ☑) → Next
9. Install progress bar
10. Finish page with "Launch Project Nimbus" checkbox
11. App appears in Windows 11 "Recommended" section (Start Menu shortcut triggers this)
```

---

## Troubleshooting

### PyInstaller Issues

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'src'` | Add `pathex=[str(PROJECT_ROOT)]` to Analysis |
| `QML module not found` | Ensure QML files are in datas list |
| `Failed to execute script 'launcher'` | Check launcher.py imports, ensure src package bundled |
| Icon not showing | Verify `Project-Nimbus.ico` exists in build_tools |

### NSIS Issues

| Error | Solution |
|-------|----------|
| `makensis not found` | Add NSIS to PATH or use full path |
| `File not found: ..\dist\Project-Nimbus.exe` | Build executable first with PyInstaller |
| Installer shows twice (double prompts) | Move MessageBox from `.onInit` to install section |
| Shortcuts not created | Verify `$CreateDesktopShortcut` variable is 1 |

### Code Signing Issues

| Error | Solution |
|-------|----------|
| `Cannot find certificate` | Ensure USB token is plugged in, run from non-elevated shell |
| `File being used by another process` | Wait for antivirus scan, add retry logic |
| `Timestamp server error` | Try alternative: `http://timestamp.sectigo.com` |

---

## Release Checklist

### Pre-Build

- [ ] Update version in `build_tools/Project-Nimbus.spec` (VERSION constant)
- [ ] Update version in `build_tools/installer.nsi` (PRODUCT_VERSION)
- [ ] Update version in `build_tools/sign_exe.bat` (INSTALLER_PATH)
- [ ] Update version in `build_tools/version_info.txt`
- [ ] Update version in `src/__init__.py`
- [ ] Update `CHANGELOG.md` with release notes

### Build

- [ ] Activate virtual environment
- [ ] Run PyInstaller: `venv\Scripts\pyinstaller.exe build_tools\Project-Nimbus.spec --noconfirm`
- [ ] Run NSIS: `& "C:\Program Files (x86)\NSIS\makensis.exe" build_tools\installer.nsi`
- [ ] Sign files: `cmd /c build_tools\sign_exe.bat`

### Test

- [ ] Run installer on clean Windows VM
- [ ] Verify UAC prompt appears
- [ ] Verify previous version detection works
- [ ] Verify shortcut options page appears
- [ ] Verify desktop and start menu shortcuts created
- [ ] Verify app launches and works
- [ ] Verify uninstaller removes files and offers to remove user data
- [ ] Test upgrade from previous version

### Publish

- [ ] Create GitHub release with version tag
- [ ] Upload `Project-Nimbus-Setup-X.Y.Z.exe` as release asset
- [ ] Update README download link if needed

---

## Version Locations

When bumping versions, update these files:

| File | Location |
|------|----------|
| `build_tools/Project-Nimbus.spec` | `VERSION = "X.Y.Z"` |
| `build_tools/installer.nsi` | `!define PRODUCT_VERSION "X.Y.Z"` |
| `build_tools/sign_exe.bat` | `INSTALLER_PATH=dist\Project-Nimbus-Setup-X.Y.Z.exe` |
| `build_tools/version_info.txt` | `filevers=(X, Y, Z, 0)` and `prodvers=(X, Y, Z, 0)` |
| `src/__init__.py` | `__version__ = "X.Y.Z"` |
| `CHANGELOG.md` | Add release notes under `## [X.Y.Z]` |
