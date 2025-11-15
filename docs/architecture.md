# Project Nimbus Architecture

## High-Level Overview

Project Nimbus is a Python-based virtual controller that converts mouse/GUI input into joystick commands via the **vJoy** driver. The modern UI is implemented with **Qt Quick (PySide6 + QML)**, backed by a Python core that manages configuration, curves, and vJoy I/O.

At a high level:
- The user interacts with a **QML UI** (joysticks, sliders, buttons).
- QML calls into a **Python bridge** (`ControllerBridge`) exposed as `controller`.
- The bridge uses **`ControllerConfig`** to read/write settings and apply curves.
- The bridge talks to **`VJoyInterface`** to send axis/button updates to the vJoy driver.

## Launch Flow

### 1. Top-Level Launcher (`run.py`)

- Performs Python version checks and virtual environment setup.
- Ensures dependencies (PySide6, vJoy bindings, etc.) are installed.
- Launches the QML application module:
  - `python run.py` → runs `src.qt_qml_app` in the venv.

For bundled executables, `build_tools/launcher.py` is used instead (no console / input prompts) and calls the same QML entry.

### 2. QML Application Entry (`src/qt_qml_app.py`)

Responsibilities:
- Create `QApplication` and `QQmlApplicationEngine`.
- Instantiate:
  - `ControllerConfig` – configuration manager
  - `ControllerBridge` – QML↔Python bridge
- Expose objects to QML:
  - `controller` → `ControllerBridge` instance
  - `config` → `ControllerConfig` instance
- Load `qml/Main.qml` and start the Qt event loop.

### 3. QML UI (`qml/`)

- `qml/Main.qml` defines the main window, top menu bar, and overall layout.
- Reusable controls live under `qml/components/`, e.g.:
  - `Joystick.qml`
  - `SliderVertical.qml` (Throttle)
  - `SliderHorizontal.qml` (Rudder)

QML controls call into the Python bridge using slots/properties such as:
- `controller.setLeftStick(x, y)`
- `controller.setRightStick(x, y)`
- `controller.setThrottle(value)`
- `controller.setRudder(value)`
- `controller.setButton(id, pressed)`
- `controller.setScaleFactor(scale)` and `controller.scaled(base)`

## Core Python Components

### `ControllerConfig` (`src/config.py`)

Configuration manager responsible for:
- Loading defaults and merging with `controller_config.json`.
- Providing `get`/`set` helpers with dot-notation paths.
- Persisting settings to disk (`save_config`).
- Validating configuration (joystick, vJoy, safety, UI scale).
- UI scaling utilities:
  - `get_scaled_value`, `get_scaled_int`
  - `set_scale_factor` (updates window/joystick sizes and font size).
- Input processing:
  - Joystick and rudder sensitivity curves
  - Deadzone/extremity handling
  - Conversion from normalized values (−1..1) to vJoy range.

### `VJoyInterface` (`src/vjoy_interface.py`)

Wrapper around the vJoy driver (via `pyvjoy`):
- Initializes and validates the vJoy device (ID, status, axis capabilities).
- Maintains current axis values and update rate constraints.
- Provides APIs:
  - `update_axis(axis, value)` – update a single axis in −1..1
  - `update_joystick(left_x, left_y, right_x, right_y)`
  - `set_button(button_id, pressed)`
  - `get_status()` – diagnostic information
- Handles:
  - Mapping logical axes (`x`, `y`, `z`, `rx`, `ry`, `rz`) to vJoy constants/IDs
  - Centering axes on initialization/reset
  - Optional failsafe / emergency stop behavior

### `ControllerBridge` (`src/bridge.py`)

Qt `QObject` exposed to QML as `controller`:
- Owns:
  - `ControllerConfig` (injected from `qt_qml_app.py`)
  - `VJoyInterface` instance
- Manages high-level state:
  - `scaleFactor` property (with `scaleFactorChanged` signal)
  - `debugBorders` property
  - Button-mode versioning (`buttonsVersion`) so QML can refresh toggles
- Provides QML-callable slots:
  - Axis methods: `setLeftStick`, `setRightStick`, `setThrottle`, `setRudder`
  - Button control: `setButton`
  - Scaling helpers: `setScaleFactor`, `scaled(base)`
  - Settings dialogs: `openJoystickSettings`, `openRudderSettings`, `openButtonSettings`, `openAxisMapping`
- Implements axis smoothing using a `QTimer` that interpolates toward target values before sending to vJoy.

## Settings & Dialogs (`src/qt_dialogs.py`)

Qt Widgets-based dialogs used by the QML/bridge layer:
- **Joystick Settings**: sensitivity, deadzone, extremity deadzone with live curve preview.
- **Rudder Settings**: independent tuning for rudder axis.
- **Button Settings**: per-button toggle vs momentary modes (1–8, ARM, RTH).
- **Axis Mapping**: maps logical UI axes (left/right sticks, throttle, rudder) to vJoy axes.

These dialogs read/write values through `ControllerConfig`, ensuring that QML, Qt Widgets, and runtime behavior all share the same configuration.

## Alternative Shells & Legacy Code

### Qt Widgets Shell (`src/qt_main.py`)

- Alternative (non-QML) Qt Widgets-based interface.
- Uses the same `ControllerConfig` and `VJoyInterface` backend.
- Not the default entry point; intended for experimentation and layout prototyping.

### Legacy Pygame UI (`src/legacy/`)

- Contains the original pygame-based UI and dialog implementations.
- Kept for reference only; not used by `run.py` or the QML application.

## Build & Packaging

- **Source-based runs**: `python run.py` (sets up venv, dependencies, and launches QML app).
- **Executable builds**:
  - PyInstaller spec and scripts under `build_tools/`.
  - `build_tools/launcher.py` serves as a GUI-friendly entry point for the bundled EXE.

For detailed build steps, see `build_tools/BUILD_EXECUTABLE.md`.
