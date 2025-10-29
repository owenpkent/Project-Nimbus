@echo off
REM Create GitHub release v1.0.0 with executable

gh release create v1.0.0 --title "Version 1.0.0" --notes "Initial release of the project." "dist\Project-Nimbus.exe"
