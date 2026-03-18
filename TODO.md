# Project Nimbus – TODO

## Adaptive Platform 2 (Custom Layout System) — `feature/adaptive-platform-2`

### Core Canvas
- [x] **Modular drag-and-drop canvas** (`CustomLayout.qml`)
- [x] **DraggableWidget** — drag, resize, delete, configure any widget
- [x] **WidgetPalette** — pop-out tool window with custom drag title bar
- [x] **Widget config dialog** — scrollable, double-click to edit all widget properties
- [x] **Grid snapping** and optional grid overlay
- [x] **Auto-save** on every widget change and exit edit mode
- [x] **Profile JSON persistence** for widget positions/sizes/config
- [x] **Save As dialog** — save layout with custom name

### Widget Improvements (All Complete)
- [x] **Smart button ID auto-assignment** — new buttons/D-pads find next unused vJoy button ID
- [x] **3-mode slider snap** — "none" (hold), "snap to zero" (return-to-zero), "snap to center" (spring-to-center)
- [x] **Slider orientation** — separate H Slider and V Slider widgets in palette
- [x] **SL0/SL1 axis support** — all 8 vJoy axes available in widget config dropdowns
- [x] **Toggle mode in edit config** — set toggle/momentary per button in widget config dialog
- [x] **Per-widget sensitivity settings** — sensitivity (0-100%), deadzone (0-100%), extremity deadzone (0-100%)
- [x] **Response curve preview** — live-updating canvas graph matching Settings menu formula
- [x] **Widget palette as pop-out window** — frameless window with custom draggable title bar, stays on top, never overlaps canvas

### Widget Types (All Complete)
- [x] **Joystick** — 2-axis analog stick with triple-click mouse lock
- [x] **Button** — single press with toggle/momentary and color/shape options
- [x] **Slider** — horizontal/vertical with 3 snap modes
- [x] **D-Pad** — 4-directional digital button cluster with auto-assigned button IDs
- [x] **Steering Wheel** — rotational single-axis with spoke indicator

### Interaction (All Complete)
- [x] **Triple-click mouse lock** — full-canvas hover overlay tracks mouse everywhere, no edge-sticking
- [x] **Unlock returns to center** — joystick snaps back to (0,0) on triple-click unlock

## Completed Features
- [x] **Flight Sim layout** — dual joysticks + throttle/rudder with responsive scaling
- [x] **Xbox layout** — standard Xbox gamepad
- [x] **Adaptive Platform 1** — accessibility-focused fixed layout with mode switching
- [x] **Profile system** — switch, save, duplicate, delete, reset profiles
- [x] **Per-profile settings** — joystick/rudder sensitivity + button toggle modes per profile
- [x] **Axis configuration dialog** — per-axis sensitivity, deadzone, VJoy mapping
- [x] **Button settings dialog** — toggle vs. momentary modes
- [x] **Game Focus Mode** — prevent stealing focus from games (Windows)
- [x] **ViGEm Xbox emulation** — XInput support for modern games
- [x] **Rudder improvements** — wider control, center-lock toggle

## v1.2.1 New Features
- [x] **Wheelchair joystick support (FPS-style delta tracking)** — cursor hidden, anchored to joystick center, delta-based deflection with continuous warp-back
- [x] **Lock Sensitivity slider** — per-joystick (1-10), controls how much physical movement is needed for full virtual deflection
- [x] **Tremor Filter** — per-joystick EMA smoothing (0-10) for jittery wheelchair joystick input
- [x] **Auto-return to center** — per-joystick toggle with configurable delay (1-10ms)
- [x] **DPI-aware cursor positioning** — QCursor.setPos() instead of Win32 SetCursorPos for correct behavior on scaled displays
- [x] **Copy sensitivity from dropdown** — per-widget axis settings can copy sensitivity/deadzone/extremity from other widgets
- [x] **Loading splash screen** — dark-themed splash with logo, version, progress messages
- [x] **Scrollbars on all settings dialogs** — QML config, Button Settings, Axis Settings
- [x] **Edit Layout as top-level menu** — dedicated menu bar button for custom layouts
- [x] **Help menu with Getting Started & Feature Guide** — in-app documentation for all features
- [x] **Widget Palette title cleanup** — removed duplicate heading
- [x] **Deprecated legacy settings for custom layouts** — Axis Configuration and Button Modes hidden when custom layout active

## v1.2.0 New Features
- [x] **Slider click mode** — "Jump to position" vs "Relative drag" per-slider
- [x] **Slider snap-back easing** — smooth NumberAnimation with OutCubic curve, sends interpolated values to vJoy
- [x] **Separate V Slider widget** — dedicated vertical slider in palette (50×160 default)
- [x] **Dark-themed ComboBox dropdowns** — all config dialog dropdowns properly styled
- [x] **Config dialog Apply always visible** — buttons outside Flickable
- [x] **Fixed profile saved spam** — removed signal from auto-save
- [x] **Reliable model refresh** — Repeater uses array model + JSON deep copy

## Release & Distribution
- [x] **EV code signing** — sign_exe.bat signs exe + installer with SHA-256 + timestamp
- [x] **UIAccess=true manifest** — embedded in exe for on-screen keyboard parity
- [x] **Windows installer (NSIS)** — shortcuts, uninstall, previous-version detection
- [x] **Application icon** — multi-size ICO (16–256px) from logo.png
- [x] **CHANGELOG.md** — semantic versioning with Keep a Changelog format
- [x] **Repo cleanup** — moved docs/screenshots/video, cleaned .gitignore
- [ ] **vJoy auto-detection** — detect and guide vJoy installation on startup
- [ ] **Portable build** — zipped standalone for advanced users

## Future: VDroid Custom Driver & Installer Bundling
- [ ] **Bundle V-Droid driver with installer** — auto-download or include during NSIS install so users don't need separate vJoy setup
- [ ] **Phase 1**: Multi-device vJoy (16 devices × 8 axes = 128 axes, zero dev needed)
- [ ] **Phase 2**: UMDF virtual HID driver with 32+ axes, 256+ buttons per device — support 20+ joysticks
- [ ] **Phase 3**: XInput compatibility layer for Xbox game support
- See [docs/architecture/VDROID_DRIVER_BRAINSTORM.md](docs/architecture/VDROID_DRIVER_BRAINSTORM.md) for full analysis

## Future: Voice Control Integration
- [ ] **Vosk integration** — offline speech recognition for hands-free button activation
- [ ] **Whisper integration** — OpenAI Whisper for high-accuracy voice commands
- [ ] **DeepRAM integration** — evaluate for low-latency voice-to-action pipeline
- [ ] **Voice-to-macro** — speak command names to trigger macro sequences
- [ ] **Custom wake word** — configurable activation phrase

## Future: Macro Editor
- [x] **Macro Joystick Mode** — convert joystick directions into button/axis/turbo actions (v1.3.0)
- [x] **Visual zone editor** — 8-zone + center joystick diagram with per-zone action config
- [x] **Quick presets** — ABXY, D-Pad, Triggers, Shoulders presets
- [x] **Turbo mode** — auto-fire buttons at configurable rate (1-30 Hz)
- [ ] **Visual macro editor** — drag-and-drop sequence builder for button press sequences
- [ ] **Timing control** — configurable delays between actions (ms precision)
- [ ] **Loop / repeat** — repeat macros N times or until cancelled
- [ ] **Conditional macros** — trigger different sequences based on toggle state
- [ ] **Import/export** — share macro profiles as JSON files
- [ ] **Voice-triggered macros** — bind macros to voice commands

## v1.4.1 Mouse Capture & Controller Mode
- [x] **Controller Mode Enforcement** — keep-alive pulse via ViGEm forces games to stay in controller mode and voluntarily release mouse
- [x] **`src/mouse_hider.py`** — sub-deadzone stick oscillations, initial burst, WH_MOUSE_LL hook, integrated ClipCursor release
- [x] **`startFullGameMode()` / `stopFullGameMode()`** — one-call combined focus mode + cursor release + controller mode
- [x] **Controller burst** — one-shot burst (amplitude 0.5 + A-button press) to force controller mode
- [x] **Game Focus Mode rewrite** — `WS_EX_NOACTIVATE` + `WM_MOUSEACTIVATE` native event filter prevents focus stealing
- [x] **One-click "Start Game Mode" button** — bottom-right of main window, opens filtered window picker
- [x] **Raw Input mouse suppression** — `WH_MOUSE_LL` hook blocks mouse-move events over game window
- [x] **ViGEm on-demand creation** — Game Mode creates ViGEm gamepad regardless of profile type
- [x] **ViGEm diagnostics** — picker popup shows red warning if ViGEmBus driver missing
- [x] **Installer: ViGEmBus driver** — NSIS installer detects and offers to install ViGEmBus alongside vJoy
- [ ] **Test with Satisfactory** — verify controller mode works with ViGEmBus installed (WIP)
- [ ] **Test with Minecraft** — verify controller mode prevents cursor re-capture
- [ ] **Test with Elden Ring** — verify game switches to gamepad prompts and releases mouse
- [ ] **Test with No Man's Sky** — verify ViGEm + controller mode works end-to-end
- [ ] **Keyboard suppression (optional)** — extend mouse hook to also suppress keyboard events reaching the game
- [ ] **Auto-detect input mode switch** — detect when game switches back to M/KB and automatically re-burst

## Backlog
- [ ] **Macro button widget** — fire a sequence of button presses from the canvas
- [ ] **Eye-gaze zone widget** — large activation zones for eye-tracking
- [ ] **Companion app** — phone accelerometer as tilt input via WebSocket
- [ ] **Toggle panel widget** — cockpit switch panel for sim games
- [ ] **Dwell Button** — hover-to-activate for users who can't click
- [ ] **Scan Mode Strip** — sequential highlight for single-switch access
- [ ] **Pressure Pad** — hold duration → analog value
- [ ] **Radial Menu** — circular button selector