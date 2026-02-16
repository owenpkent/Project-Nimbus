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
├── docs/                         # Documentation + screenshots + video
│   ├── architecture.md
│   ├── LLM_NOTES.md             # ★ This file
│   ├── screenshots/
│   └── video/
├── build_tools/                  # Build, sign, and install
│   ├── Project-Nimbus.spec       # PyInstaller spec
│   ├── Project-Nimbus.manifest   # UIAccess=true manifest
│   ├── Project-Nimbus.ico        # Application icon
│   ├── installer.nsi             # NSIS installer script
│   ├── build_exe.bat             # Build executable + installer
│   ├── sign_exe.bat              # EV code signing
│   ├── launcher.py               # PyInstaller entry point
│   └── version_info.txt          # Windows version resource
├── research/                     # Research notes
├── tests/                        # Test files
├── CHANGELOG.md                  # Version history
└── TODO.md                       # Task tracking
```

## Layout Types

| Layout | QML File | Use Case |
|--------|----------|----------|
| `flight_sim` | `FlightSimLayout.qml` | Dual joysticks + throttle/rudder |
| `xbox` | `XboxLayout.qml` | Standard Xbox gamepad |
| `adaptive` | `AdaptiveLayout.qml` | Accessibility-focused, fixed layout |
| `custom` | `CustomLayout.qml` | **★ Modular drag-and-drop canvas** |

## Custom Layout System (Adaptive Platform 2)

The `custom` layout type is the modular controller builder. Key concepts:

### Widget Schema (stored in profile JSON under `custom_layout.widgets[]`)
- **Common fields**: `id`, `type`, `x`, `y`, `width`, `height`, `label`
- **Joystick**: `mapping.axis_x`, `mapping.axis_y` (e.g. `"x"/"y"` or `"rx"/"ry"`), `triple_click_enabled`, `sensitivity`, `dead_zone`, `extremity_dead_zone`
- **Button**: `button_id` (1-128), `color`, `shape` (`"circle"/"rounded"/"square"`), `toggle_mode`
- **Slider**: `orientation` (`"horizontal"`/`"vertical"`), `mapping.axis`, `snap_mode` (`"none"`/`"left"`/`"center"`), `click_mode` (`"jump"`/`"relative"`), `sensitivity`, `dead_zone`, `extremity_dead_zone`
- **D-Pad**: `mapping.up`, `mapping.down`, `mapping.left`, `mapping.right` (button IDs)
- **Wheel**: `mapping.axis`, `sensitivity`, `dead_zone`, `extremity_dead_zone`

### Edit Mode
- Toggle via "Edit Layout" button (bottom-right)
- **Drag** widgets to reposition (snaps to grid)
- **Corner handle** to resize
- **×** button to delete
- **Double-click** to open scrollable config dialog
- **Widget Palette** — pop-out window with draggable title bar (stays on top, never overlaps canvas)
- Auto-saves on every change (move, resize, config, add, delete)

### Widget Config Dialog
- **All types**: label editing
- **Button**: button ID, color, shape, toggle/momentary switch
- **Joystick**: axis pair dropdown, triple-click lock toggle
- **Slider**: axis dropdown, snap mode (3 options), click mode (jump/relative), orientation (read-only, set by palette choice)
- **Wheel**: axis dropdown
- **Axis widgets** (joystick/slider/wheel): sensitivity (0-100%), deadzone (0-100%), extremity deadzone (0-100%), live response curve preview
- Sensitivity formula matches `config.py:apply_joystick_dialog_curve()` exactly

### Mouse Lock (Joystick)
- **Triple-click** a joystick to lock — mouse controls it from anywhere on the canvas via hover
- **Triple-click again** to unlock — joystick returns to center (0,0)
- Implemented via a full-canvas `MouseArea` overlay with `hoverEnabled: true`
- `DraggableWidget` exposes `updateJoystickPosition()` and `triggerTripleClick()` for the overlay

### Bridge Slots for Custom Layout
- `getCustomLayout()` → JSON string of widgets
- `saveCustomLayout(json, gridSnap, showGrid)`
- `saveCustomLayoutAs(name)` → duplicate profile with new name
- `getCustomLayoutGridSnap()`, `getCustomLayoutShowGrid()`

### Hardware Limits
- **vJoy**: 8 axes (X,Y,Z,RX,RY,RZ,SL0,SL1) → max 4 joysticks, 128 buttons
- **ViGEm**: 2 sticks + 2 triggers + 14 buttons (Xbox 360 hard limit)
- See `docs/VDROID_DRIVER_BRAINSTORM.md` for plans to exceed these limits

### Known Bug Fixes (for future reference)
- **Palette overlap**: Sidebar palette covered canvas widgets → fixed by making it a pop-out `Window` with `Qt.FramelessWindowHint` + custom drag title bar
- **OS title bar not showing**: `Qt.Window` and `Qt.Tool` flags didn't produce a movable window in PySide6 QML → solved with frameless window + custom MouseArea drag
- **Joystick edge-sticking**: `hoverEnabled` hover events stop when mouse leaves widget bounds → solved with full-canvas overlay `MouseArea` that maps global coords via `mapToItem()`
- **Joystick not returning to center on unlock**: `onMouseLockedChanged` now resets `xValue`/`yValue` to 0 and sends zero to controller
- **Sensitivity curve mismatch**: Widget `_applyCurve()` used different formula than Settings menu → aligned to use identical `apply_joystick_dialog_curve()` math with percentage-based params

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
- **EV signing certificate available**: UIAccess=true manifest is now included in the build
- **Active branch**: `feature/adaptive-platform-2` for the modular layout system
- **Version**: 1.2.0 — see `CHANGELOG.md` for history

## Build & Release

### Quick Build
```batch
cd build_tools
build_exe.bat        # Builds exe + installer (if NSIS available)
sign_exe.bat         # Signs exe + installer with EV cert
```

### Release Checklist
1. Update version in `src/__init__.py`, `build_tools/version_info.txt`, `build_tools/Project-Nimbus.spec`
2. Update `CHANGELOG.md`
3. Run `build_tools/build_exe.bat`
4. Run `build_tools/sign_exe.bat` (hardware token must be connected)
5. Test on clean Windows machine
6. Create GitHub release, attach `dist/Project-Nimbus-Setup-X.Y.Z.exe`
7. Git tag: `git tag v1.2.0`

### UIAccess=true
The manifest (`build_tools/Project-Nimbus.manifest`) requests `uiAccess="true"` which enables on-screen keyboard parity. Requirements:
- Executable must be **EV code-signed**
- Must be installed to a **trusted location** (e.g. `C:\Program Files\` or `%LOCALAPPDATA%\Project Nimbus\`)
- The NSIS installer handles trusted location placement automatically
