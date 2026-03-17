"""
Controller Mode Enforcement for Project Nimbus.

Makes games voluntarily release the mouse by keeping them in "controller mode."

Most modern games have dual input detection:
  - Mouse/keyboard input detected → M/KB mode → cursor captured, mouse prompts
  - Controller input detected → Controller mode → cursor RELEASED, gamepad prompts

Since Project Nimbus already creates a virtual Xbox 360 controller via ViGEm,
we can exploit this by:
  1. Sending a constant stream of controller keep-alive signals (tiny stick
     oscillations below deadzone) so the game stays in controller mode
  2. Optionally using a WH_MOUSE_LL hook to detect mouse-over-game events and
     immediately counter them with a burst of controller input
  3. Combining with ClipCursor(NULL) release so the cursor stays free

This approach makes the game VOLUNTARILY stop capturing the mouse, rather than
fighting ClipCursor in a race condition.

Pure ctypes implementation — no extra dependencies beyond vgamepad (already required).

See: research/in-progress/controller-mode-enforcement.md
"""
from __future__ import annotations

import sys
import math
import threading
import time
from typing import Any, Callable, Optional

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Low-level mouse hook
    WH_MOUSE_LL = 14
    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MOUSEWHEEL = 0x020A

    # For mouse_event blocking
    MOUSEEVENTF_MOVE = 0x0001

    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt", wintypes.POINT),
            ("mouseData", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    HOOKPROC = ctypes.WINFUNCTYPE(
        ctypes.c_long,    # return
        ctypes.c_int,     # nCode
        wintypes.WPARAM,  # wParam
        wintypes.LPARAM,  # lParam
    )


# ---------------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------------

_controller_mode_active = False
_controller_mode_lock = threading.Lock()

# Keep-alive pulse thread
_pulse_thread: Optional[threading.Thread] = None
_pulse_gamepad: Any = None  # ViGEm gamepad reference
_pulse_hz: int = 30
_pulse_game_hwnd: int = 0

# Mouse hook thread
_hook_thread: Optional[threading.Thread] = None
_hook_handle: Any = None
_hook_callback_ref: Any = None  # prevent GC of the ctypes callback
_hook_stop_event = threading.Event()

# Stats for debugging
_stats_lock = threading.Lock()
_stats = {
    "pulses_sent": 0,
    "mouse_events_over_game": 0,
    "controller_bursts_sent": 0,
    "mode_started_at": 0.0,
}

# Nimbus window handle (to identify "our" window and let mouse through)
_nimbus_hwnd: int = 0

# Callback for status changes
_status_callback: Optional[Callable[[bool], None]] = None


# ---------------------------------------------------------------------------
# Controller keep-alive pulse
# ---------------------------------------------------------------------------

def _pulse_loop() -> None:
    """
    High-frequency controller keep-alive loop.

    Sends tiny analog stick oscillations through ViGEm that are below any
    game's deadzone (typically 0.1-0.3) but large enough to register as
    "controller input received" in the game's input detection system.

    This keeps the game in controller mode so it voluntarily releases
    the mouse cursor.
    """
    # Elevate thread priority for consistent timing
    try:
        THREAD_PRIORITY_ABOVE_NORMAL = 1
        kernel32.SetThreadPriority(
            kernel32.GetCurrentThread(), THREAD_PRIORITY_ABOVE_NORMAL)
    except Exception:
        pass

    gamepad = _pulse_gamepad
    if gamepad is None:
        print("[mouse_hider] No gamepad reference — pulse thread exiting")
        return

    interval = 1.0 / max(1, _pulse_hz)
    tick = 0
    game_hwnd = _pulse_game_hwnd

    print(f"[mouse_hider] Pulse loop started at {_pulse_hz}Hz "
          f"(interval={interval*1000:.1f}ms)")

    # Initial burst: send several strong controller signals to force switch
    _send_controller_burst(gamepad, count=10, delay=0.016)

    while _controller_mode_active:
        try:
            # Oscillate left stick in a tiny circle below deadzone
            # Amplitude 0.02 is well below any game's deadzone (0.1-0.3)
            # but registers as "controller input changed" in XInputGetState
            angle = (tick % 60) * (2.0 * math.pi / 60.0)
            micro_x = 0.02 * math.cos(angle)
            micro_y = 0.02 * math.sin(angle)

            gamepad.left_joystick_float(micro_x, micro_y)
            gamepad.update()

            with _stats_lock:
                _stats["pulses_sent"] += 1

            tick += 1

            # Also release ClipCursor periodically (every 4th pulse)
            if tick % 4 == 0 and sys.platform == "win32":
                if game_hwnd:
                    _release_clip_with_attach(game_hwnd)
                else:
                    ctypes.windll.user32.ClipCursor(None)

        except Exception as e:
            if _controller_mode_active:
                print(f"[mouse_hider] Pulse error: {e}")

        time.sleep(interval)

    # Clean up: return stick to exact center
    try:
        gamepad.left_joystick_float(0.0, 0.0)
        gamepad.update()
    except Exception:
        pass

    print("[mouse_hider] Pulse loop stopped")


def _send_controller_burst(gamepad: Any, count: int = 10,
                           delay: float = 0.016) -> None:
    """
    Send a rapid burst of controller inputs to force the game into
    controller mode. Uses progressively larger (but still sub-deadzone)
    stick movements to trigger input-mode switching in games that
    require a minimum delta.
    """
    try:
        for i in range(count):
            # Alternate between small positive and negative deflections
            val = 0.05 * (1.0 if i % 2 == 0 else -1.0)
            gamepad.left_joystick_float(val, val)
            gamepad.update()
            time.sleep(delay)

        # Return to center
        gamepad.left_joystick_float(0.0, 0.0)
        gamepad.update()

        with _stats_lock:
            _stats["controller_bursts_sent"] += 1

        print(f"[mouse_hider] Sent {count}-pulse controller burst")
    except Exception as e:
        print(f"[mouse_hider] Burst error: {e}")


def _release_clip_with_attach(game_hwnd: int) -> None:
    """Release ClipCursor with thread-input attachment to game."""
    try:
        our_tid = kernel32.GetCurrentThreadId()
        game_tid = user32.GetWindowThreadProcessId(game_hwnd, None)
        if game_tid and game_tid != our_tid:
            user32.AttachThreadInput(our_tid, game_tid, True)
        ctypes.windll.user32.ClipCursor(None)
        if game_tid and game_tid != our_tid:
            user32.AttachThreadInput(our_tid, game_tid, False)
    except Exception:
        ctypes.windll.user32.ClipCursor(None)


# ---------------------------------------------------------------------------
# Mouse-over-game detection hook (WH_MOUSE_LL)
# ---------------------------------------------------------------------------

def _is_point_in_game_window(x: int, y: int) -> bool:
    """Check if a screen coordinate falls within the game window."""
    game_hwnd = _pulse_game_hwnd
    if not game_hwnd:
        return False
    try:
        rect = wintypes.RECT()
        user32.GetWindowRect(game_hwnd, ctypes.byref(rect))
        return (rect.left <= x <= rect.right and
                rect.top <= y <= rect.bottom)
    except Exception:
        return False


def _is_point_in_nimbus_window(x: int, y: int) -> bool:
    """Check if a screen coordinate falls within the Nimbus window."""
    if not _nimbus_hwnd:
        return False
    try:
        rect = wintypes.RECT()
        user32.GetWindowRect(_nimbus_hwnd, ctypes.byref(rect))
        return (rect.left <= x <= rect.right and
                rect.top <= y <= rect.bottom)
    except Exception:
        return False


def _low_level_mouse_proc(n_code: int, w_param: int, l_param: int) -> int:
    """
    WH_MOUSE_LL callback. Runs for every system-wide mouse event.

    Strategy: We do NOT suppress mouse events (that would freeze the cursor).
    Instead, when we detect mouse movement over the game window, we
    immediately send a burst of controller input to counter the game's
    automatic switch to M/KB mode.

    This is a "fight fire with fire" approach — the game sees mouse input
    but immediately gets overwhelmed by controller input, so it stays in
    (or quickly returns to) controller mode.
    """
    if n_code >= 0 and _controller_mode_active:
        try:
            ms = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            px, py = ms.pt.x, ms.pt.y

            # Only react to mouse movement (not clicks)
            if w_param == WM_MOUSEMOVE:
                if _is_point_in_game_window(px, py):
                    with _stats_lock:
                        _stats["mouse_events_over_game"] += 1

                    # Counter with immediate controller input
                    gamepad = _pulse_gamepad
                    if gamepad:
                        try:
                            # Quick jolt to reassert controller mode
                            gamepad.left_joystick_float(0.03, 0.0)
                            gamepad.update()
                            gamepad.left_joystick_float(0.0, 0.0)
                            gamepad.update()
                        except Exception:
                            pass
        except Exception:
            pass

    # Always pass the event through — never suppress (cursor must move freely)
    return user32.CallNextHookEx(_hook_handle, n_code, w_param, l_param)


def _hook_thread_func() -> None:
    """
    Dedicated thread for the WH_MOUSE_LL hook.
    Requires a Win32 message loop to function.
    """
    global _hook_handle, _hook_callback_ref

    try:
        _hook_callback_ref = HOOKPROC(_low_level_mouse_proc)
        _hook_handle = user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            _hook_callback_ref,
            None,  # hMod — NULL for WH_MOUSE_LL
            0      # dwThreadId — 0 = global
        )

        if not _hook_handle:
            err = ctypes.get_last_error()
            print(f"[mouse_hider] Failed to install mouse hook (error {err})")
            return

        print(f"[mouse_hider] Mouse hook installed (handle={_hook_handle})")

        # Run message loop until stop event
        msg = wintypes.MSG()
        while not _hook_stop_event.is_set():
            # PeekMessage with PM_REMOVE — non-blocking check
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.001)  # Yield CPU when no messages

    except Exception as e:
        print(f"[mouse_hider] Hook thread error: {e}")
    finally:
        if _hook_handle:
            user32.UnhookWindowsHookEx(_hook_handle)
            _hook_handle = None
            _hook_callback_ref = None
            print("[mouse_hider] Mouse hook removed")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_controller_mode(
    gamepad: Any,
    game_hwnd: int = 0,
    nimbus_hwnd: int = 0,
    pulse_hz: int = 30,
    use_mouse_hook: bool = True,
    callback: Optional[Callable[[bool], None]] = None,
) -> bool:
    """
    Start Controller Mode Enforcement.

    This makes the game think only a controller is connected by:
      1. Sending a burst of controller inputs to force controller mode
      2. Running a continuous keep-alive pulse at the specified frequency
      3. Optionally installing a mouse hook that detects mouse-over-game
         and immediately counters with controller input

    The game will voluntarily release the mouse cursor because it thinks
    the player is using a gamepad, not a mouse.

    Args:
        gamepad: ViGEm gamepad object (from vigem_interface.py).
        game_hwnd: HWND of the game window (for targeted release + detection).
        nimbus_hwnd: HWND of the Nimbus window (to allow mouse passthrough).
        pulse_hz: Keep-alive frequency in Hz (10-60 recommended).
        use_mouse_hook: Install WH_MOUSE_LL for mouse-over-game detection.
        callback: Optional status callback(bool).

    Returns:
        True if started successfully.
    """
    global _controller_mode_active, _pulse_thread, _pulse_gamepad
    global _pulse_hz, _pulse_game_hwnd, _nimbus_hwnd
    global _hook_thread, _status_callback

    if sys.platform != "win32":
        print("[mouse_hider] Controller mode only available on Windows")
        return False

    with _controller_mode_lock:
        if _controller_mode_active:
            print("[mouse_hider] Controller mode already active")
            return True

        if gamepad is None:
            print("[mouse_hider] No gamepad provided — cannot start")
            return False

        _pulse_gamepad = gamepad
        _pulse_game_hwnd = game_hwnd
        _nimbus_hwnd = nimbus_hwnd
        _pulse_hz = max(5, min(120, pulse_hz))
        _status_callback = callback
        _controller_mode_active = True

        # Reset stats
        with _stats_lock:
            _stats["pulses_sent"] = 0
            _stats["mouse_events_over_game"] = 0
            _stats["controller_bursts_sent"] = 0
            _stats["mode_started_at"] = time.time()

    # Start keep-alive pulse thread
    _pulse_thread = threading.Thread(
        target=_pulse_loop, daemon=True, name="ControllerPulse")
    _pulse_thread.start()

    # Start mouse hook thread (optional but recommended)
    if use_mouse_hook and game_hwnd:
        _hook_stop_event.clear()
        _hook_thread = threading.Thread(
            target=_hook_thread_func, daemon=True, name="MouseHook")
        _hook_thread.start()

    print(f"[mouse_hider] Controller Mode started "
          f"(game_hwnd={game_hwnd or 'none'}, pulse={_pulse_hz}Hz, "
          f"hook={'on' if use_mouse_hook and game_hwnd else 'off'})")

    if callback:
        callback(True)

    return True


def stop_controller_mode() -> None:
    """
    Stop Controller Mode Enforcement.

    Stops the keep-alive pulse and removes the mouse hook.
    The game will revert to its normal input detection behavior.
    """
    global _controller_mode_active, _pulse_thread, _hook_thread
    global _pulse_gamepad, _status_callback

    with _controller_mode_lock:
        if not _controller_mode_active:
            return
        _controller_mode_active = False

    # Stop mouse hook
    _hook_stop_event.set()
    if _hook_thread and _hook_thread.is_alive():
        _hook_thread.join(timeout=1.0)
    _hook_thread = None

    # Stop pulse thread
    if _pulse_thread and _pulse_thread.is_alive():
        _pulse_thread.join(timeout=1.0)
    _pulse_thread = None

    # Print stats
    with _stats_lock:
        elapsed = time.time() - _stats["mode_started_at"]
        print(f"[mouse_hider] Controller Mode stopped after {elapsed:.1f}s")
        print(f"  Pulses sent: {_stats['pulses_sent']}")
        print(f"  Mouse events over game: {_stats['mouse_events_over_game']}")
        print(f"  Controller bursts: {_stats['controller_bursts_sent']}")

    cb = _status_callback
    _status_callback = None
    _pulse_gamepad = None

    if cb:
        cb(False)


def is_controller_mode_active() -> bool:
    """Check if Controller Mode Enforcement is currently running."""
    return _controller_mode_active


def send_controller_burst(gamepad: Any = None, count: int = 15) -> None:
    """
    Send a one-shot burst of controller signals.

    Useful for forcing a game into controller mode without enabling
    the continuous keep-alive. Call this when the user first launches
    a game or when the game switches back to M/KB mode.

    Args:
        gamepad: ViGEm gamepad (uses the active one if None).
        count: Number of pulses in the burst.
    """
    gp = gamepad or _pulse_gamepad
    if gp is None:
        print("[mouse_hider] No gamepad available for burst")
        return
    _send_controller_burst(gp, count=count)


def get_controller_mode_stats() -> dict:
    """Get statistics about the current/last Controller Mode session."""
    with _stats_lock:
        result = _stats.copy()
    result["active"] = _controller_mode_active
    result["pulse_hz"] = _pulse_hz
    result["game_hwnd"] = _pulse_game_hwnd
    return result
