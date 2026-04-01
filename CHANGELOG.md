# Nimbus Adaptive Controller — Changelog

> **Formerly distributed as Project Nimbus**

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **User Accounts** (`src/cloud_client.py`) — Optional sign-in with Email, Google OAuth, or Facebook OAuth via Supabase. Tokens stored securely in OS credential vault (Windows Credential Manager) via `keyring`. Supports session restore, silent token refresh, and offline fallback.
- **Cloud Profile Sync** — Nimbus+ subscribers can sync profiles across machines. Last-write-wins merge strategy per profile ID. Push on save, pull on startup.
- **Telemetry & Crash Reporting** (`src/telemetry.py`) — Opt-in anonymous usage analytics and crash reporting. Events buffered locally and batch-flushed every 5 minutes. No PII collected — all identifiers are SHA-256 hashed. Optional Sentry SDK integration for structured crash reports.
- **Auto-Updater** (`src/updater.py`) — Lightweight version checker that fetches a JSON manifest on startup. Non-intrusive ribbon notification when a new version is available. Supports stable/beta/dev update channels. Force-update warning when running below minimum supported version.
- **Account Dialog** (`qml/components/AccountDialog.qml`) — Sign-in UI with Google, Facebook, and email/password options. Shows account status, tier, and sync button when signed in.
- **Privacy Settings Dialog** (`qml/components/SettingsPrivacyDialog.qml`) — Toggle crash reports and analytics independently. Expandable "What we collect" and "What we NEVER collect" sections for full transparency.
- **Update Notification Ribbon** (`qml/components/UpdateNotification.qml`) — Non-intrusive top-of-window ribbon with download and dismiss buttons. Connects to `UpdateChecker` signals.
- **New dependencies**: `httpx>=0.27.0` (async HTTP), `keyring>=25.0.0` (OS credential vault), `sentry-sdk>=2.0.0` (crash reporting)
- **Documentation**: `docs/setup/ACCOUNTS.md`, `docs/setup/TELEMETRY.md`, `docs/setup/UPDATER.md` — comprehensive setup and usage guides for all three new systems.

---

## [1.5.0] — 2026-03-29 — *Renamed to Nimbus Adaptive Controller*

### Added
- **VS Code-style status ribbon** — Thin ribbon at the bottom of the main window displays the active output mode (Xbox/vJoy), current profile name, and connection status. Click the output mode label to switch between ViGEm and vJoy from the ribbon without opening any menu.
- **New Profile dialog** — Single combined dialog replacing the old two-step save-then-create flow. Enter profile name, optional description, and check/uncheck "save current profile first" — all in one step. Blank canvas is created on confirm; no widgets are inherited from the previous profile.
- **Recent Profiles menu** — File → Recent Profiles submenu shows the last 5 used profiles (most-recent first). Recent list is persisted in `controller_config.json` under `ui.recent_profiles` and survives application restarts.
- **Profile reload on switch** — `CustomLayout.qml` now listens to `profileChanged` and reloads `widgetModel`, `gridSnap`, and `showGrid` from the newly active profile immediately. Previously the canvas stayed blank after switching profiles.
- **Smart widget placement** — `_findFreePosition()` in `CustomLayout.qml` scans the canvas for a clear spot (AABB collision check, grid-snap step size) before placing a new widget from the palette. New widgets no longer drop on top of existing ones.
- **Bundled-profile save guard** — Clicking "Save Layout" while on a bundled profile (e.g., `adaptive_platform_2`) redirects to "Save Layout As..." so the bundled file cannot be accidentally overwritten.
- **`isBundledProfile()` bridge slot** — QML-callable slot that returns `true` when the active profile is a built-in bundled profile.
- **`createProfileAs()` bridge slot** — QML-callable slot creating a new blank profile (empty widget canvas, default settings) by name and description. Emits `profilesListChanged` so the profile menu updates immediately.
- **`getRecentProfiles()` bridge slot** — Returns the recent-profiles list (filtered to profiles that still exist on disk) as a `QVariantList` for QML.

### Changed
- **Widget palette window width** — Widened from 200 px to 240 px for better readability of ViGEm-mode labels.
- **ViGEm palette separation** — Widget palette shows context-specific controls based on output mode. ViGEm mode: Left Stick, Right Stick, LT/RT triggers, Xbox button presets, D-Pad with fixed IDs 11–14. vJoy mode: generic joystick, buttons, sliders, wheel, D-Pad with dynamic IDs.
- **Xbox button labels read-only** — In ViGEm mode the per-widget config dialog shows the fixed Xbox label (A/B/X/Y/LB/RB/Back/Start/LS/RS) as read-only text; numeric ID editing is only available in vJoy mode.
- **Joystick axis combos context-aware** — `sl0`/`sl1` axes are hidden from axis dropdowns in ViGEm mode (Xbox controller has no slider axes).
- **New profile starts blank** — `config.create_profile_as()` now produces a profile with `layout_type: "custom"`, an empty `widgets: []` canvas, and default sensitivity settings. It no longer copies widget layout or axis mappings from the current profile.
- **Recent profiles persistence** — `bridge.switchProfile()` writes the updated recent list to `config.set("ui.recent_profiles", ...)` and calls `config.save_config()` on every switch.

### Fixed
- **`ReferenceError: root is not defined` in `CustomLayout.qml`** — Delegate signal handlers (`onWidgetMoved`, `onWidgetResized`, etc.) referenced `root` but `DraggableWidget` also defines `id: root` internally. Fixed by adding `readonly property var layout: root` on the canvas `Rectangle` and using `canvas.layout` in all delegate signal handlers.
- **Scrollbar encroaching on palette content** — `ColumnLayout` inside the `Flickable` now subtracts `vsb.width` from its width so the attached `ScrollBar` overlay does not clip the rightmost edge of palette items.
- **`isViGEmAvailable` capitalization mismatch** — QML was calling `controller.isViGEmAvailable` but the bridge slot is `isVigemAvailable`. Corrected throughout `Main.qml`.

---

## [1.4.2] — 2026-03-18

### Added
- **Controller Monitor status bar** — Live controller output display at the bottom of the Nimbus window. Toggle via **View → Controller Monitor**. Shows all current axis values (LX, LY, RX, RY, LT, RT) and active buttons at 150ms refresh. Replaces the need for an external vJoy monitor when using ViGEm.
- **Individual axis selection for joystick widgets** — Axis Pair combo replaced with separate **X-Axis** and **Y-Axis** dropdowns in the widget config dialog. Each can independently be set to any axis (`x`, `y`, `rx`, `ry`, `z`, `rz`, `sl0`, `sl1`) or `None`. Enables mixed mappings like Left-Y + Right-X from a single joystick widget.
- **Per-axis invert toggles** — Each axis row in the joystick config dialog now has an **INV** button. When active (blue), that axis direction is flipped. Useful for games with inverted camera axes or for left-handed control schemes.
- **`getControllerStateText()` bridge slot** — Returns a formatted one-line summary of current ViGEm/vJoy axis and button state for the monitor bar.

### Fixed
- **Taskbar icon missing** — `WS_EX_APPWINDOW` is now explicitly set and `WS_EX_TOOLWINDOW` cleared when Game Focus Mode is enabled. The Nimbus taskbar entry is always visible even with `WS_EX_NOACTIVATE` active.
- **Can't bring Nimbus to foreground** — Game Focus Mode (`WS_EX_NOACTIVATE`) was being persisted to config via `startFullGameMode`, so it was active on every startup even outside game sessions. It is now session-only: enabled automatically when Full Game Mode starts, disabled when it stops, and never saved to the profile config.
- **Axis + Button macro not moving** — The keep-alive pulse loop (`mouse_hider.py`) was calling `left_joystick_float(micro_x, micro_y)` every 33ms, overwriting any macro-set axis value (e.g. LY:+1.0 for forward movement). The pulse now saves the current axis state from `ViGEmInterface.current_values`, adds the tiny oscillation delta on top, then immediately restores the saved values. Jump + movement now work simultaneously.
- **Axis + Button macro action not saving** — `_saveCurrentZone` in `MacroEditorDialog.qml` was missing `"axis_button"` from its action array (index 5 out of bounds → saved `undefined`). Execution code was already correct but never reached because the saved action was `undefined`.

### Changed
- **`start_controller_mode()` now accepts `vigem_interface` parameter** — The pulse loop and mouse hook burst both save/restore the full left + right stick state through this reference, preventing any pulse from clobbering gameplay axis values.
- **Game Focus Mode restore key changed** — `setWindow` now checks `ui.no_focus_mode_user` (explicit user setting) instead of `ui.no_focus_mode` (which was set by game mode auto-enable). Existing profiles with a stale `ui.no_focus_mode: true` will no longer force `WS_EX_NOACTIVATE` at startup.

---

## [1.4.1] — 2026-03-17

### Added
- **Controller Mode Enforcement** — New approach to mouse capture that makes games *voluntarily* release the cursor. Instead of fighting `ClipCursor` in a race condition, Nimbus sends continuous controller keep-alive signals through ViGEm so the game thinks only a gamepad is connected and stops capturing the mouse.
- **`src/mouse_hider.py`** — Pure `ctypes` module implementing:
  - Controller keep-alive pulse (configurable 5–120 Hz) with sub-deadzone stick oscillations
  - Initial controller burst to force games into controller mode on startup
  - `WH_MOUSE_LL` hook that detects mouse-over-game and immediately counters with controller input
  - Integrated `ClipCursor(NULL)` release alongside controller pulse
- **`startControllerMode()` / `stopControllerMode()`** — New bridge slots for QML
- **`sendControllerBurst()`** — One-shot burst to force controller mode without continuous keep-alive
- **`startFullGameMode()` / `stopFullGameMode()`** — Recommended one-call approach combining focus mode + cursor release + controller mode enforcement
- **One-click "Start Game Mode" button** — Visible in bottom-right corner of main window. Opens a window picker (filtered to hide browsers/system apps), click your game, everything starts automatically.
- **ViGEm diagnostics** — Picker popup shows red warning if ViGEmBus driver is not installed
- **Controller mode statistics** — Track pulses sent, mouse events detected, bursts fired
- **ViGEmBus driver in installer** — NSIS installer now detects and offers to download/install the ViGEmBus driver alongside vJoy
- **Research doc** — `research/in-progress/controller-mode-enforcement.md` documenting the dual-input-detection exploit

### Changed
- **Mouse capture strategy** — Shifted from pure `ClipCursor(NULL)` racing to a combined approach: controller mode enforcement (primary) + cursor release (fallback). Games that detect Xbox input will voluntarily release the mouse, eliminating the race condition entirely.
- **Game Focus Mode rewritten** — Now uses true `WS_EX_NOACTIVATE` window style instead of save/restore approach. Clicking Project Nimbus **never** steals focus from the game — no more pause menus triggering on click.
- **`startFullGameMode()` auto-enables Game Focus Mode** — No need to enable separately from View menu.
- **`startFullGameMode()` no longer calls `make_borderless()`** — This was reshaping/minimizing games. Game Mode now only starts focus mode + cursor release + controller mode enforcement; leave the game window as-is.
- **ViGEm gamepad created on demand** — Game Mode now creates a ViGEm gamepad regardless of profile type, so controller mode enforcement works even with flight_sim profiles.
- **Installer updated** — Driver page now shows both vJoy and ViGEmBus with detection and silent installation.

### Fixed
- **Clicking Nimbus caused game to pause** — The old Game Focus Mode briefly transferred focus to Nimbus before restoring it. Games like Minecraft detected the focus loss and opened the pause menu. Fixed by using `WS_EX_NOACTIVATE` + `WM_MOUSEACTIVATE` native event filter so focus never leaves the game at all.
- **Raw Input mouse still moved game camera** — Games using Raw Input (Satisfactory, Unreal Engine titles) received mouse delta movement even when the cursor was outside the game window. The `WH_MOUSE_LL` hook now **suppresses** mouse-move events when the cursor is over the game window, blocking Raw Input from seeing them.
- **Games not switching to controller mode** — Controller burst amplitude was too small (0.05) to exceed Unreal Engine's deadzone (0.25). Increased burst amplitude to 0.5 and added A-button press during burst for unambiguous controller detection.
- **Game Mode picked wrong window** — Auto-detect fallback picked Microsoft Edge instead of the game. Replaced with a filtered window picker popup.
- **Game Mode minimized the game** — `make_borderless()` reshaped the game window, causing it to disappear. Removed from Game Mode flow.
- **Controller mode silently skipped** — If profile didn't use ViGEm (e.g., flight_sim), no gamepad existed and controller mode was silently not started. Fixed: ViGEm gamepad is now created on demand.

### Technical Notes
- Controller keep-alive sends stick oscillations (amplitude 0.08) that are below most games' deadzones (0.15–0.3) but large enough that UE/Unity input detection registers them
- The `WH_MOUSE_LL` hook now suppresses mouse-move events over the game window (returns 1 to block) while passing through events over Nimbus — this prevents Raw Input camera movement
- `WS_EX_NOACTIVATE` + `QAbstractNativeEventFilter` for `WM_MOUSEACTIVATE` → `MA_NOACTIVATE` keeps Qt mouse handling working while preventing window activation
- Requires ViGEmBus driver — installer now handles installation automatically
- **Status: Work in progress** — Controller mode enforcement may not work with all games yet

---

## [1.4.0] — 2026-03-17

### Added
- **Borderless Gaming Integration** — Built-in borderless window mode + continuous `ClipCursor(NULL)` release. No external tools needed. Access via **View → Borderless Gaming...**
- **Auto-detect games** — Identifies 30+ known games from a built-in compatibility database (`src/borderless.py`)
- **One-click workflow** — Green "Apply Borderless + Free Cursor" button applies both simultaneously
- **Adjustable release speed** — Tune polling interval from 16ms (aggressive) to 200ms (gentle)
- **Compatibility browser** — In-app tab showing verified/likely/partial/incompatible games with filter buttons
- **`src/borderless.py`** — Pure `ctypes` module: window enumeration, borderless conversion, cursor release polling, game compat database, auto-detect
- **`qml/components/BorderlessGamingDialog.qml`** — Full-featured game setup + compatibility dialog
- **`docs/GAME_COMPATIBILITY.md`** — Documented game list with genre tips and setup guidance
- **QML/PySide6 UI** — Complete rewrite of the user interface using Qt Quick (QML) with a dark-themed, scalable layout
- **Game Focus Mode** — View menu toggle that restores focus to the game after each interaction using Windows thread-input attachment
- **ViGEm auto-selection** — Automatically uses Xbox 360 (XInput) for xbox/adaptive/custom profiles and vJoy (DirectInput) for flight sim
- **Smooth axis interpolation** — EMA-based smoothing timer at the vJoy update rate (default 60 Hz, configurable up to 240 Hz)
- **Profile system overhaul** — Full create, save, save-as, duplicate, delete, reset-to-defaults from File menu; stored in `%APPDATA%\ProjectNimbus`
- **About dialog** — Dynamic version, description, copyright, and license info in Help menu

### Changed
- **Single default profile** — Removed `flight_simulator`, `xbox_controller`, and `adaptive_platform_1` bundled profiles. `adaptive_platform_2` (Custom Layout Builder) is now the only bundled profile and opens on first launch
- **Default fallback** — `config.py` now falls back to `adaptive_platform_2` instead of `flight_simulator` everywhere

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
