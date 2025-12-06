"""
Windows API utilities for preventing focus loss.

This module provides utilities to keep games focused while interacting
with Project Nimbus. Uses focus restoration approach instead of 
WS_EX_NOACTIVATE which breaks mouse input handling.

Implementation based on research/game-focus-solutions.md
"""
from __future__ import annotations

import sys
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
    
    # Store the last foreground window before we took focus
    _last_foreground_hwnd: Optional[int] = None
    _game_focus_mode_enabled: bool = False
    _our_hwnd: Optional[int] = None


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


def enable_game_focus_mode(our_hwnd: int) -> bool:
    """Enable game focus mode.
    
    This mode tracks which window was focused before Project Nimbus
    and provides a function to restore focus to it.
    
    Args:
        our_hwnd: Our window's HWND
        
    Returns:
        True if enabled successfully
    """
    global _game_focus_mode_enabled, _our_hwnd
    
    if sys.platform != "win32":
        print("Game focus mode: Only available on Windows")
        return False
    
    _our_hwnd = our_hwnd
    _game_focus_mode_enabled = True
    print(f"Game focus mode ENABLED (our HWND: {our_hwnd})")
    print("  When you click Project Nimbus, focus will be restored to the previous window")
    return True


def disable_game_focus_mode() -> bool:
    """Disable game focus mode."""
    global _game_focus_mode_enabled, _last_foreground_hwnd
    
    _game_focus_mode_enabled = False
    _last_foreground_hwnd = None
    print("Game focus mode DISABLED")
    return True


def is_game_focus_mode_enabled() -> bool:
    """Check if game focus mode is currently enabled."""
    return _game_focus_mode_enabled if sys.platform == "win32" else False


def on_window_activated() -> None:
    """Called when our window is activated (gets focus).
    
    If game focus mode is enabled, this will restore focus to 
    the previous foreground window.
    """
    global _last_foreground_hwnd
    
    if not _game_focus_mode_enabled:
        return
    
    if sys.platform != "win32":
        return
    
    # If we have a saved foreground window, restore focus to it
    if _last_foreground_hwnd and _last_foreground_hwnd != _our_hwnd:
        print(f"Restoring focus to HWND {_last_foreground_hwnd}")
        set_foreground_window(_last_foreground_hwnd)


def save_foreground_window() -> None:
    """Save the current foreground window.
    
    Call this BEFORE our window gets focus (e.g., on mouse press).
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
    """Enable game focus mode (new implementation)."""
    return enable_game_focus_mode(hwnd)


def remove_window_no_activate(hwnd: int) -> bool:
    """Disable game focus mode."""
    return disable_game_focus_mode()


def is_no_activate_enabled(hwnd: int) -> bool:
    """Check if game focus mode is enabled."""
    return is_game_focus_mode_enabled()
