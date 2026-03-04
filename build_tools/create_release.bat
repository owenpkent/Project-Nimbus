@echo off
REM Create GitHub release v1.3.1 with executable

gh release create v1.3.1 --title "Version 1.3.1" --notes "See CHANGELOG.md for details." "dist\Project-Nimbus-1.3.1.exe" "dist\Project-Nimbus-Setup-1.3.1.exe"
