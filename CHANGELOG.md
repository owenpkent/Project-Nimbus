# Project Nimbus Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] — 2026-03-17

### Added
- **QML/PySide6 UI** — Complete rewrite of the user interface using Qt Quick (QML) with a dark-themed, scalable layout that replaces the legacy Pygame canvas
- **Game Focus Mode** — View menu toggle that prevents Project Nimbus from stealing focus from games; automatically restores focus to the game after each interaction using Windows thread-input attachment
- **Cursor management for wheelchair joystick** — `ClipCursor` locking to constrain the physical cursor to the joystick widget area during locked mode, with `unclipCursor` on release
- **ViGEm auto-selection** — Automatically uses Xbox 360 (ViGEm/XInput) emulation for xbox/adaptive/custom profiles and vJoy (DirectInput) for flight sim; falls back gracefully if ViGEm is unavailable
- **Smooth axis interpolation** — Configurable EMA-based smoothing timer applies per-axis target tracking at the vJoy update rate (default 60 Hz, configurable up to 240 Hz)
- **Profile system overhaul** — Profiles stored in `%APPDATA%\ProjectNimbus`; full create, save, save-as, duplicate, delete, reset-to-defaults, and open-folder actions accessible from the File menu
- **About dialog** — Version, description, copyright, and license info accessible from Help menu
- **Loading splash screen** — Dark-themed splash with logo, version, and progress messages on startup (previously undocumented)

### Changed
- **Default profiles refined** — Flight Simulator, Xbox Controller, Adaptive Platform 1, and Adaptive Platform 2 profiles cleaned up with consistent axis mappings, button labels, and accessibility options
- **PyInstaller build tooling** — Updated to PyInstaller 6.19 with versioned distribution filenames (`Project-Nimbus-1.4.0.exe`, `Project-Nimbus-Setup-1.4.0.exe`)

---

## [1.3.1] — 2026-03-03

### Changed
- **Versioned distribution filenames** — Executable and installer now include the version number in their filename (`Project-Nimbus-1.3.1.exe`, `Project-Nimbus-Setup-1.3.1.exe`) for clearer release management
- **Code-signed release** — EV certificate signed with SHA-256 timestamping via DigiCert

---

## [1.3.0] — 2026-01-20

### Added
- **Macro Joystick Mode** — Convert any joystick widget into a macro trigger: each of 8 directional zones (plus center) maps to a configurable button press, axis value, or turbo action
- **Visual zone editor** — 8-zone + center joystick diagram in the per-widget config dialog for visually assigning actions to each direction
- **Quick presets** — One-click presets in the macro editor: ABXY face buttons, D-Pad directions, Triggers, and Shoulder buttons
- **Turbo mode** — Auto-fire any button at a configurable rate (1–30 Hz) from within the macro zone editor
- **vJoy auto-detection** — Detects whether vJoy is installed at startup and shows a guided prompt if it is missing

---

## [1.2.1] — 2025-02-15

### Added
- **Wheelchair joystick support (FPS-style delta tracking)** — When a joystick is locked, the cursor is hidden and continuously warped back to the joystick center. Each mouse movement is treated as a delta offset, scaled by a configurable sensitivity multiplier. This maps physical wheelchair joystick deflection directly to virtual joystick deflection.
- **Tremor Filter** — Per-joystick EMA smoothing (0-10) to reduce jittery input from wheelchair joysticks with involuntary tremor
- **Lock Sensitivity slider** — Per-joystick sensitivity (1-10, default 4) controlling how much physical mouse movement is needed for full virtual deflection
- **Auto-return to center** — Per-joystick toggle; when locked mode mouse stops, virtual joystick snaps back to center. Configurable delay (1-10ms) for fine-tuning response feel.
- **Copy sensitivity from dropdown** — Per-widget axis settings can copy sensitivity/deadzone/extremity from other axis widgets
- **Help menu documentation** — In-app "Getting Started" guide and "Feature Guide" accessible via Help menu with comprehensive wheelchair joystick setup instructions
- **Loading splash screen** — Dark-themed splash screen with logo, version, and progress messages shown during startup
- **Scrollbars on all settings dialogs** — QML config dialog, Button Settings, and Axis Settings all have styled scrollbars
- **DPI-aware cursor positioning** — Uses Qt's `QCursor.setPos()` instead of Windows `SetCursorPos` for correct behavior on scaled displays

### Changed
- **Edit Layout is a top-level menu** — Dedicated "Edit Layout" menu in the menu bar (custom layouts only), deferred loading to prevent startup flash
- **Axis Configuration and Button Modes hidden for custom layouts** — These legacy dialogs only appear for non-custom layout profiles; custom layouts use per-widget settings instead
- **Widget Palette title cleanup** — Removed duplicate "Widget Palette" heading inside the palette content since the window title bar already shows it
- **Docs folder reorganized** — Documentation now organized into subdirectories: `setup/`, `architecture/`, `development/`, `accessibility/`
- **Installer improvements** — Optional prompt to remove user data on uninstall; user profiles in `%APPDATA%` preserved by default across reinstalls

---

## [1.2.0] — 2025-02-14

### Added
- **Windows Installer (NSIS)** — Full installer with desktop/start menu shortcuts, uninstall support, previous-version detection
- **Code-signed executable** — EV certificate signing with SHA-256 timestamping for instant SmartScreen trust
- **UIAccess manifest** — `uiAccess="true"` for on-screen keyboard parity (requires signed exe in trusted location)
- **Vertical Slider widget** — Separate "V Slider" in palette (tall & narrow, bottom-to-top fill)
- **Slider click mode** — Per-slider "Jump to position" vs "Relative drag" option in config dialog
- **Dark-themed ComboBox dropdowns** — All config dialog dropdowns now have proper dark styling with blue highlight

### Fixed
- **Config dialog Apply button hidden** — Moved Cancel/Apply buttons outside the Flickable so they're always visible at the bottom of the dialog regardless of content height
- **"Profile saved" spam** — Removed `profileSaved.emit()` from auto-save; only explicit saves trigger the notification now
- **Vertical slider rendering** — Fixed QML anchor conflicts in fill rectangles by using pure x/y/width/height (no conditional anchors)
- **Widget property changes not applying** — Changed Repeater to use `model: root.widgetModel` with `modelData` and `JSON.parse(JSON.stringify())` deep copy for reliable delegate recreation
- **Repeater delegate scope** — Prefixed helper function calls with `root.` to fix `ReferenceError` when using array model

### Changed
- **Slider palette split** — Replaced single "Slider" button with "H Slider" (horizontal) and "V Slider" (vertical) in the widget palette
- **Orientation is read-only** — Orientation is determined at creation time by palette choice; config dialog shows it as informational text instead of a dropdown

---

## [1.0.1] — 2025-12-01

### Added
- **Custom Layout System** — Drag-and-drop widget canvas with 5 widget types: Joystick, Button, Slider, D-Pad, Steering Wheel
- **Widget Palette** — Pop-out tool window with smart auto-assignment of axes and button IDs
- **Per-widget config dialog** — Label, axis mapping, sensitivity, deadzone, extremity deadzone, snap mode, toggle mode, triple-click lock
- **Triple-click mouse lock** — Lock joystick to follow mouse cursor; triple-click again to release (returns to center)
- **Response curve preview** — Real-time graph in config dialog matching exact backend formula
- **Save Layout As** — Save custom layouts with custom names for different games

### Fixed
- **Widget palette overlap** — Moved palette to external pop-out window
- **Mouse lock edge sticking** — Full-canvas overlay tracks mouse without boundary issues

---

## [1.0.0] — 2025-11-15

### Initial Release
- Virtual controller interface using vJoy and ViGEm
- Flight Sim, Xbox, and Adaptive layout profiles
- Joystick sensitivity curves with deadzone support
- Button toggle/momentary modes
- Axis mapping configuration
- Profile system with save/load/switch
- No-focus mode for seamless game integration
