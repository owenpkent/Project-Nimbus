# LLM Notes

Quick reference for AI assistants working on Project Nimbus.

## Project Context

**Project Nimbus** is a virtual controller interface that transforms mouse input into virtual joystick commands via vJoy. It's designed for accessibility—enabling users with mobility limitations to interact with joystick-dependent software using mouse input.

**Primary use cases:**
- Adaptive gaming (mouse-first joystick control)
- UAV/rover control via Mission Planner
- Steam Input integration for XInput games
- Assistive technology development

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| UI Framework | Qt Quick (PySide6 QML) |
| Driver | vJoy (virtual joystick) |
| Config | JSON (`controller_config.json`) |
| Build | PyInstaller |

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Entry point (launches QML UI) |
| `src/qt_qml_app.py` | QML application bootstrap |
| `src/bridge.py` | Python↔QML bridge (`ControllerBridge`) |
| `src/qt_dialogs.py` | Qt Widgets settings dialogs |
| `src/vjoy_interface.py` | vJoy driver communication |
| `src/config.py` | Configuration management |
| `qml/Main.qml` | Main QML window and layout |
| `qml/components/` | Reusable QML controls (Joystick, Sliders) |

## Project Structure

```
Project-Nimbus/
├── run.py                    # Launcher (Qt Quick UI default)
├── qml/                      # QML UI files
│   ├── Main.qml
│   └── components/
├── src/
│   ├── qt_qml_app.py         # QML app entry
│   ├── bridge.py             # ControllerBridge (Python↔QML)
│   ├── qt_dialogs.py         # Settings dialogs
│   ├── vjoy_interface.py     # vJoy driver interface
│   ├── config.py             # Config management
│   └── legacy/               # Old pygame UI (reference only)
├── build_tools/              # PyInstaller build system
├── profiles/                 # User profile storage
├── controller_config.json    # Runtime settings
└── requirements.txt
```

## Conventions

- **UI Scaling**: Use `controller.scaled(value)` for DPI-aware sizing
- **Code Style**: PEP 8 with type hints
- **Settings**: All persist to JSON; per-profile for sensitivity/buttons
- **Profiles**: JSON files in user data directory (`%APPDATA%\ProjectNimbus\profiles\`)

## Layout Types

| Layout | Use Case |
|--------|----------|
| `flight_sim` | Dual joysticks + throttle/rudder |
| `xbox` | Standard Xbox gamepad |
| `adaptive` | Accessibility-focused, larger buttons |

## Things to Avoid

- Do not modify `src/legacy/` — kept for reference only
- Do not use `src/qt_main.py` directly — use `run.py`
- Avoid hardcoding sizes — use `controller.scaled()` for scaling

## Owner Context

- **Accessibility-first**: Design decisions prioritize users with mobility limitations
- **Mouse-first input model**: Core philosophy is mouse-driven joystick control
- **Qt Quick (QML) is the primary UI**: The pygame UI is legacy/deprecated
