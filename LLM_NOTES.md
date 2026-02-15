# LLM Notes

Quick reference for AI assistants working on Project Nimbus.

## Project Context

**Project Nimbus** is a modular virtual controller interface that transforms mouse input into virtual joystick commands via vJoy or ViGEm (Xbox emulation). It's designed as a **free, open-source software Xbox Adaptive Controller** — enabling users with physical disabilities to build custom controller layouts without needing expensive hardware.

**Primary use cases:**
- Adaptive gaming (mouse-first joystick control)
- UAV/rover control via Mission Planner
- Steam Input integration for XInput games
- Assistive technology development
- Custom controller building for users with mobility limitations

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| UI Framework | Qt Quick (PySide6 QML) |
| Virtual Controller | vJoy (DirectInput, 8 axes, 128 buttons) |
| Xbox Emulation | ViGEm / vgamepad (XInput, 2 sticks + 2 triggers + 14 buttons) |
| Config | JSON (profiles + `controller_config.json`) |
| Build | PyInstaller |

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Entry point (launches QML UI via venv) |
| `src/qt_qml_app.py` | QML application bootstrap |
| `src/bridge.py` | Python↔QML bridge (`ControllerBridge`) |
| `src/config.py` | Configuration & profile management |
| `src/qt_dialogs.py` | Qt Widgets settings dialogs |
| `src/vjoy_interface.py` | vJoy driver communication (8 axes: X,Y,Z,RX,RY,RZ,SL0,SL1) |
| `src/vigem_interface.py` | ViGEm Xbox 360 controller emulation |
| `src/window_utils.py` | Game Focus Mode (Windows API) |
| `qml/Main.qml` | Main window, menus, layout loader |
| `qml/layouts/` | Layout QML files (FlightSim, Xbox, Adaptive, **Custom**) |
| `qml/components/` | Reusable QML controls (Joystick, Sliders, DraggableWidget, WidgetPalette) |
| `profiles/` | Bundled profile JSON files |

## Project Structure

```
Project-Nimbus/
├── run.py                        # Launcher (Qt Quick UI default)
├── run.bat                       # Windows batch launcher
├── requirements.txt              # Python dependencies
├── controller_config.json        # Runtime settings (auto-generated)
├── qml/
│   ├── Main.qml                  # Main window + layout loader
│   ├── layouts/
│   │   ├── FlightSimLayout.qml   # Dual joysticks + throttle/rudder
│   │   ├── XboxLayout.qml        # Standard Xbox gamepad
│   │   ├── AdaptiveLayout.qml    # Accessibility-focused fixed layout
│   │   └── CustomLayout.qml      # ★ Modular drag-and-drop canvas
│   └── components/
│       ├── Joystick.qml          # Virtual joystick control
│       ├── DraggableWidget.qml   # ★ Drag/resize wrapper for any widget
│       ├── WidgetPalette.qml     # ★ Sidebar toolbar for adding widgets
│       ├── SliderVertical.qml
│       ├── SliderHorizontal.qml
│       └── NumberPad.qml
├── src/
│   ├── qt_qml_app.py             # QML app entry
│   ├── bridge.py                 # ControllerBridge (Python↔QML)
│   ├── config.py                 # Config + profile management
│   ├── qt_dialogs.py             # Settings dialogs (Axis, Button, Slider)
│   ├── vjoy_interface.py         # vJoy driver interface
│   ├── vigem_interface.py        # ViGEm Xbox controller emulation
│   ├── window_utils.py           # Game Focus Mode (Windows)
│   ├── qt_main.py                # Alt Qt Widgets shell (not default)
│   ├── qt_widgets.py             # Qt Widgets UI components
│   └── legacy/                   # Old pygame UI (reference only)
├── profiles/
│   ├── flight_simulator.json
│   ├── xbox_controller.json
│   ├── adaptive_platform_1.json
│   └── adaptive_platform_2.json  # ★ Modular custom layout profile
├── docs/                         # Documentation
├── build_tools/                  # PyInstaller build system
├── research/                     # Research notes
├── tests/                        # Test files
└── screenshots/                  # UI screenshots
```

## Layout Types

| Layout | QML File | Use Case |
|--------|----------|----------|
| `flight_sim` | `FlightSimLayout.qml` | Dual joysticks + throttle/rudder |
| `xbox` | `XboxLayout.qml` | Standard Xbox gamepad |
| `adaptive` | `AdaptiveLayout.qml` | Accessibility-focused, fixed layout |
| `custom` | `CustomLayout.qml` | **★ Modular drag-and-drop canvas** |

## Custom Layout System (Adaptive Platform 2)

The `custom` layout type is the new modular controller builder. Key concepts:

### Widget Schema (stored in profile JSON under `custom_layout.widgets[]`)
- **Common fields**: `id`, `type`, `x`, `y`, `width`, `height`, `label`
- **Joystick**: `mapping.axis_x`, `mapping.axis_y` (e.g. `"x"/"y"` or `"rx"/"ry"`)
- **Button**: `button_id` (1-128), `color`, `shape` (`"circle"/"rounded"/"square"`)
- **Slider**: `orientation`, `mapping.axis`, `center_return` (spring-to-center option)

### Edit Mode
- Toggle via "Edit Layout" button (bottom-right)
- **Drag** widgets to reposition (snaps to grid)
- **Corner handle** to resize
- **×** button to delete
- **Double-click** to open config dialog (label, axis mapping, button ID, etc.)
- **Widget Palette** sidebar to add new joystick/button/slider widgets
- Auto-saves when exiting edit mode

### Bridge Slots for Custom Layout
- `getCustomLayout()` → JSON string of widgets
- `saveCustomLayout(json, gridSnap, showGrid)`
- `getCustomLayoutGridSnap()`, `getCustomLayoutShowGrid()`

### Hardware Limits
- **vJoy**: 8 axes (X,Y,Z,RX,RY,RZ,SL0,SL1) → max 4 joysticks, 128 buttons
- **ViGEm**: 2 sticks + 2 triggers + 14 buttons (Xbox 360 hard limit)

## Conventions

- **UI Scaling**: Use `controller.scaled(value)` for DPI-aware sizing in fixed layouts
- **Code Style**: PEP 8 with type hints
- **Settings**: All persist to JSON; per-profile for sensitivity/buttons/layout
- **Profiles**: JSON files in user data directory (`%APPDATA%\ProjectNimbus\profiles\`)
- **Controller Interface**: Bridge auto-selects vJoy or ViGEm based on profile layout type

## Things to Avoid

- Do not modify `src/legacy/` — kept for reference only
- Do not use `src/qt_main.py` directly — use `run.py`
- Avoid hardcoding sizes — use `controller.scaled()` for scaling in fixed layouts
- Do not hardcode button IDs in new widgets — use smart auto-assignment

## Owner Context

- **Accessibility-first**: Design decisions prioritize users with physical disabilities
- **Mouse-first input model**: Core philosophy is mouse-driven joystick control
- **Free & open**: Goal is a modular software Xbox Adaptive Controller where everything is free
- **Qt Quick (QML) is the primary UI**: The pygame UI is legacy/deprecated
- **EV signing certificate available**: For UIAccess=true on-screen keyboard parity (future)
- **Active branch**: `feature/adaptive-platform-2` for the modular layout system
