"""
Windows API utilities for preventing focus loss.

This module provides utilities to keep games focused while interacting
with Project Nimbus. Uses WS_EX_NOACTIVATE to make the Nimbus window
truly non-activating — clicking on Nimbus NEVER steals focus from the
game, so games like Minecraft won't open the pause menu.

The previous approach (v1.4.0) used save/restore of the foreground
window, which caused a brief focus transfer that triggered pause menus.
The new approach uses WS_EX_NOACTIVATE + WM_MOUSEACTIVATE interception
so focus never leaves the game at all.

Implementation based on research/game-focus-solutions.md
"""
from __future__ import annotations

import sys
import struct
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PySide6.QtGui import QWindow

# Only import Windows-specific modules on Windows
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes, POINTER, Structure, byref
    
    user32 = ctypes.windll.user32
    
    # Window style constants
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080  # Don't show in taskbar
    WS_EX_APPWINDOW = 0x00040000   # Force show in taskbar
    
    # WM_MOUSEACTIVATE return values
    WM_MOUSEACTIVATE = 0x0021
    MA_NOACTIVATE = 3
    MA_NOACTIVATEANDEAT = 4
    
    # SetWindowPos flags for SWP calls
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040
    HWND_TOPMOST = -1
    HWND_NOTOPMOST = -2
    
    # Use SetWindowLongPtrW on 64-bit
    try:
        _SetWindowLongPtr = user32.SetWindowLongPtrW
        _GetWindowLongPtr = user32.GetWindowLongPtrW
    except AttributeError:
        _SetWindowLongPtr = user32.SetWindowLongW
        _GetWindowLongPtr = user32.GetWindowLongW
    
    # Function signatures for focus management
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.AttachThreadInput.restype = wintypes.BOOL
    
    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    
    # Module state
    _last_foreground_hwnd: Optional[int] = None
    _game_focus_mode_enabled: bool = False
    _our_hwnd: Optional[int] = None
    _native_filter: Optional[object] = None  # QAbstractNativeEventFilter instance
    _original_ex_style: Optional[int] = None


def get_qt_window_handle(qwindow: QWindow) -> int:
    """Get native HWND from Qt window.
    
    Args:
        qwindow: A Qt QWindow object
        
    Returns:
        The native window handle (HWND on Windows)
    """
    return int(qwindow.winId())


def get_foreground_window() -> int:
    """Get the current foreground window handle."""
    if sys.platform != "win32":
        return 0
    return user32.GetForegroundWindow()


def set_foreground_window(hwnd: int) -> bool:
    """Set a window as the foreground window.
    
    This uses a trick to allow SetForegroundWindow to work:
    attach to the target window's thread temporarily.
    """
    if sys.platform != "win32":
        return False
    
    if hwnd == 0:
        return False
    
    try:
        # Get our thread ID
        our_thread = kernel32.GetCurrentThreadId()
        
        # Get the target window's thread ID
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        
        if target_thread == 0:
            return False
        
        # Attach our thread to the target thread's input queue
        if our_thread != target_thread:
            user32.AttachThreadInput(our_thread, target_thread, True)
        
        # Now we can set the foreground window
        result = user32.SetForegroundWindow(hwnd)
        
        # Detach threads
        if our_thread != target_thread:
            user32.AttachThreadInput(our_thread, target_thread, False)
        
        return bool(result)
    except Exception as e:
        print(f"Error setting foreground window: {e}")
        return False


def _install_native_filter(app=None) -> bool:
    """Install a QAbstractNativeEventFilter that intercepts WM_MOUSEACTIVATE.
    
    When WS_EX_NOACTIVATE is set, Windows still sends WM_MOUSEACTIVATE.
    Qt's default handler may try to activate the window anyway. Our filter
    intercepts this message and returns MA_NOACTIVATE so the window
    never takes focus, but mouse events still reach Qt widgets normally.
    """
    global _native_filter
    
    if sys.platform != "win32":
        return False
    
    if _native_filter is not None:
        return True  # Already installed
    
    try:
        from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray
        from PySide6.QtWidgets import QApplication
        
        class NoActivateFilter(QAbstractNativeEventFilter):
            """Intercept WM_MOUSEACTIVATE to prevent window activation."""
            
            def nativeEventFilter(self, event_type, message):
                if event_type == b"windows_generic_MSG" or event_type == QByteArray(b"windows_generic_MSG"):
                    # On Windows, message is a pointer to a MSG struct
                    # MSG layout (64-bit): HWND(8) + UINT(4) + pad(4) + WPARAM(8) + LPARAM(8) + ...
                    # We need to read the message ID (UINT at offset 8)
                    try:
                        # Cast message to a pointer we can read
                        msg_ptr = int(message)
                        if msg_ptr == 0:
                            return False, 0
                        
                        # Read UINT message at offset 8 (after HWND on 64-bit)
                        ptr_size = ctypes.sizeof(ctypes.c_void_p)  # 8 on 64-bit
                        msg_id_offset = ptr_size  # HWND is first field
                        msg_id = ctypes.c_uint.from_address(msg_ptr + msg_id_offset).value
                        
                        if msg_id == WM_MOUSEACTIVATE:
                            # Return MA_NOACTIVATE — allow mouse event but don't activate
                            return True, MA_NOACTIVATE
                    except Exception:
                        pass
                
                return False, 0
        
        _native_filter = NoActivateFilter()
        
        if app is None:
            app = QApplication.instance()
        if app:
            app.installNativeEventFilter(_native_filter)
            print("[window_utils] Native WM_MOUSEACTIVATE filter installed")
            return True
        else:
            print("[window_utils] No QApplication instance — filter not installed")
            return False
            
    except Exception as e:
        print(f"[window_utils] Failed to install native filter: {e}")
        return False


def _remove_native_filter() -> None:
    """Remove the WM_MOUSEACTIVATE native event filter."""
    global _native_filter
    
    if _native_filter is None:
        return
    
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.removeNativeEventFilter(_native_filter)
    except Exception:
        pass
    
    _native_filter = None
    print("[window_utils] Native filter removed")


def enable_game_focus_mode(our_hwnd: int) -> bool:
    """Enable game focus mode using WS_EX_NOACTIVATE.
    
    This makes the Nimbus window truly non-activating — clicking on it
    will NEVER steal focus from the game. No brief focus transfer, no
    pause menu triggers, no flash.
    
    How it works:
      1. Add WS_EX_NOACTIVATE extended style to our window
      2. Install a native event filter for WM_MOUSEACTIVATE → MA_NOACTIVATE
      3. Mouse events still reach Qt widgets normally via hit-testing
    
    Args:
        our_hwnd: Our window's HWND
        
    Returns:
        True if enabled successfully
    """
    global _game_focus_mode_enabled, _our_hwnd, _original_ex_style
    
    if sys.platform != "win32":
        print("Game focus mode: Only available on Windows")
        return False
    
    _our_hwnd = our_hwnd
    
    try:
        # Save original extended style so we can restore it
        _original_ex_style = _GetWindowLongPtr(our_hwnd, GWL_EXSTYLE)
        
        # Add WS_EX_NOACTIVATE
        new_style = _original_ex_style | WS_EX_NOACTIVATE
        _SetWindowLongPtr(our_hwnd, GWL_EXSTYLE, new_style)
        
        # Install the native event filter
        _install_native_filter()
        
        _game_focus_mode_enabled = True
        
        # Verify
        verify = _GetWindowLongPtr(our_hwnd, GWL_EXSTYLE)
        has_noactivate = bool(verify & WS_EX_NOACTIVATE)
        
        print(f"[window_utils] Game Focus Mode ENABLED (WS_EX_NOACTIVATE={'OK' if has_noactivate else 'FAILED'})")
        print(f"  HWND: {our_hwnd}")
        print(f"  Clicking Nimbus will NOT steal focus from games")
        
        return has_noactivate
        
    except Exception as e:
        print(f"[window_utils] Failed to enable game focus mode: {e}")
        return False


def disable_game_focus_mode() -> bool:
    """Disable game focus mode — restore normal window activation behavior."""
    global _game_focus_mode_enabled, _last_foreground_hwnd, _original_ex_style
    
    if sys.platform != "win32":
        return False
    
    try:
        if _our_hwnd and _original_ex_style is not None:
            # Restore original extended style (removes WS_EX_NOACTIVATE)
            _SetWindowLongPtr(_our_hwnd, GWL_EXSTYLE, _original_ex_style)
            _original_ex_style = None
        
        # Remove the native filter
        _remove_native_filter()
        
    except Exception as e:
        print(f"[window_utils] Error restoring window style: {e}")
    
    _game_focus_mode_enabled = False
    _last_foreground_hwnd = None
    print("[window_utils] Game Focus Mode DISABLED — normal activation restored")
    return True


def is_game_focus_mode_enabled() -> bool:
    """Check if game focus mode is currently enabled."""
    return _game_focus_mode_enabled if sys.platform == "win32" else False


def on_window_activated() -> None:
    """Called when our window is activated (gets focus).
    
    With WS_EX_NOACTIVATE, this should rarely fire. But if it does
    (e.g., Alt+Tab), and game focus mode is enabled, restore focus
    to the saved foreground window as a fallback.
    """
    global _last_foreground_hwnd
    
    if not _game_focus_mode_enabled:
        return
    
    if sys.platform != "win32":
        return
    
    # If we have a saved foreground window, restore focus to it
    if _last_foreground_hwnd and _last_foreground_hwnd != _our_hwnd:
        set_foreground_window(_last_foreground_hwnd)


def save_foreground_window() -> None:
    """Save the current foreground window.
    
    Call this BEFORE our window gets focus (e.g., on mouse press).
    With WS_EX_NOACTIVATE this is mainly a safety net — the window
    shouldn't actually take focus on click.
    """
    global _last_foreground_hwnd
    
    if not _game_focus_mode_enabled:
        return
    
    if sys.platform != "win32":
        return
    
    current = get_foreground_window()
    # Only save if it's not our window
    if current != _our_hwnd and current != 0:
        _last_foreground_hwnd = current


# Legacy function names for compatibility
def make_window_no_activate(hwnd: int) -> bool:
    """Enable game focus mode (WS_EX_NOACTIVATE implementation)."""
    return enable_game_focus_mode(hwnd)


def remove_window_no_activate(hwnd: int) -> bool:
    """Disable game focus mode."""
    return disable_game_focus_mode()


def is_no_activate_enabled(hwnd: int) -> bool:
    """Check if game focus mode is enabled."""
    return is_game_focus_mode_enabled()
