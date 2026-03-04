@echo off
REM Create GitHub release v1.3.1 with executable

set ASSETS=dist\Project-Nimbus-1.3.1.exe
if exist "dist\Project-Nimbus-Setup-1.3.1.exe" set ASSETS=%ASSETS% "dist\Project-Nimbus-Setup-1.3.1.exe"
gh release create v1.3.1 --title "Version 1.3.1" --notes "See CHANGELOG.md for details." %ASSETS%
