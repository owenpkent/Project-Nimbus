# Keyboard Output — Native Keystroke Emission

## The Goal

Enable any Nimbus button or widget to emit **keyboard keystrokes and shortcuts** directly to the foreground application — with no external software, no additional downloads, and fully bundled in the installer.

This is the missing output mode that makes Nimbus useful for **productivity apps, AAC, streaming, and any application that doesn't accept controller input** (see [MODULAR_CONTROL_SURFACE.md](MODULAR_CONTROL_SURFACE.md)).

---

## Why No External Dependencies

The existing codebase already uses `ctypes.windll.user32` in `src/window_utils.py` (for `WS_EX_NOACTIVATE`, `SetForegroundWindow`) and in `src/bridge.py` (for `ClipCursor`, `ClientToScreen`). The Windows `SendInput` API lives in the same `user32.dll` — **no new DLL, no new library, no pip install**.

This means the keyboard output module:
- Ships inside the PyInstaller bundle with zero extra size
- Works on any Windows 10/11 machine (no driver install, unlike vJoy)
- Requires no admin rights to use
- Cannot be blocked by antivirus (it's the same API Word and Chrome use)

Compare to alternatives:

| Approach | Dependencies | Bundleable | Admin Required |
|----------|-------------|-----------|----------------|
| **`ctypes` + `SendInput`** (recommended) | None — `user32.dll` is always present | ✅ Yes | ❌ No |
| `pyautogui` | PIL, numpy, pyobjc | ⚠️ Large | ❌ No |
| `pynput` | Xlib / AppKit / win32 | ⚠️ Complex | ❌ No |
| `keyboard` library | Low-level hook driver | ⚠️ Sometimes | ✅ Sometimes |
| `pywin32` / `win32api` | win32 extension DLLs | ⚠️ Extra DLLs | ❌ No |

---

## How `SendInput` Works

`SendInput` is the Windows API for injecting synthetic keyboard and mouse events. It's the same mechanism used by accessibility software (Dragon NaturallySpeaking, JAWS, Windows On-Screen Keyboard). Games and applications cannot distinguish `SendInput` events from real keystrokes.

```
Nimbus button pressed (QML → bridge.py setButton())
    ↓
KeyboardInterface.set_button(button_id, pressed=True)
    ↓
Lookup: button_id → key mapping (e.g., button 1 → Ctrl+Z)
    ↓
Build INPUT struct with KEYBDINPUT
    ↓
ctypes.windll.user32.SendInput(...)
    ↓
Foreground application receives keystroke
```

The key point: **Nimbus sends the keystroke to the foreground window**, not to itself. Because Nimbus uses Game Focus Mode (`WS_EX_NOACTIVATE`) to avoid stealing focus, the game or productivity app stays in the foreground and receives the input directly.

---

## Implementation: `src/keyboard_interface.py`

This module follows the exact same duck-type interface as `VJoyInterface` and `ViGEmInterface` — it implements `set_button()` and `update_axis()` so it can be dropped into `bridge.py` as a third output mode with minimal changes.

```python
"""
Keyboard output interface for Nimbus Adaptive Controller.

Emits synthetic keystrokes via Windows SendInput API (user32.dll).
No external dependencies — user32.dll is always present on Windows.

Follows the same duck-type interface as VJoyInterface and ViGEmInterface:
    set_button(button_id: int, pressed: bool) -> bool
    update_axis(axis: str, value: float) -> bool
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import Any

KEYBOARD_AVAILABLE = sys.platform == "win32"

if KEYBOARD_AVAILABLE:
    user32 = ctypes.windll.user32

    # SendInput constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_UNICODE = 0x0004

    # Virtual key codes (subset — extend as needed)
    # Full list: https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    VK_CODES: dict[str, int] = {
        # Letters
        **{c: ord(c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"},
        # Numbers
        **{str(n): ord(str(n)) for n in range(10)},
        # Modifiers
        "ctrl": 0x11, "lctrl": 0x11, "rctrl": 0xA3,
        "shift": 0x10, "lshift": 0xA0, "rshift": 0xA1,
        "alt": 0x12, "lalt": 0x12, "ralt": 0xA5,
        "win": 0x5B,
        # Function keys
        **{f"f{n}": 0x6F + n for n in range(1, 13)},
        # Navigation
        "enter": 0x0D, "return": 0x0D,
        "escape": 0x1B, "esc": 0x1B,
        "space": 0x20,
        "tab": 0x09,
        "backspace": 0x08,
        "delete": 0x2E,
        "insert": 0x2D,
        "home": 0x24,
        "end": 0x23,
        "pageup": 0x21,
        "pagedown": 0x22,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
        # Media
        "play_pause": 0xB3,
        "next_track": 0xB0,
        "prev_track": 0xB1,
        "volume_up": 0xAF,
        "volume_down": 0xAE,
        "mute": 0xAD,
        # Misc
        "printscreen": 0x2C,
        "numlock": 0x90,
        "capslock": 0x14,
        "semicolon": 0xBA,
        "equals": 0xBB,
        "comma": 0xBC,
        "minus": 0xBD,
        "period": 0xBE,
        "slash": 0xBF,
        "grave": 0xC0,
        "lbracket": 0xDB,
        "backslash": 0xDC,
        "rbracket": 0xDD,
        "quote": 0xDE,
    }

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT_UNION)]


def _send_key(vk_code: int, key_up: bool = False) -> None:
    """Send a single virtual key event via SendInput."""
    if not KEYBOARD_AVAILABLE:
        return
    flags = KEYEVENTF_KEYUP if key_up else 0
    # Mark extended keys (navigation, right-side modifiers)
    if vk_code in (0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                   0x2D, 0x2E, 0xA3, 0xA5):
        flags |= KEYEVENTF_EXTENDEDKEY
    inp = INPUT(
        type=INPUT_KEYBOARD,
        _input=_INPUT_UNION(ki=KEYBDINPUT(
            wVk=vk_code,
            wScan=0,
            dwFlags=flags,
            time=0,
            dwExtraInfo=None,
        ))
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _send_combo(keys: list[str], key_up: bool = False) -> None:
    """
    Send a key combination (e.g. ['ctrl', 'z'] for Ctrl+Z).
    On press: send modifiers first, then the main key.
    On release: reverse order.
    """
    vk_list = [VK_CODES.get(k.lower(), 0) for k in keys]
    vk_list = [v for v in vk_list if v]  # filter unknowns
    if key_up:
        vk_list = list(reversed(vk_list))
    for vk in vk_list:
        _send_key(vk, key_up=key_up)


class KeyMapping:
    """
    Maps a button_id to a key combination.

    key_combo: list of key name strings, e.g. ['ctrl', 'z'] or ['f5'] or ['space']
    hold: if True, key is held while button is held; if False, tap on press only
    """
    def __init__(self, key_combo: list[str], hold: bool = True):
        self.key_combo = key_combo
        self.hold = hold


class KeyboardInterface:
    """
    Keyboard output interface — drop-in alongside VJoyInterface / ViGEmInterface.

    Usage in bridge.py:
        self._keyboard = KeyboardInterface()
        self._keyboard.set_mapping(1, ['ctrl', 'z'])   # Button 1 → Ctrl+Z
        self._keyboard.set_mapping(2, ['ctrl', 'shift', 's'])  # Button 2 → Ctrl+Shift+S

    Then in setButton():
        if self._output_mode == 'keyboard':
            self._keyboard.set_button(button_id, pressed)
    """

    def __init__(self) -> None:
        self.is_connected: bool = KEYBOARD_AVAILABLE
        # button_id → KeyMapping
        self._mappings: dict[int, KeyMapping] = {}
        # axis → key pairs for axis-to-key (e.g. slider → volume up/down)
        self._axis_mappings: dict[str, tuple[str, str]] = {}
        self._axis_thresholds: dict[str, float] = {}
        self._axis_state: dict[str, bool] = {}  # track which direction is active

    def set_mapping(self, button_id: int, key_combo: list[str], hold: bool = True) -> None:
        """Assign a key combination to a button ID."""
        self._mappings[button_id] = KeyMapping(key_combo, hold)

    def set_axis_mapping(
        self,
        axis: str,
        positive_key: str,
        negative_key: str,
        threshold: float = 0.5,
    ) -> None:
        """
        Map an axis to two keys (positive direction / negative direction).
        e.g. set_axis_mapping('x', 'right', 'left') for arrow key steering.
        e.g. set_axis_mapping('z', 'volume_up', 'volume_down', threshold=0.3)
        """
        self._axis_mappings[axis] = (positive_key, negative_key)
        self._axis_thresholds[axis] = threshold
        self._axis_state[axis] = False  # False = neither direction active

    def load_from_profile(self, profile: dict) -> None:
        """
        Load key mappings from a profile dict.

        Expected profile format:
        {
            "keyboard_mappings": {
                "1": {"keys": ["ctrl", "z"], "hold": true},
                "2": {"keys": ["ctrl", "shift", "s"], "hold": false},
                "3": {"keys": ["f5"], "hold": true}
            },
            "keyboard_axis_mappings": {
                "x": {"positive": "right", "negative": "left", "threshold": 0.5},
                "y": {"positive": "down", "negative": "up", "threshold": 0.5}
            }
        }
        """
        for btn_str, mapping in profile.get("keyboard_mappings", {}).items():
            try:
                btn_id = int(btn_str)
                self.set_mapping(btn_id, mapping["keys"], mapping.get("hold", True))
            except (ValueError, KeyError):
                pass

        for axis, mapping in profile.get("keyboard_axis_mappings", {}).items():
            try:
                self.set_axis_mapping(
                    axis,
                    mapping["positive"],
                    mapping["negative"],
                    mapping.get("threshold", 0.5),
                )
            except KeyError:
                pass

    # --- Duck-type interface matching VJoyInterface / ViGEmInterface ---

    def set_button(self, button_id: int, pressed: bool) -> bool:
        """
        Press or release the key(s) mapped to button_id.
        Returns True if a mapping existed and was sent.
        """
        if not KEYBOARD_AVAILABLE:
            return False
        mapping = self._mappings.get(button_id)
        if not mapping:
            return False
        if mapping.hold:
            _send_combo(mapping.key_combo, key_up=not pressed)
        else:
            # Tap mode: only fire on press, not on release
            if pressed:
                _send_combo(mapping.key_combo, key_up=False)
                time.sleep(0.02)  # 20ms hold — enough for any app to register
                _send_combo(mapping.key_combo, key_up=True)
        return True

    def update_axis(self, axis: str, value: float) -> bool:
        """
        Convert an axis value to key presses.
        Positive threshold → positive_key held; negative threshold → negative_key held.
        Between thresholds → both released.
        """
        if not KEYBOARD_AVAILABLE:
            return False
        if axis not in self._axis_mappings:
            return False

        pos_key, neg_key = self._axis_mappings[axis]
        threshold = self._axis_thresholds.get(axis, 0.5)
        prev_state = self._axis_state.get(axis, 0)  # -1, 0, +1

        if value > threshold:
            new_state = 1
        elif value < -threshold:
            new_state = -1
        else:
            new_state = 0

        if new_state == prev_state:
            return True  # No change

        # Release previous
        if prev_state == 1:
            _send_key(VK_CODES.get(pos_key.lower(), 0), key_up=True)
        elif prev_state == -1:
            _send_key(VK_CODES.get(neg_key.lower(), 0), key_up=True)

        # Press new
        if new_state == 1:
            _send_key(VK_CODES.get(pos_key.lower(), 0), key_up=False)
        elif new_state == -1:
            _send_key(VK_CODES.get(neg_key.lower(), 0), key_up=False)

        self._axis_state[axis] = new_state
        return True

    def release_all(self) -> None:
        """Release all currently held keys. Call on profile switch or app exit."""
        for mapping in self._mappings.values():
            _send_combo(mapping.key_combo, key_up=True)
        for axis, (pos_key, neg_key) in self._axis_mappings.items():
            state = self._axis_state.get(axis, 0)
            if state == 1:
                _send_key(VK_CODES.get(pos_key.lower(), 0), key_up=True)
            elif state == -1:
                _send_key(VK_CODES.get(neg_key.lower(), 0), key_up=True)
        self._axis_state = {k: 0 for k in self._axis_state}

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self.is_connected,
            "platform": sys.platform,
            "mappings": {k: v.key_combo for k, v in self._mappings.items()},
        }
```

---

## Integration into `bridge.py`

The `KeyboardInterface` follows the same duck-type contract as `VJoyInterface` and `ViGEmInterface`. Adding it to `bridge.py` requires three small changes:

### 1. Import and instantiate

```python
# In bridge.py __init__, alongside _vjoy and _vigem:
from .keyboard_interface import KeyboardInterface, KEYBOARD_AVAILABLE

self._keyboard: Optional[KeyboardInterface] = None
self._use_keyboard = False
```

### 2. Add to `_get_active_interface()`

```python
def _get_active_interface(self):
    if self._use_keyboard and self._keyboard:
        return self._keyboard
    if self._use_vigem and self._vigem:
        return self._vigem
    return self._vjoy
```

### 3. Add a QML-callable slot to switch modes

```python
@Slot(str)
def setOutputMode(self, mode: str) -> None:
    """Switch output mode: 'vjoy', 'vigem', or 'keyboard'."""
    if mode == "keyboard":
        if self._keyboard is None:
            self._keyboard = KeyboardInterface()
        # Load keyboard mappings from current profile
        profile_data = self._config.get_profile_data()
        self._keyboard.load_from_profile(profile_data)
        self._use_keyboard = True
        self._use_vigem = False
    elif mode == "vigem":
        self._use_keyboard = False
        self._use_vigem = True
    else:  # vjoy
        self._use_keyboard = False
        self._use_vigem = False
```

---

## Profile Format Extension

Keyboard mappings live in the existing JSON profile system alongside the current axis mappings. No new file format needed — just new keys in the same profile JSON:

```json
{
  "profile_id": "photoshop_drawing",
  "layout_type": "custom",
  "output_mode": "keyboard",
  "keyboard_mappings": {
    "1":  { "keys": ["ctrl", "z"],          "hold": false },
    "2":  { "keys": ["ctrl", "shift", "z"], "hold": false },
    "3":  { "keys": ["b"],                  "hold": false },
    "4":  { "keys": ["e"],                  "hold": false },
    "5":  { "keys": ["ctrl", "s"],          "hold": false },
    "6":  { "keys": ["ctrl", "shift", "s"], "hold": false },
    "7":  { "keys": ["lbracket"],           "hold": true  },
    "8":  { "keys": ["rbracket"],           "hold": true  }
  },
  "keyboard_axis_mappings": {
    "z": {
      "positive": "rbracket",
      "negative": "lbracket",
      "threshold": 0.3
    }
  }
}
```

The `output_mode` field tells `bridge.py` which interface to activate when this profile loads. Existing profiles without `output_mode` default to `"vjoy"` or `"vigem"` as before — **fully backwards compatible**.

---

## Example Profiles

### Photoshop / Clip Studio Paint

| Button | Keys | Action |
|--------|------|--------|
| 1 | `Ctrl+Z` | Undo |
| 2 | `Ctrl+Shift+Z` | Redo |
| 3 | `B` | Brush tool |
| 4 | `E` | Eraser tool |
| 5 | `Ctrl+S` | Save |
| 6 | `Ctrl+Shift+S` | Save As |
| 7 | `[` (hold) | Brush size down |
| 8 | `]` (hold) | Brush size up |
| Slider Z | `[` / `]` | Brush size via slider |

### DaVinci Resolve — Editing

| Button | Keys | Action |
|--------|------|--------|
| 1 | `Ctrl+Z` | Undo |
| 2 | `Space` | Play/Pause |
| 3 | `Ctrl+B` | Blade (cut) |
| 4 | `Delete` | Ripple delete |
| 5 | `M` | Add marker |
| 6 | `Ctrl+Shift+,` | Go to previous edit |
| 7 | `Ctrl+Shift+.` | Go to next edit |
| Slider X | `Left` / `Right` | Frame step (hold) |

### OBS Studio — Streaming

| Button | Keys | Action |
|--------|------|--------|
| 1 | `F1` | Scene 1 |
| 2 | `F2` | Scene 2 |
| 3 | `F3` | Scene 3 |
| 4 | `F4` | Scene 4 |
| 5 | `Ctrl+Shift+R` | Start/stop recording |
| 6 | `Ctrl+Shift+M` | Mute mic |

### AAC Quick Phrases (via TTS — future)

For AAC use, buttons map to phrases rather than keys. This requires the TTS output extension described in [AAC_INTEGRATION.md](AAC_INTEGRATION.md). The keyboard output mode is the stepping stone — the same `set_button()` dispatch point that calls `_send_combo()` can instead call `pyttsx3.say()`.

---

## Unicode / Text Output

For AAC or text input use cases, `SendInput` also supports Unicode character injection directly — no virtual key lookup needed:

```python
def send_unicode_string(text: str) -> None:
    """Type a full string of Unicode characters via SendInput."""
    inputs = []
    for char in text:
        for key_up in (False, True):
            inp = INPUT(
                type=INPUT_KEYBOARD,
                _input=_INPUT_UNION(ki=KEYBDINPUT(
                    wVk=0,
                    wScan=ord(char),
                    dwFlags=KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0),
                    time=0,
                    dwExtraInfo=None,
                ))
            )
            inputs.append(inp)
    ArrayType = INPUT * len(inputs)
    user32.SendInput(len(inputs), ArrayType(*inputs), ctypes.sizeof(INPUT))
```

This lets a button emit an entire phrase as typed text — useful for AAC phrase buttons before a full TTS engine is integrated.

---

## Key Safety Considerations

### Stuck Keys

If Nimbus crashes or the profile switches while a key is held, the key stays stuck in the OS. Mitigations:

1. **`release_all()` on profile switch** — already in the interface; call from `bridge.py` when `setOutputMode()` or `loadProfile()` is called
2. **`release_all()` on app exit** — hook into `QApplication.aboutToQuit`
3. **Hold-mode timeout** — optionally auto-release held keys after N ms with no update

### Focus Requirement

`SendInput` sends to the **foreground window**. If Nimbus accidentally steals focus (e.g., a dialog opens), keystrokes go to Nimbus instead of the target app. This is already solved by Game Focus Mode (`WS_EX_NOACTIVATE`) in `window_utils.py` — keyboard output mode should always run with no-focus mode enabled.

### Modifier Leak

If a combo like `Ctrl+Z` is interrupted mid-send (e.g., `Ctrl` down, then crash before `Z`), `Ctrl` stays held. `release_all()` handles this, but the `_send_combo()` implementation sends all keys in a single `SendInput` batch where possible to minimize the window for this.

---

## Testing Without a Target App

```python
# Quick test — run standalone, open Notepad first
import time
from src.keyboard_interface import KeyboardInterface

kb = KeyboardInterface()
kb.set_mapping(1, ['ctrl', 'z'])           # Undo
kb.set_mapping(2, ['ctrl', 'shift', 'z'])  # Redo
kb.set_mapping(3, ['a', 'b', 'c'])         # Won't work as combo — use send_unicode_string

time.sleep(2)  # Switch to Notepad in this 2 seconds
kb.set_button(1, pressed=True)
time.sleep(0.05)
kb.set_button(1, pressed=False)
```

---

## PyInstaller Bundling

Because `keyboard_interface.py` uses only `ctypes` (stdlib) and `user32.dll` (always present on Windows), **no special PyInstaller hooks are needed**. The module bundles automatically with the rest of `src/`.

Verify with:
```
pyinstaller --onefile --collect-all src ...
```

`user32.dll` is a Windows system DLL — PyInstaller never needs to bundle it.

---

## Implementation Checklist

- [ ] Create `src/keyboard_interface.py` with `KeyboardInterface` class
- [ ] Add `output_mode` field to profile JSON schema in `src/config.py`
- [ ] Add `KeyboardInterface` instantiation to `bridge.py __init__`
- [ ] Add `setOutputMode()` slot to `bridge.py`
- [ ] Update `_get_active_interface()` in `bridge.py` to check keyboard mode
- [ ] Call `release_all()` on profile switch and app exit
- [ ] Add `keyboard_mappings` editor to the profile/settings UI (QML)
- [ ] Ship 3–5 pre-built keyboard profiles (Photoshop, DaVinci, OBS)
- [ ] Add `send_unicode_string()` for AAC text output (Phase 2)

---

## Related Documents

- [Modular Control Surface](MODULAR_CONTROL_SURFACE.md) — keyboard output is what enables non-gaming use cases
- [AAC Integration](AAC_INTEGRATION.md) — keyboard output is the first step toward phrase/TTS output
- [Hardware Integration](HARDWARE_INTEGRATION.md) — physical adaptive hardware input → keyboard output pipeline
- [Voice Command Integration](../distribution/VOICE_COMMAND.md) — voice commands can trigger keyboard output too
