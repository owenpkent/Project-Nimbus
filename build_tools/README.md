# Build Tools

This directory contains tools for building Project Nimbus as a standalone executable.

## Files

- **`build_exe.bat`** - Automated build script for creating the Windows executable
- **`Project-Nimbus.spec`** - PyInstaller configuration file
- **`launcher.py`** - GUI-friendly entry point for the executable (no stdin dependencies)
- **`BUILD_EXECUTABLE.md`** - Comprehensive build documentation
- **`create_release.bat`** - Script for creating GitHub releases

## Quick Build

From the project root directory:
```batch
build_tools\build_exe.bat
```

Or from this directory:
```batch
build_exe.bat
```

The executable will be created at `dist\Project-Nimbus.exe`

## Documentation

See `BUILD_EXECUTABLE.md` for detailed build instructions and troubleshooting.
