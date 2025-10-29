# Building Project Nimbus Executable

This guide explains how to create a standalone Windows executable (.exe) for Project Nimbus.

## Quick Start

### Option 1: Automated Build (Recommended)

Simply run the build script:

```batch
build_exe.bat
```

This will:
1. Check for PyInstaller and install it if needed
2. Clean previous build files
3. Build the executable using PyInstaller
4. Create `dist\Project-Nimbus.exe`

### Option 2: Manual Build

If you prefer to build manually:

```batch
# Activate virtual environment
venv\Scripts\activate

# Install PyInstaller (if not already installed)
pip install pyinstaller>=6.0.0

# Build the executable
pyinstaller --clean --noconfirm Project-Nimbus.spec
```

## Output

After a successful build, you'll find:

- **Executable**: `dist\Project-Nimbus.exe` - The standalone application
- **Build files**: `build\` folder - Temporary build files (can be deleted)

## Distribution

The `Project-Nimbus.exe` file in the `dist` folder is a **standalone executable** that includes:

- All Python dependencies (PySide6, NumPy, pyvjoy)
- All QML interface files
- Configuration files
- Application resources

### To distribute:

1. Copy `dist\Project-Nimbus.exe` to any location
2. The executable can run on any Windows system **without Python installed**
3. **Important**: The target system must have [VJoy driver](http://vjoystick.sourceforge.net/) installed

## File Size

The executable will be approximately 100-150 MB due to bundled Qt libraries and Python runtime.

## Troubleshooting

### Build fails with "Module not found"

Make sure all dependencies are installed in your virtual environment:
```batch
venv\Scripts\activate
pip install -r requirements.txt
```

### Executable doesn't start

- Check that VJoy driver is installed on the target system
- Try running from command line to see error messages:
  ```batch
  dist\Project-Nimbus.exe
  ```

### "Console=False" option

The spec file is configured with `console=False`, which means:
- No console window appears when running the .exe
- For debugging, change `console=True` in `Project-Nimbus.spec`

### Antivirus False Positives

Some antivirus software may flag PyInstaller executables as suspicious. This is a known issue with PyInstaller. You may need to:
- Add an exception in your antivirus software
- Submit the executable to your antivirus vendor for whitelisting

## Advanced Configuration

### Customizing the Build

Edit `Project-Nimbus.spec` to customize:

- **Icon**: Change `icon='logo.png'` to use a custom .ico file
- **Console**: Set `console=True` to show console window for debugging
- **UPX Compression**: Set `upx=False` to disable compression (faster build, larger file)
- **One-file vs One-folder**: Current config creates one-file executable

### Creating an Icon

To use a proper Windows icon:

1. Convert `logo.png` to `logo.ico` using an online converter
2. Update the spec file: `icon='logo.ico'`
3. Rebuild

## Build Requirements

- Windows OS
- Python 3.8+
- Virtual environment with all dependencies installed
- PyInstaller 6.0+
- Approximately 500MB free disk space for build process

## Clean Build

To perform a completely clean build:

```batch
# Delete all build artifacts
rmdir /s /q build
rmdir /s /q dist
del /q *.spec~

# Rebuild
build_exe.bat
```

## Notes

- First build may take 5-10 minutes
- Subsequent builds are faster (2-3 minutes)
- The executable is portable and can be copied to other Windows systems
- Configuration file (`controller_config.json`) is created in the same directory as the .exe on first run
