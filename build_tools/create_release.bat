@echo off
REM Create GitHub release v1.4.2 with executable

set ASSETS=dist\Nimbus-Adaptive-Controller-1.4.2.exe
if exist "dist\Nimbus-Adaptive-Controller-Setup-1.4.2.exe" set ASSETS=%ASSETS% "dist\Nimbus-Adaptive-Controller-Setup-1.4.2.exe"
gh release create v1.4.2 --title "Version 1.4.2" --notes "See CHANGELOG.md for details." %ASSETS%
