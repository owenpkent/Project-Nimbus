# Widget Ideas for Adaptive Platform 2

A brainstorm of widget types for the modular controller builder, with a focus on accessibility for users with physical disabilities.

---

## Current Widgets

| Widget | Description | Status |
|--------|-------------|--------|
| **Joystick** | 2-axis analog stick with thumb indicator | ✅ Implemented |
| **Button** | Single press button (toggle or momentary) | ✅ Implemented |
| **Slider** | Single-axis analog control (horizontal) | ✅ Implemented |

---

## Planned Widgets

### Steering Wheel
- **Type**: `wheel`
- **Description**: Rotational input mapped to a single axis. Visual is a circular arc that the user drags around. Great for driving games.
- **Properties**: `mapping.axis`, `rotation_range` (e.g. 270°), `center_return` (bool)
- **Accessibility benefit**: Larger target area than a joystick for single-axis control; intuitive for users who understand steering but struggle with dual-axis sticks.

### D-Pad (Digital Directional Pad)
- **Type**: `dpad`
- **Description**: 4-directional button cluster (Up/Down/Left/Right). Each direction maps to a separate button ID.
- **Properties**: `mapping.up`, `mapping.down`, `mapping.left`, `mapping.right` (button IDs)
- **Accessibility benefit**: Discrete directional input is easier for users with tremors than continuous analog control.

### Centered Slider (Spring-to-Center)
- **Type**: Slider with `center_return: true`
- **Description**: Like a standard slider but returns to center when released, like a flight stick axis. Useful for steering, pitch, or any axis where center = neutral.
- **Accessibility benefit**: Provides analog axis control without needing a full 2D joystick — simpler for single-axis tasks.

---

## Brainstormed Accessibility Widgets

### Dwell Button (Hover-to-Activate)
- **Type**: `dwell_button`
- **Description**: Activates when the mouse hovers over it for a configurable duration (e.g. 1 second). No click required.
- **Properties**: `dwell_time_ms`, `button_id`, `visual_countdown` (bool)
- **Accessibility benefit**: Critical for users who cannot click a mouse — common in users with severe motor impairments. Works with eye-tracking systems that simulate mouse hover.
- **Visual**: Circular fill animation showing dwell progress.

### Large Target Button
- **Type**: `big_button`
- **Description**: Extra-large button that takes up significant screen area. Designed to be an easy target for users with limited fine motor control.
- **Properties**: Same as button but with enforced minimum size (e.g. 120×120px)
- **Accessibility benefit**: Fitts's Law — larger targets are easier to hit. Essential for users with tremors or limited precision.

### Scan Mode Strip
- **Type**: `scan_strip`
- **Description**: A row of buttons that highlights sequentially. User presses a single switch (or clicks anywhere) to select the currently highlighted button. Configurable scan speed.
- **Properties**: `buttons[]` (array of button IDs), `scan_speed_ms`, `auto_scan` (bool)
- **Accessibility benefit**: Single-switch access — the gold standard for users with severe motor limitations who can only operate one switch. Used extensively in AAC (Augmentative and Alternative Communication) devices.

### Pressure Pad (Hold-for-Value)
- **Type**: `pressure_pad`
- **Description**: A large area where holding longer increases the axis value (like pressing harder on a trigger). Release resets. Visual shows a fill level.
- **Properties**: `mapping.axis`, `ramp_time_ms` (time to reach full value), `max_value`
- **Accessibility benefit**: Converts a simple hold action into analog axis control. No precision dragging needed — just hold and wait.

### Radial Menu
- **Type**: `radial_menu`
- **Description**: Circular menu with segments. Click/drag into a segment to activate that button. Good for grouping related actions.
- **Properties**: `segments[]` (array of `{button_id, label, color}`)
- **Accessibility benefit**: Groups many buttons into one target area. User only needs to reach one spot, then select direction. Reduces total mouse travel distance.

### Toggle Panel
- **Type**: `toggle_panel`
- **Description**: Grid of on/off toggle switches, like a cockpit switch panel. Each switch stays in its position until flipped again.
- **Properties**: `switches[]` (array of `{button_id, label}`), `columns`
- **Accessibility benefit**: Clear visual state — switches show ON/OFF position. Good for cockpit sims where many buttons need to maintain state.

### Macro Button
- **Type**: `macro_button`
- **Description**: A button that fires a sequence of button presses/releases with configurable delays.
- **Properties**: `sequence[]` (array of `{button_id, pressed, delay_ms}`), `label`
- **Accessibility benefit**: Reduces complex multi-button inputs to a single action. Critical for users who cannot perform rapid sequential inputs (e.g. fighting game combos, QTE sequences).

### Mouse Lock Joystick (Triple-Click Lock)
- **Type**: Enhancement to existing joystick
- **Description**: Triple-click on a joystick to lock the mouse to it — the mouse is captured and all movement controls the joystick until triple-click again. Eliminates the need to stay within the joystick circle.
- **Accessibility benefit**: Users don't need to maintain mouse position within a small target. Once locked, the entire mouse range becomes the joystick range. Essential for flight simulators where continuous joystick control is needed.

### Sticky Axis (Click-to-Set)
- **Type**: Enhancement to slider/joystick
- **Description**: Click to set a value, and it stays there without holding. Click again to change. Like a "click and release" throttle.
- **Properties**: `sticky: true` on any axis widget
- **Accessibility benefit**: Removes the need to hold the mouse down continuously. Users can set a throttle value and release the mouse.

### Eye-Gaze Zone
- **Type**: `gaze_zone`
- **Description**: Very large colored zones on screen. When the mouse (or eye tracker cursor) enters a zone, it activates. Can be configured as buttons or axis regions.
- **Properties**: `activation_method` (`"enter"` or `"dwell"`), `mapping`
- **Accessibility benefit**: Designed for eye-tracking input. Zones should be large enough (200×200+) for reliable gaze detection.

### Tilt Indicator (Accelerometer Input)
- **Type**: `tilt_display`
- **Description**: If the device has an accelerometer (tablet, phone via companion app), display tilt angle and map to axes.
- **Accessibility benefit**: Some users can tilt a device more easily than move a mouse. Could work via WebSocket from a phone companion app.

---

## Widget Sizing Guidelines for Accessibility

| User Need | Recommended Minimum Size |
|-----------|-------------------------|
| Standard mouse user | 40×40px |
| Limited fine motor control | 80×80px |
| Significant tremor | 120×120px |
| Eye-tracking / head mouse | 150×150px |
| Single-switch scanning | Full-width strip |

---

## Priority Order for Implementation

1. **Centered Slider** (quick addition — `center_return` property on existing slider)
2. **D-Pad** (common need, straightforward 4-button widget)
3. **Steering Wheel** (unique value for driving games)
4. **Triple-Click Mouse Lock** (high value for flight sim users)
5. **Dwell Button** (critical accessibility feature)
6. **Scan Mode Strip** (single-switch access)
7. **Macro Button** (complex input simplification)
8. **Pressure Pad** (analog from hold duration)
9. **Radial Menu** (efficient button grouping)
10. **Toggle Panel** (cockpit sim use case)
