@echo off
REM Build script for Project Nimbus executable
REM This script creates a standalone .exe file using PyInstaller

echo ================================================
echo Project Nimbus - Executable Builder
echo ================================================
echo.

REM Change to project root directory (parent of build_tools)
cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run run.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install PyInstaller if not already installed
echo.
echo Checking for PyInstaller...
python -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller>=6.0.0
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Clean previous build
echo.
echo Cleaning previous build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Project-Nimbus.exe" del /q "Project-Nimbus.exe"

REM Build the executable
echo.
echo Building executable with PyInstaller...
echo This may take a few minutes...
echo.
pyinstaller --clean --noconfirm build_tools\Project-Nimbus.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

REM Check if executable was created
if exist "dist\Project-Nimbus.exe" (
    echo.
    echo ================================================
    echo SUCCESS! Executable created successfully!
    echo ================================================
    echo.
    echo Location: dist\Project-Nimbus.exe
    echo.
    echo You can now:
    echo 1. Run dist\Project-Nimbus.exe directly
    echo 2. Copy dist\Project-Nimbus.exe to any location
    echo.
    echo NOTE: Make sure VJoy driver is installed on the target system!
    echo.
) else (
    echo.
    echo ERROR: Executable was not created!
    echo Check the build output for errors.
)

pause
