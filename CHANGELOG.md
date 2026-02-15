# Project Nimbus Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] — 2026-02-14

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
