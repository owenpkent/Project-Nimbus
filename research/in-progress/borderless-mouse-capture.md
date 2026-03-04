# Borderless Mode & Mouse Capture Release

**Status:** 🟡 In Progress — Research + Sample Code  
**Related:** `research/in-progress/mouse-capture-problem.md`

## The Goal

Allow users to interact with Project Nimbus even when a game has captured the mouse.
Two complementary problems need solving:

1. **Game is in exclusive fullscreen** — mouse is locked to the game's window and can't reach Nimbus at all
2. **Game is windowed but still clips the cursor** — game calls `ClipCursor()` to confine the mouse to its own rect

This document covers both, plus what *can't* be solved without going too deep into game internals.

---

## How Games Capture the Mouse — Three Mechanisms

Understanding which mechanism a game uses determines which solution works.

### 1. `ClipCursor(rect)` — Most Common
The game calls `ClipCursor` with its window rect. Windows then refuses to let the cursor leave that rectangle, even in windowed mode.

**Key fact:** `ClipCursor` is a **global, shared desktop resource** — any process can release it by calling `ClipCursor(NULL)`. It is not per-process. This is how we can fight it from outside the game.

```python
import ctypes
ctypes.windll.user32.ClipCursor(None)  # Releases the lock from any process
```

**Catch:** Most games re-apply `ClipCursor` every frame in their input loop, so releasing it once is a race condition. You need to keep releasing it faster than the game re-applies it (see the polling approach below).

### 2. Exclusive Fullscreen — Renders on top of everything
When a game runs in exclusive fullscreen (`DXGI_SWAP_EFFECT_DISCARD`, old DirectX modes), Windows gives it full control of the display. No other window can appear on top, so Nimbus literally can't be seen or clicked.

**Solution:** Force the game into borderless windowed mode (see below). Once it's a normal window, the OS desktop compositing takes over and Nimbus can overlay or sit beside it.

### 3. Raw Input (`RegisterRawInputDevices`) — The Hard Case
The game registers for raw HID mouse input, reading mouse *delta* directly from the device driver. It doesn't use the cursor at all — so `ClipCursor` and cursor position are irrelevant. The game just moves its camera based on raw delta.

**This cannot be solved from outside the game process** without DLL injection (which triggers anti-cheat). For Raw Input games, the solution is purely hardware/setup: second monitor, tablet, or streaming (see `mouse-capture-problem.md` solutions 2, 5, 6).

Most modern FPS games (Valorant, CS2, Fortnite) use Raw Input. Older and indie games typically use `ClipCursor`.

---

## Solution A: Force Borderless Windowed Mode

Derived from the **NoMoreBorder** project (MIT License — https://github.com/invcble/NoMoreBorder).

This strips a game window's border/title bar decorations using Win32 style flags, then repositions and resizes it to fill the screen. The result looks like fullscreen but is actually a normal window — which means:
- The OS desktop compositor is active
- Other windows (including Nimbus) can appear on top or beside it
- `ClipCursor` from the game typically only covers its own window rect, which is now the full screen, so it doesn't actually confine in practice when Nimbus is on a second monitor

### How It Works

```python
import ctypes
import ctypes.wintypes as wintypes

user32 = ctypes.windll.user32

def get_window_handle(title_substring: str) -> int | None:
    """Find a window by partial title match. Returns hwnd or None."""
    result = []

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_substring.lower() in buf.value.lower():
                result.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result[0] if result else None


def make_borderless(hwnd: int, x: int, y: int, width: int, height: int) -> bool:
    """
    Strip window borders and resize to fill the screen.
    Equivalent to borderless windowed/fullscreen mode.

    hwnd   - window handle from get_window_handle()
    x, y   - top-left position (usually 0, 0 for primary monitor)
    width  - target width in pixels
    height - target height in pixels
    """
    # Win32 style constants
    WS_CAPTION     = 0x00C00000  # Title bar + border
    WS_THICKFRAME  = 0x00040000  # Resizable border
    WS_MINIMIZE    = 0x20000000
    WS_MAXIMIZE    = 0x01000000
    WS_SYSMENU     = 0x00080000
    GWL_STYLE      = -16
    GWL_EXSTYLE    = -20
    WS_EX_DLGMODALFRAME = 0x00000001
    WS_EX_WINDOWEDGE    = 0x00000100
    WS_EX_CLIENTEDGE    = 0x00000200
    WS_EX_STATICEDGE    = 0x00020000
    SWP_NOZORDER    = 0x0004
    SWP_FRAMECHANGED = 0x0020

    try:
        # Read current styles
        style    = user32.GetWindowLongW(hwnd, GWL_STYLE)
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        # Strip decorations
        style    &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZE | WS_MAXIMIZE | WS_SYSMENU)
        ex_style &= ~(WS_EX_DLGMODALFRAME | WS_EX_WINDOWEDGE | WS_EX_CLIENTEDGE | WS_EX_STATICEDGE)

        # Apply
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

        # Force frame recalculation, then resize
        user32.SetWindowPos(
            hwnd, 0, x, y, width, height,
            SWP_NOZORDER | SWP_FRAMECHANGED
        )
        return True
    except Exception as e:
        print(f"make_borderless failed: {e}")
        return False


def restore_window(hwnd: int, x: int, y: int, width: int, height: int) -> bool:
    """Restore window decorations (undo make_borderless)."""
    WS_CAPTION    = 0x00C00000
    WS_THICKFRAME = 0x00040000
    WS_SYSMENU    = 0x00080000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    GWL_STYLE      = -16
    HWND_TOP       = 0
    SWP_NOZORDER   = 0x0004
    SWP_FRAMECHANGED = 0x0020

    try:
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style |= WS_CAPTION | WS_THICKFRAME | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        user32.SetWindowPos(hwnd, HWND_TOP, x, y, width, height, SWP_NOZORDER | SWP_FRAMECHANGED)
        return True
    except Exception as e:
        print(f"restore_window failed: {e}")
        return False
```

### Usage
```python
import ctypes.wintypes as wintypes

# Get primary monitor size
user32 = ctypes.windll.user32
screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)

hwnd = get_window_handle("Elden Ring")
if hwnd:
    make_borderless(hwnd, 0, 0, screen_w, screen_h)
    print("Game is now borderless windowed")
```

### Limitations
- Only works while the game is already running in **windowed mode** (not exclusive fullscreen). Some games must be set to windowed in their in-game options first before this tool can strip the border.
- A few games re-apply their window style every few frames. Those will "fight back" — the window will flicker. In practice this is rare.
- Does **not** help with Raw Input games.
- Requires `pywin32` OR can be done with pure `ctypes` (sample above uses pure ctypes — no extra dependency).

---

## Solution B: `ClipCursor(NULL)` Polling

Since `ClipCursor` is a shared resource, we can release it repeatedly on a background timer. When Nimbus wants mouse access (e.g. user is about to tap the UI), we start a timer that calls `ClipCursor(NULL)` at ~100ms intervals.

```python
import ctypes
import threading

_release_timer: threading.Timer | None = None
_releasing = False

def _release_tick():
    """Called repeatedly to keep the cursor unclipped."""
    global _release_timer
    if _releasing:
        ctypes.windll.user32.ClipCursor(None)
        _release_timer = threading.Timer(0.1, _release_tick)
        _release_timer.daemon = True
        _release_timer.start()

def start_cursor_release():
    """Begin continuously releasing cursor clip. Call when Nimbus needs mouse access."""
    global _releasing, _release_timer
    if _releasing:
        return
    _releasing = True
    _release_tick()
    print("Cursor release: started")

def stop_cursor_release():
    """Stop releasing cursor clip. Call when done with Nimbus, game can re-claim."""
    global _releasing, _release_timer
    _releasing = False
    if _release_timer:
        _release_timer.cancel()
        _release_timer = None
    print("Cursor release: stopped")
```

### Practical integration with Nimbus

The natural trigger points in the existing codebase are:
- **Start releasing** when the user presses a dedicated "use Nimbus" button in their controller profile, or when a touch begins on the Nimbus window
- **Stop releasing** when the interaction is done and Game Focus Mode restores focus to the game

`bridge.py` already has `unclipCursor()` at line 263 — this polling approach builds on that same call, just made continuous.

### Limitations
- Race condition with fast games (≤16ms input loop) — 100ms polling means the cursor is re-clipped for up to 100ms. A tighter interval (16ms) reduces this but uses more CPU.
- Has no effect on Raw Input games (cursor is irrelevant to them).
- When `stop_cursor_release()` is called, the game will re-clip within one of its own frames — this is the desired behavior.

---

## Solution C: `WH_MOUSE_LL` Global Hook (Advanced)

A `WH_MOUSE_LL` (low-level mouse) hook runs in **our** process's message loop and receives mouse events system-wide before they are delivered anywhere else. This is how accessibility tools intercept mouse input.

This is more powerful than polling but requires:
- A live Win32 message loop on the thread that installs the hook
- For Windows Store apps / some protected processes: `UIAccess=true` in the app manifest (which Nimbus is already pursuing for the signing/UAC work)

```python
import ctypes
import ctypes.wintypes as wintypes
import threading

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200

user32 = ctypes.WinDLL('user32', use_last_error=True)

# Must keep a reference to the callback to prevent GC
_hook_handle = None
_hook_callback = None

def _low_level_mouse_proc(n_code, w_param, l_param):
    """
    Called for every system-wide mouse event.
    Return 0 and call CallNextHookEx to pass the event through normally.
    Returning a non-zero value (without calling next) suppresses the event —
    use with extreme care, suppressing input is hostile to the user.
    """
    if n_code >= 0:
        # Example: log mouse position when cursor is moving
        if w_param == WM_MOUSEMOVE:
            ms = ctypes.cast(l_param, ctypes.POINTER(wintypes.POINT)).contents
            # Could redirect this event, check bounds, etc.
            pass

    return user32.CallNextHookEx(_hook_handle, n_code, w_param, l_param)

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

def install_mouse_hook():
    global _hook_handle, _hook_callback
    _hook_callback = HOOKPROC(_low_level_mouse_proc)
    _hook_handle = user32.SetWindowsHookExW(
        WH_MOUSE_LL,
        _hook_callback,
        None,   # hMod — NULL for WH_MOUSE_LL (runs in our process)
        0       # dwThreadId — 0 = global hook
    )
    if not _hook_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    print(f"Mouse hook installed: {_hook_handle}")

def uninstall_mouse_hook():
    global _hook_handle
    if _hook_handle:
        user32.UnhookWindowsHookEx(_hook_handle)
        _hook_handle = None
        print("Mouse hook removed")

def run_hook_message_loop():
    """
    WH_MOUSE_LL requires a message loop on the installing thread.
    Run this in a dedicated daemon thread.
    """
    install_mouse_hook()
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    uninstall_mouse_hook()
```

**Practical use case for Nimbus:** Rather than suppressing input, the hook could detect when the cursor is being pushed against a `ClipCursor` boundary, and automatically trigger `start_cursor_release()` — essentially detecting when the user is *trying* to reach Nimbus but being blocked.

### Important notes
- `WH_MOUSE_LL` does **not** inject into other processes — it runs entirely in Nimbus's own process. This means it works without admin rights.
- It does **not** bypass `ClipCursor` — it receives the event *after* the cursor position has already been clamped. It can detect the clamping (cursor not moving despite events) but can't prevent it alone.
- Combined with Solution B (polling `ClipCursor(NULL)`), this becomes a smart release trigger.

---

## What Cannot Be Solved (The Hard Wall)

| Scenario | Why it can't be fixed externally |
|---|---|
| Modern FPS with Raw Input (Valorant, CS2, Fortnite) | Mouse delta read from HID driver; cursor/ClipCursor are irrelevant |
| Games with anti-cheat (EAC, BattleEye) | Any DLL injection or process memory access triggers a ban |
| Exclusive fullscreen that re-takes display ownership | Only fixable from inside the game settings (or GPU driver tricks) |

For these cases, the only real solutions remain: second monitor/display, tablet as separate input device, or streaming the game (see `mouse-capture-problem.md`).

---

## Integration Plan for Nimbus

### New module: `src/borderless.py`
A clean, self-contained module with no new dependencies (pure `ctypes`):

```
src/borderless.py
  - get_window_handle(title_substring) -> int | None
  - make_borderless(hwnd, x, y, w, h) -> bool
  - restore_window(hwnd, x, y, w, h) -> bool
  - start_cursor_release(interval_ms=100)
  - stop_cursor_release()
  - get_clip_cursor_rect() -> tuple | None   # diagnostic: what rect is currently clipped?
```

### `bridge.py` additions
- `startCursorRelease()` / `stopCursorRelease()` Qt slots — wrap the polling timer
- `makeGameBorderless(window_title)` slot — calls `make_borderless()` with primary screen dims
- `restoreGameWindow(window_title)` slot — calls `restore_window()`

These slots can be called from QML buttons or wired to controller profile button bindings.

### `unclipCursor()` already exists
`bridge.py` line 263 already implements a one-shot `ClipCursor(None)`. The polling wrapper just calls this repeatedly.

### Dependencies
No new dependencies required. Pure `ctypes` (stdlib). `pywin32` is **not** needed for this approach — the NoMoreBorder `win32gui` calls can be replaced with equivalent `ctypes` calls as shown above.

---

## Testing Approach

1. **Test with Minecraft** (Java Edition, windowed) — uses `ClipCursor`. Solution B should work.
2. **Test with an older DirectX game** (e.g. Skyrim in windowed mode) — Solution A + B combined.
3. **Test with a Raw Input game** (e.g. CS2) — confirm that none of these solutions work, and document it clearly for users.
4. **Regression:** Confirm existing Game Focus Mode (`noFocusMode`) still works correctly alongside cursor release.

---

## References

- NoMoreBorder source (MIT): https://github.com/invcble/NoMoreBorder
- `ClipCursor` MSDN: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-clipcursor
- `SetWindowsHookExA` MSDN: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowshookexa
- `LowLevelMouseProc` MSDN: https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelmouseproc
- Related Nimbus research: `research/in-progress/mouse-capture-problem.md`
- UIAccess signing strategy: `research/roadmap/uiaccess-signing-strategy.md`
