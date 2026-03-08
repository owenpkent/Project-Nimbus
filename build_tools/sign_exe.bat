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
set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
set TIMESTAMP_URL=http://timestamp.digicert.com
set EXE_PATH=dist\Project-Nimbus-1.3.2.exe
set INSTALLER_PATH=dist\Project-Nimbus-Setup-1.3.2.exe

REM Check if signtool exists
if not exist %SIGNTOOL% (
    echo ERROR: signtool.exe not found at %SIGNTOOL%
    echo Please install Windows SDK or update the SIGNTOOL path in this script.
    pause
    exit /b 1
)

echo NOTE: You may be prompted for your hardware token PIN.
echo.

REM Sign the main executable
if exist "%EXE_PATH%" (
    echo Signing %EXE_PATH%...
    %SIGNTOOL% sign /tr %TIMESTAMP_URL% /td sha256 /fd sha256 /a "%EXE_PATH%"
    if errorlevel 1 (
        echo ERROR: Failed to sign %EXE_PATH%
        pause
        exit /b 1
    )
    echo Verifying...
    %SIGNTOOL% verify /pa "%EXE_PATH%"
    if errorlevel 1 (
        echo ERROR: Signature verification failed for %EXE_PATH%
        pause
        exit /b 1
    )
    echo [OK] %EXE_PATH% signed and verified.
    echo.
) else (
    echo WARNING: %EXE_PATH% not found, skipping.
)

REM Sign the installer (if it exists)
if exist "%INSTALLER_PATH%" (
    echo Signing %INSTALLER_PATH%...
    %SIGNTOOL% sign /tr %TIMESTAMP_URL% /td sha256 /fd sha256 /a "%INSTALLER_PATH%"
    if errorlevel 1 (
        echo ERROR: Failed to sign %INSTALLER_PATH%
        pause
        exit /b 1
    )
    echo Verifying...
    %SIGNTOOL% verify /pa "%INSTALLER_PATH%"
    if errorlevel 1 (
        echo ERROR: Signature verification failed for %INSTALLER_PATH%
        pause
        exit /b 1
    )
    echo [OK] %INSTALLER_PATH% signed and verified.
    echo.
) else (
    echo WARNING: %INSTALLER_PATH% not found, skipping installer signing.
)

echo.
echo ================================================
echo SUCCESS: All available files are signed!
echo ================================================
echo.
pause
