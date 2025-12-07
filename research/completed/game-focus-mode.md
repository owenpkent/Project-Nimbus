# Game Focus Mode

**Status:** ✅ Implemented (December 2025)

## Problem

When using Project Nimbus as a virtual controller with mouse input, clicking on the UI causes the game window to lose focus. This breaks gameplay—games pause, input stops.

## Solution: Focus Restoration

We use a focus restoration approach that saves the foreground window on mouse press and restores it on release.

### How It Works

1. **On Mouse Press**: Save the current foreground window (the game)
   ```python
   def save_foreground_window():
       current = user32.GetForegroundWindow()
       if current != _our_hwnd:
           _last_foreground_hwnd = current
   ```

2. **On Mouse Release**: Restore focus to the saved window
   ```python
   def on_window_activated():
       if _last_foreground_hwnd:
           set_foreground_window(_last_foreground_hwnd)
   ```

3. **Focus Restoration Trick**: Windows normally prevents `SetForegroundWindow` from working unless you're the foreground app. We work around this by temporarily attaching to the target window's input thread:
   ```python
   user32.AttachThreadInput(our_thread, target_thread, True)
   user32.SetForegroundWindow(target_hwnd)
   user32.AttachThreadInput(our_thread, target_thread, False)
   ```

4. **Result**: Nimbus briefly takes focus (so mouse input works normally), then immediately returns focus to the game when you release.

## Usage

1. Launch Project Nimbus
2. Start your game
3. Go to **View > Game Focus Mode** (checkbox)
4. Click/touch Project Nimbus — game stays focused!

## Configuration

Setting is persisted in `controller_config.json`:
```json
{
  "ui": {
    "no_focus_mode": true
  }
}
```

## Files Modified

| File | Purpose |
|------|---------|
| `src/window_utils.py` | Windows API helpers for focus management |
| `src/bridge.py` | Added `noFocusMode` property and `setWindow()` slot |
| `qml/Main.qml` | Added "Game Focus Mode" toggle in View menu |

## Known Limitations

- **Windows only** — Uses Windows API, not available on Mac/Linux
- **Brief focus loss** — Game loses focus momentarily during press, regains on release
- **Some games may detect this** — Games that pause instantly on focus loss may still notice
- **Alt+Tab still switches windows** — This is expected behavior
- **Touchscreen support untested** — Currently tested with mouse input only

## Why Not WS_EX_NOACTIVATE?

We initially tried `WS_EX_NOACTIVATE` which prevents the window from ever taking focus. However, this broke mouse input in Qt:
- Joystick drag operations didn't work
- The window couldn't capture mouse events properly
- vJoy stopped receiving any input

The focus restoration approach is a reliable compromise.

## Future Improvements

- Add visual indicator when Game Focus Mode is active
- Consider using a timer to delay focus restoration (might feel smoother)
- Test with various games to see which detect the brief focus loss
