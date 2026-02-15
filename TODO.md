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

### Planned Widgets
- [ ] **Dwell Button** — hover-to-activate for users who can't click
- [ ] **Scan Mode Strip** — sequential highlight for single-switch access
- [ ] **Macro Button** — fire a sequence of button presses
- [ ] **Pressure Pad** — hold duration → analog value
- [ ] **Radial Menu** — circular button selector

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

## Future: VDroid Custom Driver
- [ ] **Phase 1**: Multi-device vJoy (16 devices × 8 axes = 128 axes, zero dev needed)
- [ ] **Phase 2**: UMDF virtual HID driver with 32+ axes, 256+ buttons per device
- [ ] **Phase 3**: XInput compatibility layer for Xbox game support
- See [docs/VDROID_DRIVER_BRAINSTORM.md](docs/VDROID_DRIVER_BRAINSTORM.md) for full analysis

## Backlog
- [ ] **Macro system** — record and playback button sequences (ref: Celtic Magic GCM)
- [ ] **Eye-gaze zone widget** — large activation zones for eye-tracking
- [ ] **Companion app** — phone accelerometer as tilt input via WebSocket
- [ ] **Toggle panel widget** — cockpit switch panel for sim games