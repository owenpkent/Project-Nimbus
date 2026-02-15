# Project Nimbus – TODO

## Adaptive Platform 2 (Custom Layout System) — `feature/adaptive-platform-2`

### Core Canvas
- [x] **Modular drag-and-drop canvas** (`CustomLayout.qml`)
- [x] **DraggableWidget** — drag, resize, delete, configure any widget
- [x] **WidgetPalette** — sidebar toolbar to add joystick/button/slider
- [x] **Widget config dialog** — double-click to edit label, axis, button ID, color, shape
- [x] **Grid snapping** and optional grid overlay
- [x] **Auto-save** on exit edit mode
- [x] **Profile JSON persistence** for widget positions/sizes/config

### Widget Improvements
- [ ] **Smart button ID auto-assignment** — new buttons find next unused vJoy button ID
- [ ] **Centered slider option** — `center_return` property for spring-to-center axes
- [ ] **SL0/SL1 axis support** — expose vJoy slider axes in widget config dropdowns
- [ ] **Toggle mode in edit config** — set toggle/momentary per button in widget config dialog
- [ ] **Axis sensitivity in edit config** — per-widget sensitivity/deadzone settings
- [ ] **Fix widget palette overlap** — palette should not cover canvas widgets

### New Widget Types
- [ ] **D-Pad** — 4-directional digital button cluster
- [ ] **Steering Wheel** — rotational single-axis input
- [ ] **Dwell Button** — hover-to-activate for users who can't click
- [ ] **Scan Mode Strip** — sequential highlight for single-switch access
- [ ] **Macro Button** — fire a sequence of button presses
- [ ] **Pressure Pad** — hold duration → analog value
- [ ] **Radial Menu** — circular button selector

### Interaction
- [ ] **Triple-click mouse lock** — lock mouse to joystick until triple-click again
- [ ] **Sticky axis mode** — click to set value, stays without holding

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

## Release & Distribution
- [ ] **EV code signing** — sign executable with EV certificate, enable UIAccess=true
- [ ] **Windows installer** — PyInstaller + NSIS/Inno Setup
- [ ] **vJoy auto-detection** — detect and guide vJoy installation on startup
- [ ] **Portable build** — zipped standalone for advanced users

## Backlog
- [ ] **Macro system** — record and playback button sequences (ref: Celtic Magic GCM)
- [ ] **Eye-gaze zone widget** — large activation zones for eye-tracking
- [ ] **Companion app** — phone accelerometer as tilt input via WebSocket
- [ ] **Toggle panel widget** — cockpit switch panel for sim games