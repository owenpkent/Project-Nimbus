# Game Window Focus Problem

## Current Setup

```
┌─────────────────┐    Bluetooth    ┌─────────────────┐    Synergy    ┌─────────────────┐
│   Wheelchair    │ ─────────────── │     Laptop      │ ────────────► │   Gaming PC     │
│   Controller    │   (1 device     │  (touchscreen)  │   (KVM over   │  (runs games)   │
│                 │    limit)       │                 │    network)   │                 │
└─────────────────┘                 └─────────────────┘               └─────────────────┘
```

**Key constraints:**
- Wheelchair Bluetooth can only connect to ONE device at a time
- Currently connected to laptop
- Synergy extends keyboard/mouse from laptop to gaming PC
- Games run on the gaming PC

## The Problem

Two possible scenarios:

**Scenario A: Project Nimbus on Laptop**
- vJoy runs on laptop, but game is on gaming PC
- vJoy input never reaches the game!
- Need to somehow bridge vJoy across machines

**Scenario B: Project Nimbus on Gaming PC (via Synergy)**
- Clicking Project Nimbus steals focus from the game
- Game may pause or ignore input when unfocused

## Goal

Get virtual controller input from the laptop (where Bluetooth connects) to the gaming PC (where games run), without focus issues.

---

## Solution Options

### 1. Borderless Gaming (Windows Utility)

**What it does:** Forces games into borderless windowed mode, which can help with focus issues.

**Status:** Previously attempted, unclear if working correctly.

**Pros:**
- Free and open source
- Works with most games
- Simple setup

**Cons:**
- Doesn't actually solve the focus problem directly
- Just changes window mode, doesn't prevent focus loss
- May not work with all games (especially older titles)

**Verdict:** ❓ Needs more testing - may help but likely not a complete solution

---

### 2. Moonlight Game Streaming ⭐ BEST FIT FOR CURRENT SETUP

**What it does:** Streams games from a host PC (Gaming PC) to client (Laptop) using NVIDIA GameStream or Sunshine.

**How it fits your setup:**
```
┌─────────────────┐                 ┌─────────────────┐    Moonlight    ┌─────────────────┐
│   Wheelchair    │  Bluetooth      │     Laptop      │ ◄────────────── │   Gaming PC     │
│   Controller    │ ──────────────► │                 │   (stream)      │   (Sunshine)    │
└─────────────────┘                 │ Project Nimbus  │ ──────────────► │                 │
                                    │ + Moonlight     │  (controller)   │   Game runs     │
                                    └─────────────────┘                 └─────────────────┘
```

**The magic:** Moonlight has built-in virtual controller support! When you connect a controller on the client (laptop), it appears as a real Xbox controller on the host (gaming PC). This could work with vJoy!

**Pros:**
- You already have two machines - no extra hardware
- Game focus is irrelevant - it's on the gaming PC, you interact with laptop
- Moonlight natively supports controller passthrough
- Sunshine works with any GPU (not just NVIDIA)
- Low latency on local network (often <10ms)
- Replaces Synergy for gaming (but could keep Synergy for non-gaming)

**Cons:**
- Need to install Sunshine on Gaming PC
- Need to test if vJoy on laptop passes through as a controller
- Video stream adds some latency (though usually minimal on LAN)
- May need to configure firewall/network

**Open Questions:**
- Does Moonlight see vJoy as a controller and pass it through?
- If not, can we send input over network another way?
- What's the actual latency like for your network?

**Verdict:** ⭐⭐⭐ MOST PROMISING - fits your two-machine setup perfectly

---

### 3. VirtualHere

**What it does:** USB over network - shares USB devices between computers.

**How it could help:**
- Could potentially share the vJoy device across network
- Run game on one machine, controller UI on another

**Pros:**
- Hardware-level USB sharing
- Game sees a "real" USB device
- No focus issues since input comes from network

**Cons:**
- Paid software (free version limited to 1 device)
- Requires two machines or complex VM setup
- vJoy is a virtual device - unclear if VirtualHere can share it
- Additional network latency

**Open Questions:**
- Does VirtualHere work with virtual devices like vJoy?
- Is there a way to use this on a single machine?

**Verdict:** ❓ Uncertain - may not work with virtual devices

---

### 4. Windows API: Prevent Focus Loss

**What it does:** Use Windows API to keep game focused or make Project Nimbus not steal focus.

**Possible approaches:**
- `WS_EX_NOACTIVATE` window style - window doesn't activate on click
- `SetWindowLong` to modify Project Nimbus window behavior
- Use a click-through overlay instead of stealing focus

**Pros:**
- Single machine solution
- No additional software needed
- Could be built directly into Project Nimbus

**Cons:**
- Complex to implement correctly
- May not work with all games
- Touch input on non-activating windows is tricky
- Could cause other UX issues

---

#### Implementation Plan: No-Focus Window Mode

##### Step 1: Qt/QML Window Flags

Try the simplest approach first - Qt has built-in flags for this:

```qml
// In Main.qml or ApplicationWindow
ApplicationWindow {
    flags: Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
    // ...
}
```

**What `Qt.WindowDoesNotAcceptFocus` does:**
- Window receives mouse/touch events but doesn't take keyboard focus
- Should prevent stealing focus from the game

**Potential issue:** May not work on all platforms or with all window managers.

##### Step 2: Windows API Fallback (if Qt flags don't work)

Use Python `ctypes` to set `WS_EX_NOACTIVATE` directly:

```python
# In bridge.py or a new window_utils.py
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

def make_window_no_activate(hwnd):
    """Make window not steal focus when clicked."""
    # Get current extended style
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    # Add NOACTIVATE flag
    new_style = style | WS_EX_NOACTIVATE
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
    
def get_qt_window_handle(qwindow):
    """Get native HWND from Qt window."""
    return int(qwindow.winId())
```

Call after window is created:
```python
# In qt_qml_app.py after engine loads
window = engine.rootObjects()[0]
hwnd = get_qt_window_handle(window)
make_window_no_activate(hwnd)
```

##### Step 3: Handle Mouse/Touch Events Without Activation

The tricky part: Windows may still try to activate on mouse down. Override with:

```python
WM_MOUSEACTIVATE = 0x0021
MA_NOACTIVATE = 3

# May need to subclass window or use event filter
# to return MA_NOACTIVATE on WM_MOUSEACTIVATE
```

In Qt, this might require a native event filter:
```python
from PySide6.QtCore import QAbstractNativeEventFilter

class NoActivateFilter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            # Parse MSG structure and check for WM_MOUSEACTIVATE
            # Return MA_NOACTIVATE
            pass
        return False, 0
```

##### Expected Behavior

| Action | With No-Focus Mode | Normal Behavior |
|--------|-------------------|-----------------|
| Click Project Nimbus | Game stays focused | Game loses focus |
| Drag joystick | Game stays focused | Game loses focus |
| Click button | Game stays focused | Game loses focus |
| Type in game | Input goes to game | Input goes to PN |
| Alt+Tab | Normal switching | Normal switching |

##### Testing Plan

1. **Test A: Simple game (Notepad as proxy)**
   - Open Notepad, type some text
   - Click on Project Nimbus
   - Verify cursor stays in Notepad and typing still works

2. **Test B: Actual game**
   - Launch a game that pauses when unfocused
   - Interact with Project Nimbus
   - Verify game doesn't pause

3. **Test C: Touch input**
   - Same tests but with touchscreen instead of mouse
   - Touch behavior may differ from mouse clicks

##### Potential Issues & Workarounds

| Issue | Workaround |
|-------|------------|
| Qt flag doesn't work | Fall back to Windows API |
| Touch still activates | May need `WM_POINTERACTIVATE` handling |
| Can't close/minimize window | Add keyboard shortcut or system tray |
| Can't resize window | May need to temporarily enable focus for resize |
| Some games still detect focus loss | Try `WS_EX_TOOLWINDOW` style as well |

##### UI/UX Considerations

- **Add toggle in menu:** "Gaming Mode" or "No-Focus Mode" - lets user enable/disable
- **Visual indicator:** Show when no-focus mode is active (colored border?)
- **Default off:** Keep normal behavior by default, user opts in for gaming

##### Code Location

```
src/
├── window_utils.py      # New file for Windows API helpers
├── qt_qml_app.py        # Add no-focus initialization
└── bridge.py            # Add toggle property for QML
qml/
└── Main.qml             # Add menu option and window flags
```

##### Implementation Order

1. Try `Qt.WindowDoesNotAcceptFocus` flag (5 min test)
2. If works → add menu toggle, done
3. If not → implement Windows API approach
4. Add `WS_EX_NOACTIVATE` via ctypes
5. If mouse still activates → add native event filter
6. Test with touch input
7. Add UI toggle and visual indicator

**Verdict:** ⭐ Most promising for single-machine solution - start with Step 1

---

#### ✅ IMPLEMENTATION COMPLETE (Dec 2025)

The Windows API approach has been implemented. Here's what was done:

##### Files Created/Modified

| File | Purpose |
|------|---------|
| `src/window_utils.py` | **NEW** - Windows API helpers for WS_EX_NOACTIVATE |
| `src/bridge.py` | Added `noFocusMode` property and `setWindow()` slot |
| `qml/Main.qml` | Added "Game Focus Mode" toggle in View menu |

##### How It Works

**Approach: Focus Restoration (not WS_EX_NOACTIVATE)**

We tried `WS_EX_NOACTIVATE` first, but it breaks mouse input in Qt - joysticks don't receive drag events properly. Instead, we use a focus restoration approach:

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

4. **Result**: Project Nimbus briefly takes focus (so mouse input works normally), then immediately returns focus to the game when you release.

##### Usage

1. Launch Project Nimbus
2. Start your game
3. Go to **View > Game Focus Mode** (checkbox)
4. Click/touch Project Nimbus - game stays focused!

##### Configuration

Setting is persisted in `controller_config.json`:
```json
{
  "ui": {
    "no_focus_mode": true
  }
}
```

##### Known Limitations

- **Windows only** - Uses Windows API, not available on Mac/Linux
- **Brief focus loss** - Game loses focus momentarily during press, regains on release
- **Some games may detect this** - Games that pause instantly on focus loss may still notice
- **Alt+Tab still switches windows** - This is expected behavior

##### Why Not WS_EX_NOACTIVATE?

We initially tried `WS_EX_NOACTIVATE` which prevents the window from ever taking focus. However, this broke mouse input in Qt:
- Joystick drag operations didn't work
- The window couldn't capture mouse events properly
- VJoy stopped receiving any input

The focus restoration approach is a compromise that works reliably.

##### Future Improvements

- Add visual indicator when game focus mode is active
- Consider using a timer to delay focus restoration (might feel smoother)
- Test with various games to see which detect the brief focus loss

---

### 5. Steam Input + Big Picture Mode

**What it does:** Steam's built-in controller support with overlay.

**How it could help:**
- Steam handles controller input at a lower level
- Big Picture mode designed for controller-only use
- On-screen keyboard and overlays don't steal focus

**Pros:**
- Already integrated with many games
- Handles focus properly
- Works with vJoy (already confirmed)

**Cons:**
- Only works with Steam games
- Big Picture mode is clunky
- Doesn't solve the UI for Project Nimbus itself

**Verdict:** ✅ Partial solution - good for Steam games but doesn't address our UI

---

### 6. Remote Desktop / Second Display

**What it does:** Run Project Nimbus on a tablet via remote desktop to the main PC.

**How it could help:**
- Tablet shows only Project Nimbus
- Main PC screen shows game (stays focused)
- Input goes directly to vJoy on main PC

**Pros:**
- Simple concept
- Game always has focus on main display
- Works with any game

**Cons:**
- Need a tablet or second device
- Remote desktop latency
- Setup complexity

**Verdict:** 🔬 Practical workaround - worth documenting as an option

---

## Open Problems

### 🔴 Mouse Capture by Games

**The Problem:**
Some games capture/lock the mouse cursor, preventing the user from clicking on Project Nimbus at all. This is a significant accessibility barrier for users who cannot use a keyboard to Alt+Tab.

**Current Workaround:**
- Have a caregiver press Alt+Tab to switch focus
- Once Project Nimbus has focus, it works normally
- Game Focus Mode then restores focus to the game after each interaction

**Potential Solutions to Research:**

1. **Borderless Windowed Mode**
   - Many games have a "Borderless Windowed" or "Windowed Fullscreen" option
   - This typically doesn't capture the mouse
   - User can move cursor to Project Nimbus on a second monitor or overlay

2. **Multi-Monitor Setup**
   - Game on primary monitor (even fullscreen)
   - Project Nimbus on secondary monitor/tablet
   - Some games release mouse at screen edges

3. **Global Hotkey to Release Mouse**
   - Implement a global hotkey (e.g., F12) that forces mouse release
   - Would require low-level keyboard hook
   - Could trigger Alt+Tab programmatically

4. **Overlay Mode**
   - Run Project Nimbus as a game overlay (like Steam Overlay)
   - Would require significant architectural changes
   - May conflict with anti-cheat systems

5. **Touch Input Device**
   - Use a separate touchscreen/tablet for Project Nimbus
   - Touch input may not be captured by the game
   - Could use Spacedesk or similar for wireless display

6. **Steam Input / Big Picture**
   - Steam's overlay can work even when games capture mouse
   - Could potentially integrate with Steam Input API

**Priority:** HIGH - This is a core accessibility issue that prevents independent use.

---

## Completed

- ✅ **Game Focus Mode** - Implemented focus restoration approach (Dec 2025)
- ✅ **Borderless Gaming Integration** - Documented in README

## Next Steps

1. **Research overlay solutions** - Can we run as a game overlay?
2. **Test multi-monitor behavior** - Do games release mouse at screen edges?
3. **Investigate global hotkeys** - Can we implement Alt+Tab trigger?
4. **Research Moonlight** - Check if self-streaming or vJoy passthrough works

## Notes

- The core issue is that Windows gives focus to whatever window receives user input
- Touch input is treated the same as mouse clicks for focus purposes
- Some games have "background input" options that help, but many don't
- Controller input (XInput/DirectInput) typically requires window focus unless app specifically handles background input
- **Mouse capture is a separate problem from focus** - even with Game Focus Mode, if the game captures the mouse, the user can't click on Project Nimbus at all

