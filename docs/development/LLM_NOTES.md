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
| `src/borderless.py` | Borderless gaming + ClipCursor release (Windows, pure ctypes) |
| `qml/Main.qml` | Main window, menus, layout loader |
| `qml/layouts/` | Layout QML files (CustomLayout is default; FlightSim/Xbox/Adaptive are legacy) |
| `qml/components/` | Reusable QML controls (Joystick, Sliders, DraggableWidget, WidgetPalette, BorderlessGamingDialog) |
| `profiles/` | Bundled profile JSON files (only `adaptive_platform_2.json` now) |

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
│   └── adaptive_platform_2.json  # ★ Only bundled profile (default, custom layout)
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
| `custom` | `CustomLayout.qml` | **★ Default — modular drag-and-drop canvas** |
| `flight_sim` | `FlightSimLayout.qml` | Dual joysticks + throttle/rudder (legacy) |
| `xbox` | `XboxLayout.qml` | Standard Xbox gamepad (legacy) |
| `adaptive` | `AdaptiveLayout.qml` | Accessibility-focused fixed layout (legacy) |

## Custom Layout System (Adaptive Platform 2)

The `custom` layout type is the modular controller builder. Key concepts:

### Widget Schema (stored in profile JSON under `custom_layout.widgets[]`)
- **Common fields**: `id`, `type`, `x`, `y`, `width`, `height`, `label`
- **Joystick**: `mapping.axis_x`, `mapping.axis_y` (e.g. `"x"/"y"` or `"rx"/"ry"`), `triple_click_enabled`, `auto_center`, `sensitivity`, `dead_zone`, `extremity_dead_zone`, `macro_mode`, `macro_config`
- **Button**: `button_id` (1-128), `color`, `shape` (`"circle"/"rounded"/"square"`), `toggle_mode`
- **Slider**: `orientation` (`"horizontal"`/`"vertical"`), `mapping.axis`, `snap_mode` (`"none"`/`"left"`/`"center"`), `click_mode` (`"jump"`/`"relative"`), `sensitivity`, `dead_zone`, `extremity_dead_zone`
- **D-Pad**: `mapping.up`, `mapping.down`, `mapping.left`, `mapping.right` (button IDs)
- **Wheel**: `mapping.axis`, `sensitivity`, `dead_zone`, `extremity_dead_zone`

### Macro Joystick Mode (v1.3.0)
Converts a joystick into a macro input device where each direction triggers buttons, axes, or turbo actions instead of analog stick output.

#### Enabling Macro Mode
1. Double-click joystick widget → Enable "Macro Mode" toggle
2. Click "Edit Macro Mappings..." to open the visual zone editor
3. Configure each zone's action and apply

#### Macro Config Schema
```json
{
  "macro_mode": true,
  "macro_config": {
    "zones": {
      "north": { "action": "button", "buttons": [4] },
      "east": { "action": "multi_button", "buttons": [5, 6] },
      "south": { "action": "turbo", "buttons": [1], "turbo_hz": 10 },
      "west": { "action": "axis", "axis": "z", "axis_value": 1.0 },
      "center": { "action": "button", "buttons": [9] },
      "northeast": { "action": "none" },
      "southeast": { "action": "none" },
      "southwest": { "action": "none" },
      "northwest": { "action": "none" }
    },
    "deadzone_percent": 30,
    "diagonal_mode": "8-way"
  }
}
```

#### Action Types
| Action | Description |
|--------|-------------|
| `none` | No action (zone disabled) |
| `button` | Press single button when in zone |
| `multi_button` | Press multiple buttons simultaneously |
| `axis` | Set axis to configured value (e.g., full throttle) |
| `turbo` | Auto-fire button at configurable rate (1-30 Hz) |

#### Zone Detection
- **Deadzone**: Center area (configurable 10-50%) triggers `center` zone
- **8-way mode**: 8 directional zones at 45° each (N, NE, E, SE, S, SW, W, NW)
- **4-way mode**: 4 cardinal zones at 90° each (N, E, S, W)
- Angle calculated from joystick position using `atan2(-ny, nx)`

#### Visual Indicators
- Purple border when macro mode enabled
- "MACRO" label at top of joystick
- Zone divider lines overlay
- Current zone arrow indicator (↑, →, ↓, ←, ↗, ↘, ↙, ↖, ●)

#### Quick Presets
The macro editor includes preset buttons:
- **ABXY**: Maps N/E/S/W to Y/B/A/X buttons
- **D-Pad**: Maps to D-pad button IDs (13-16)
- **Triggers**: Maps N/S to LT/RT axes
- **Shoulders**: Maps W/E/Center to LB/RB/LS buttons
- **Clear All**: Resets all zones to "none"

#### Implementation Files
- `qml/components/MacroEditorDialog.qml` — Visual zone editor dialog
- `qml/components/DraggableWidget.qml` — Zone detection and action execution
- `qml/layouts/CustomLayout.qml` — Macro mode UI in config dialog

### Edit Mode
- Toggle via Settings → Edit Layout menu item (custom layout only)
- **Drag** widgets to reposition (snaps to grid)
- **Corner handle** to resize
- **×** button to delete
- **Double-click** to open scrollable config dialog
- **Widget Palette** — pop-out window with draggable title bar (stays on top, never overlaps canvas)
- Auto-saves on every change (move, resize, config, add, delete)

### Widget Config Dialog
- **All types**: label editing
- **Button**: button ID, color, shape, toggle/momentary switch
- **Joystick**: axis pair dropdown, triple-click lock toggle, auto-return to center toggle
- **Slider**: axis dropdown, snap mode (3 options), click mode (jump/relative), orientation (read-only, set by palette choice)
- **Wheel**: axis dropdown
- **Axis widgets** (joystick/slider/wheel): sensitivity (0-100%), deadzone (0-100%), extremity deadzone (0-100%), live response curve preview
- Sensitivity formula matches `config.py:apply_joystick_dialog_curve()` exactly

### Mouse Lock (Joystick)
- **Triple-click** a joystick to lock — mouse controls it from anywhere on the canvas via hover
- **Triple-click again** to unlock — joystick returns to center (0,0)
- Implemented via a full-canvas `MouseArea` overlay with `hoverEnabled: true` and `cursorShape: Qt.BlankCursor`
- `DraggableWidget` exposes `updateJoystickPosition()` and `triggerTripleClick()` for the overlay

#### FPS-Style Delta Tracking (v1.2.1 — Wheelchair Joystick Breakthrough)
When a joystick is locked, the system uses FPS-style delta tracking instead of absolute position mapping:
1. **On lock**: cursor hidden (`Qt.BlankCursor`), warped to joystick center via `QCursor.setPos()`, confined to window via `ClipCursor`
2. **On every mouse move**: compute pixel offset from joystick center, scale by `lockSensitivity` multiplier (1-20x), clamp to -1..1, update joystick, then **warp cursor back to center**
3. **Warp-back detection**: events where cursor is within 3px of center are treated as our own warp and skipped
4. **On unlock**: cursor reappears, confinement released

**Why this works for wheelchair joysticks**: A wheelchair joystick controls cursor velocity (not position). Full physical deflection → constant cursor speed → constant pixel delta from center each frame → constant virtual joystick deflection. Releasing the physical joystick → cursor stops → no delta → auto-return timer fires → virtual joystick snaps to center.

**Key DPI fix**: `QCursor.setPos()` (Qt, DPI-aware) must be used instead of `SetCursorPos()` (Win32, physical pixels). Without this, on scaled displays (125%, 150%), the warp target is consistently up-left of the actual center.

#### Per-Widget Lock Settings
- `auto_center` (bool): enable auto-return to center when mouse stops
- `auto_center_delay` (1-10ms): how long mouse must be idle before return
- `lock_sensitivity` (1-10 UI, actual multiplier = value × 2): higher = less physical movement needed for full deflection
- `tremor_filter` (0-10): EMA smoothing strength. 0 = off (raw input), 10 = heavy smoothing. Alpha = 1.0 - (value/10) × 0.9. Designed for wheelchair joysticks with involuntary tremor.
- At delay ≤ 0: instant snap to center (no animation). Otherwise: OutCubic easing, duration scales with delay

#### Cursor Confinement
- `controller.clipCursorToWindow()` / `controller.unclipCursor()` — Windows `ClipCursor` API keeps invisible cursor in app window so hover events keep firing
- `controller.setCursorPos(x, y)` — `QCursor.setPos()` for DPI-correct cursor warping

### Splash Screen (v1.2.1)
- `qt_qml_app.py:_create_splash()` paints logo + version + tagline on a dark QPixmap
- Shown before heavy init (ControllerConfig, ControllerBridge), closed after QML loads
- Uses `QSplashScreen.showMessage()` for progress updates between init steps

### Bridge Slots for Custom Layout
- `getCustomLayout()` → JSON string of widgets
- `saveCustomLayout(json, gridSnap, showGrid)`
- `saveCustomLayoutAs(name)` → duplicate profile with new name
- `getCustomLayoutGridSnap()`, `getCustomLayoutShowGrid()`

### Hardware Limits
- **vJoy**: 8 axes (X,Y,Z,RX,RY,RZ,SL0,SL1) → max 4 joysticks, 128 buttons
- **ViGEm**: 2 sticks + 2 triggers + 14 buttons (Xbox 360 hard limit)
- See `docs/architecture/VDROID_DRIVER_BRAINSTORM.md` for plans to exceed these limits

### Known Bug Fixes (for future reference)
- **Palette overlap**: Sidebar palette covered canvas widgets → fixed by making it a pop-out `Window` with `Qt.FramelessWindowHint` + custom drag title bar
- **OS title bar not showing**: `Qt.Window` and `Qt.Tool` flags didn't produce a movable window in PySide6 QML → solved with frameless window + custom MouseArea drag
- **Joystick edge-sticking**: `hoverEnabled` hover events stop when mouse leaves widget bounds → solved with full-canvas overlay `MouseArea` that maps global coords via `mapToItem()`
- **Joystick not returning to center on unlock**: `onMouseLockedChanged` now resets `xValue`/`yValue` to 0 and sends zero to controller
- **Sensitivity curve mismatch**: Widget `_applyCurve()` used different formula than Settings menu → aligned to use identical `apply_joystick_dialog_curve()` math with percentage-based params

## Borderless Gaming System

`src/borderless.py` — pure `ctypes`, zero extra dependencies:

- **`enumerate_windows(include_invisible=False)`** → `list[WindowInfo]` — all visible top-level windows (filters system/Nimbus windows)
- **`make_borderless(hwnd, x, y, width, height)`** → `bool` — strips `WS_CAPTION`, `WS_THICKFRAME`, `WS_BORDER`, `WS_DLGFRAME`; saves original style; resizes to `GetMonitorInfo` work area
- **`restore_window(hwnd)`** → `bool` — restores saved style + original rect
- **`is_borderless(hwnd)`** → `bool` — checks if hwnd has been made borderless by us
- **`start_cursor_release(interval_ms, callback)`** — starts a daemon thread that calls `ClipCursor(NULL)` every `interval_ms`
- **`stop_cursor_release()`** — stops the thread
- **`is_cursor_release_active()`** → `bool`
- **`get_clip_cursor_rect()`** → `tuple[int,int,int,int] | None` — current ClipCursor rect
- **`auto_detect_game()`** → `tuple[WindowInfo, GameCompatEntry] | None` — finds a running window matching the compat database
- **`get_compatible_games()`** → `list[GameCompatEntry]` — full compat database
- **`GameCompatEntry`** dataclass fields: `name`, `status` (verified/likely/partial/incompatible), `input_method`, `notes`, `window_title_hint`, `needs_borderless`, `needs_cursor_release`, `recommended_interval_ms`

**Bridge slots** (all in `src/bridge.py`):
`isBorderlessAvailable`, `getRunningWindows`, `getGameCompatibility`, `autoDetectGame`, `makeGameBorderless`, `restoreGameWindow`, `isGameBorderless`, `startCursorRelease`, `stopCursorRelease`, `isCursorReleaseActive`, `getClipCursorRect`, `applyBorderlessAndRelease`, `restoreAndStopRelease`

**Signals**: `cursorReleaseChanged(bool)`, `borderlessModeChanged(int, bool)`

**UI**: `qml/components/BorderlessGamingDialog.qml` — opened via **View → Borderless Gaming...**
- Tab 0: Game Setup — auto-detect, window picker, one-click apply, release speed slider
- Tab 1: Compatibility — filterable list by status with notes

**Game compatibility docs**: `docs/GAME_COMPATIBILITY.md`

---

## Conventions

- **UI Scaling**: Use `controller.scaled(value)` for DPI-aware sizing in fixed layouts
- **Code Style**: PEP 8 with type hints
- **Settings**: All persist to JSON; per-profile for sensitivity/buttons/layout
- **Profiles**: JSON files in user data directory (`%APPDATA%\ProjectNimbus\profiles\`)
- **Default profile**: `adaptive_platform_2` (custom layout) — only bundled profile
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
- **Active branch**: `feature/borderless-mouse-integration` (borderless gaming & mouse capture)
- **Version**: 1.3.2 — see `CHANGELOG.md` for history

## Build & Release

> **Full guide**: See [../setup/PACKAGING.md](../setup/PACKAGING.md) for comprehensive build/release documentation.

### Quick Build
```powershell
# 1. Build executable
venv\Scripts\pyinstaller.exe build_tools\Project-Nimbus.spec --noconfirm

# 2. Build installer
& "C:\Program Files (x86)\NSIS\makensis.exe" build_tools\installer.nsi

# 3. Sign both
cmd /c build_tools\sign_exe.bat
```

### Version Bump Locations
When releasing a new version, update these files:
- `src/__init__.py` — `__version__`
- `build_tools/Project-Nimbus.spec` — `VERSION`
- `build_tools/installer.nsi` — `PRODUCT_VERSION`
- `build_tools/sign_exe.bat` — `INSTALLER_PATH`
- `build_tools/version_info.txt` — `filevers` and `prodvers`
- `CHANGELOG.md` — Release notes

### Installer Features (v1.2.1)
- **UAC admin prompt** — `RequestExecutionLevel admin`
- **Running app detection** — Checks if app is running, offers to close
- **Previous version detection** — Checks BOTH HKCU and HKLM registries
- **Shortcut options page** — Custom page with Desktop/Start Menu checkboxes
- **BringToFront** — Ensures installer visible after UAC elevation

### UIAccess=true
The manifest (`build_tools/Project-Nimbus.manifest`) requests `uiAccess="true"` which enables on-screen keyboard parity. Requirements:
- Executable must be **EV code-signed**
- Must be installed to a **trusted location** (e.g. `C:\Program Files\` or `%LOCALAPPDATA%\Programs\Project Nimbus\`)
- The NSIS installer handles trusted location placement automatically

## Quick Reference for AI Assistants

| Task | Start Here |
|------|------------|
| Understanding the app | `README.md`, then `docs/architecture/architecture.md` |
| Project structure | `DIRECTORY.md` (root) |
| Making UI changes | `qml/Main.qml`, `qml/layouts/CustomLayout.qml` |
| Adding QML↔Python features | `src/bridge.py` (add @Slot methods) |
| Changing settings/profiles | `src/config.py` |
| Building releases | `docs/setup/PACKAGING.md` |
| Adding new widget types | `docs/development/INTEGRATION_GUIDE.md` |
