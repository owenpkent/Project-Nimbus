# Project Nimbus Documentation

> **Quick Start**: See [../DIRECTORY.md](../DIRECTORY.md) for project structure overview.

## Setup & Installation
- [Installation Guide](setup/INSTALLATION.md) — installer, vJoy setup, prerequisites, troubleshooting
- [Profile System](setup/PROFILES.md) — profile storage, JSON structure, custom layout widget properties
- [Packaging Guide](setup/PACKAGING.md) — **build & distribute** — PyInstaller, NSIS, code signing, release checklist

## Architecture
- [Architecture Overview](architecture/architecture.md) — codebase structure, QML/Python bridge, widget system
- [V-Droid Driver Brainstorm](architecture/VDROID_DRIVER_BRAINSTORM.md) — custom virtual HID driver plans (future)

## Development
- [LLM Notes](development/LLM_NOTES.md) — **for AI assistants** — implementation details, conventions, known fixes
- [Integration Guide](development/INTEGRATION_GUIDE.md) — how to add new widgets and features
- [Start Here](development/START_HERE.md) — quick orientation for new contributors
- [Widget Ideas](development/WIDGET_IDEAS.md) — planned and brainstormed widget concepts

## Accessibility
- [Accessibility Spotlight Nomination](accessibility/ACCESSIBILITY_SPOTLIGHT_NOMINATION.md)

## Media
- [Screenshots](screenshots/) — application UI screenshots
- [Video](video/) — demo videos

---

## Key Files for AI Assistants

| Task | File |
|------|------|
| Understand project structure | [../DIRECTORY.md](../DIRECTORY.md) |
| Make UI changes | `qml/Main.qml`, `qml/layouts/CustomLayout.qml` |
| Add QML↔Python features | `src/bridge.py` |
| Build releases | [setup/PACKAGING.md](setup/PACKAGING.md) |
| Bug fixes / implementation notes | [development/LLM_NOTES.md](development/LLM_NOTES.md) |
