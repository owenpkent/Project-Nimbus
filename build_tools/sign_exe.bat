@echo off
REM Code signing script for Project Nimbus
REM Requires EV certificate on hardware token

echo ================================================
echo Project Nimbus - Code Signing
echo ================================================
echo.

REM Change to project root directory (parent of build_tools)
cd /d "%~dp0\.."

REM Configure paths - update SIGNTOOL path if needed
set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
set TIMESTAMP_URL=http://timestamp.digicert.com
set EXE_PATH=dist\Project-Nimbus.exe

REM Check if executable exists
if not exist "%EXE_PATH%" (
    echo ERROR: %EXE_PATH% not found!
    echo Run build_exe.bat first to create the executable.
    pause
    exit /b 1
)

REM Check if signtool exists
if not exist %SIGNTOOL% (
    echo ERROR: signtool.exe not found at %SIGNTOOL%
    echo Please install Windows SDK or update the SIGNTOOL path in this script.
    pause
    exit /b 1
)

echo Signing %EXE_PATH%...
echo.
echo NOTE: You may be prompted for your hardware token PIN.
echo.

%SIGNTOOL% sign /tr %TIMESTAMP_URL% /td sha256 /fd sha256 /a "%EXE_PATH%"

if errorlevel 1 (
    echo.
    echo ERROR: Signing failed!
    echo.
    echo Common issues:
    echo - Hardware token not connected
    echo - Token not unlocked (wrong PIN)
    echo - Certificate expired
    echo.
    pause
    exit /b 1
)

echo.
echo Verifying signature...
%SIGNTOOL% verify /pa "%EXE_PATH%"

if errorlevel 1 (
    echo.
    echo ERROR: Signature verification failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo SUCCESS: %EXE_PATH% is signed and verified!
echo ================================================
echo.
pause
