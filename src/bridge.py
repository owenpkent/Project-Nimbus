from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer
from PySide6.QtGui import QCursor, QWindow

from .config import ControllerConfig
from .vjoy_interface import VJoyInterface
from .qt_dialogs import AxisMappingQt, JoystickSettingsQt, ButtonSettingsQt, SliderSettingsQt, AxisSettingsQt

# Try to import ViGEm for Xbox controller emulation (preferred for modern games)
try:
    from .vigem_interface import ViGEmInterface, VIGEM_AVAILABLE
except ImportError:
    VIGEM_AVAILABLE = False
    ViGEmInterface = None

# Import window utilities for game focus mode (Windows only)
try:
    from .window_utils import (
        make_window_no_activate,
        remove_window_no_activate,
        get_qt_window_handle,
        is_no_activate_enabled,
        save_foreground_window,
        on_window_activated,
    )
    WINDOW_UTILS_AVAILABLE = True
except ImportError:
    WINDOW_UTILS_AVAILABLE = False

# Import borderless window management (Windows only)
try:
    from . import borderless as _borderless
    BORDERLESS_AVAILABLE = True
except ImportError:
    BORDERLESS_AVAILABLE = False
    _borderless = None


class ControllerBridge(QObject):
    """
    QObject bridge that connects QML UI to Python back end (VJoy + Config).
    Exposed to QML as context property "controller" in qt_qml_app.py
    """

    scaleFactorChanged = Signal(float)
    vjoyConnectionChanged = Signal(bool)
    debugBordersChanged = Signal(bool)
    buttonsVersionChanged = Signal(int)
    profileChanged = Signal(str)  # Emits new profile ID
    layoutTypeChanged = Signal(str)  # Emits new layout type
    profilesListChanged = Signal()  # Emits when profile list changes (add/delete)
    profileSaved = Signal(bool)  # Emits save result
    noFocusModeChanged = Signal(bool)  # Emits when no-focus mode changes
    cursorReleaseChanged = Signal(bool)  # Emits when cursor release polling starts/stops
    borderlessModeChanged = Signal(int, bool)  # Emits (hwnd, is_borderless)

    def __init__(self, config: ControllerConfig, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._window: Optional[QWindow] = None
        self._no_focus_mode = False
        self._cursor_release_active = False
        self._borderless_game_hwnd: int = 0
        
        # Determine which controller interface to use based on profile layout type
        # ViGEm (Xbox emulation) is preferred for xbox/adaptive profiles as it works with XInput games
        # vJoy is used for flight_sim profiles or as fallback
        self._use_vigem = False
        self._vigem: Optional[ViGEmInterface] = None
        self._vjoy: Optional[VJoyInterface] = None
        
        self._init_controller_interface()
        
        self._scale = float(self._config.get("ui.scale_factor", 1.0))
        self._debug_borders = bool(self._config.get("ui.debug_borders", False))
        self._buttons_version = 0
        # Axis smoothing state: per-axis current and target in [-1,1]
        self._axis_state: dict[str, dict[str, float]] = {}
        # Timer to apply smoothing at vJoy update rate
        self._smooth_timer = QTimer(self)
        try:
            hz = int(self._config.get("vjoy.update_rate", 60))
            hz = max(10, min(240, hz))
            self._smooth_timer.setInterval(max(1, int(1000 / hz)))
        except Exception:
            self._smooth_timer.setInterval(16)
        self._smooth_timer.timeout.connect(self._smoothing_tick)
        self._smooth_timer.start()
        # Emit initial status
        self.vjoyConnectionChanged.emit(self._is_controller_connected())
    
    def _init_controller_interface(self) -> None:
        """Initialize the appropriate controller interface based on profile type."""
        layout_type = self._config.get_layout_type()
        use_vigem_config = self._config.get("controller.prefer_vigem", True)
        
        # Use ViGEm for Xbox/Adaptive/Custom profiles if available (works with XInput games like No Man's Sky)
        if layout_type in ("xbox", "adaptive", "custom") and VIGEM_AVAILABLE and use_vigem_config:
            print(f"Profile '{layout_type}' detected - using ViGEm Xbox controller emulation")
            print("This provides XInput compatibility for games like No Man's Sky")
            if self._vigem is None:
                self._vigem = ViGEmInterface(self._config)
            self._use_vigem = True
            # Also init vJoy as fallback
            if self._vjoy is None:
                self._vjoy = VJoyInterface(self._config)
        else:
            # Use vJoy for flight sim profiles or if ViGEm unavailable
            if layout_type in ("xbox", "adaptive") and not VIGEM_AVAILABLE:
                print(f"Warning: ViGEm not available for {layout_type} profile")
                print("Install with: pip install vgamepad")
                print("Falling back to vJoy (may not work with XInput-only games)")
            if self._vjoy is None:
                self._vjoy = VJoyInterface(self._config)
            self._use_vigem = False
    
    def _is_controller_connected(self) -> bool:
        """Check if the active controller interface is connected."""
        if self._use_vigem and self._vigem:
            return self._vigem.is_connected
        elif self._vjoy:
            return self._vjoy.is_connected
        return False
    
    def _get_active_interface(self):
        """Get the currently active controller interface."""
        if self._use_vigem and self._vigem:
            return self._vigem
        return self._vjoy

    # ----- Scale factor property -----
    def _get_scale(self) -> float:
        return float(self._scale)

    def _set_scale(self, value: float) -> None:
        value = float(value)
        if value <= 0:
            return
        if abs(value - self._scale) < 1e-6:
            return
        self._scale = value
        self._config.set_scale_factor(value)
        self._config.save_config()
        self.scaleFactorChanged.emit(self._scale)

    scaleFactor = Property(float, _get_scale, _set_scale, notify=scaleFactorChanged)

    # ----- Debug borders property -----
    def _get_debug(self) -> bool:
        return bool(self._debug_borders)

    def _set_debug(self, value: bool) -> None:
        value = bool(value)
        if value == self._debug_borders:
            return
        self._debug_borders = value
        self._config.set("ui.debug_borders", self._debug_borders)
        self._config.save_config()
        self.debugBordersChanged.emit(self._debug_borders)

    debugBorders = Property(bool, _get_debug, _set_debug, notify=debugBordersChanged)

    # ----- Buttons version property (to refresh QML toggle states) -----
    def _get_buttons_version(self) -> int:
        return int(self._buttons_version)

    buttonsVersion = Property(int, _get_buttons_version, notify=buttonsVersionChanged)

    # ----- No-focus mode property (prevents stealing focus from games) -----
    def _get_no_focus_mode(self) -> bool:
        return bool(self._no_focus_mode)
    
    def _set_no_focus_mode(self, enabled: bool) -> None:
        if self._no_focus_mode == enabled:
            return
        
        if not WINDOW_UTILS_AVAILABLE:
            print("No-focus mode: window_utils not available")
            return
        
        if self._window is None:
            print("No-focus mode: window not set yet")
            return
        
        hwnd = get_qt_window_handle(self._window)
        
        if enabled:
            success = make_window_no_activate(hwnd)
            if success:
                self._no_focus_mode = True
                self._config.set("ui.no_focus_mode", True)
                self._config.save_config()
                self.noFocusModeChanged.emit(True)
                print("No-focus mode ENABLED - window will not steal focus from games")
        else:
            success = remove_window_no_activate(hwnd)
            if success:
                self._no_focus_mode = False
                self._config.set("ui.no_focus_mode", False)
                self._config.save_config()
                self.noFocusModeChanged.emit(False)
                print("No-focus mode DISABLED - normal window behavior restored")
    
    noFocusMode = Property(bool, _get_no_focus_mode, _set_no_focus_mode, notify=noFocusModeChanged)
    
    @Slot(QWindow)
    def setWindow(self, window: QWindow) -> None:  # noqa: N802
        """Set the window reference for no-focus mode. Called from QML after window is ready."""
        self._window = window
        # Restore saved no-focus mode setting
        if self._config.get("ui.no_focus_mode", False):
            self._set_no_focus_mode(True)
    
    @Slot(result=bool)
    def isNoFocusModeAvailable(self) -> bool:  # noqa: N802
        """Check if no-focus mode is available on this platform."""
        return WINDOW_UTILS_AVAILABLE and sys.platform == "win32"
    
    @Slot()
    def clipCursorToWindow(self) -> None:  # noqa: N802
        """Confine the mouse cursor to the application window bounds (Windows only)."""
        if sys.platform != "win32" or not self._window:
            return
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = int(self._window.winId())
            rect = wintypes.RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            # Convert client coords to screen coords
            pt_tl = wintypes.POINT(rect.left, rect.top)
            pt_br = wintypes.POINT(rect.right, rect.bottom)
            ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt_tl))
            ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt_br))
            clip_rect = wintypes.RECT(pt_tl.x, pt_tl.y, pt_br.x, pt_br.y)
            ctypes.windll.user32.ClipCursor(ctypes.byref(clip_rect))
        except Exception as e:
            print(f"ClipCursor failed: {e}")

    @Slot(int, int, int, int)
    def clipCursorToRect(self, screen_x: int, screen_y: int, width: int, height: int) -> None:  # noqa: N802
        """Confine the mouse cursor to a specific screen rectangle (Windows only).

        Used to lock cursor to the joystick widget area so a wheelchair joystick
        maps 1:1 to the virtual joystick.
        """
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes
            clip_rect = wintypes.RECT(screen_x, screen_y, screen_x + width, screen_y + height)
            ctypes.windll.user32.ClipCursor(ctypes.byref(clip_rect))
        except Exception as e:
            print(f"ClipCursorToRect failed: {e}")

    @Slot(int, int)
    def setCursorPos(self, screen_x: int, screen_y: int) -> None:  # noqa: N802
        """Move the mouse cursor to a specific screen position.

        Uses Qt's QCursor.setPos() which handles DPI scaling correctly,
        unlike Windows SetCursorPos which expects physical pixels.
        """
        try:
            from PySide6.QtCore import QPoint
            QCursor.setPos(QPoint(screen_x, screen_y))
        except Exception as e:
            print(f"setCursorPos failed: {e}")

    @Slot()
    def unclipCursor(self) -> None:  # noqa: N802
        """Release the mouse cursor confinement."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            ctypes.windll.user32.ClipCursor(None)
        except Exception as e:
            print(f"UnclipCursor failed: {e}")

    @Slot()
    def onMousePressed(self) -> None:  # noqa: N802
        """Called from QML when mouse is pressed on any interactive element.
        
        In game focus mode, this saves the current foreground window
        so we can restore focus to it later.
        """
        if WINDOW_UTILS_AVAILABLE and self._no_focus_mode:
            save_foreground_window()
    
    @Slot()
    def onMouseReleased(self) -> None:  # noqa: N802
        """Called from QML when mouse is released.
        
        In game focus mode, this restores focus to the previous foreground window.
        """
        if WINDOW_UTILS_AVAILABLE and self._no_focus_mode:
            on_window_activated()

    # ----- Slots callable from QML -----
    @Slot(str, float)
    def setAxis(self, axis: str, value: float) -> None:  # noqa: N802 (Qt slot naming)
        """
        Set an axis value coming from QML (-1.0 .. 1.0 recommended).
        """
        try:
            iface = self._get_active_interface()
            if iface:
                iface.update_axis(axis.lower(), float(value))
        except Exception:
            pass

    @Slot(int, bool)
    def setButton(self, button_id: int, pressed: bool) -> None:  # noqa: N802
        try:
            iface = self._get_active_interface()
            if iface:
                iface.set_button(int(button_id), bool(pressed))
        except Exception:
            pass

    @Slot(float)
    def setScaleFactor(self, value: float) -> None:  # noqa: N802
        self._set_scale(value)

    @Slot(int, result=int)
    def scaled(self, base: int) -> int:  # noqa: N802
        """Return a config-scaled integer for a given base pixel value."""
        try:
            return int(self._config.get_scaled_int(int(base)))
        except Exception:
            return int(base)

    # High-level control slots that apply curves and mapping, mirroring widget UI behavior
    @Slot(float, float)
    def setLeftStick(self, x: float, y: float) -> None:  # noqa: N802
        try:
            px = self._config.apply_sensitivity_curve(float(x), 'left', 'x')
            py = self._config.apply_sensitivity_curve(float(y), 'left', 'y')
            if self._is_controller_connected():
                # For ViGEm, use direct stick control
                if self._use_vigem and self._vigem:
                    self._vigem.set_left_stick(px, py)
                else:
                    ax = str(self._config.get("axis_mapping.left_x", "x"))
                    ay = str(self._config.get("axis_mapping.left_y", "y"))
                    if ax != "none":
                        self._set_axis_target(ax, px)
                    if ay != "none":
                        self._set_axis_target(ay, py)
        except Exception:
            pass

    @Slot(float, float)
    def setRightStick(self, x: float, y: float) -> None:  # noqa: N802
        try:
            px = self._config.apply_sensitivity_curve(float(x), 'right', 'x')
            py = self._config.apply_sensitivity_curve(float(y), 'right', 'y')
            if self._is_controller_connected():
                # For ViGEm, use direct stick control
                if self._use_vigem and self._vigem:
                    self._vigem.set_right_stick(px, py)
                else:
                    ax = str(self._config.get("axis_mapping.right_x", "rx"))
                    ay = str(self._config.get("axis_mapping.right_y", "ry"))
                    if ax != "none":
                        self._set_axis_target(ax, px)
                    if ay != "none":
                        self._set_axis_target(ay, py)
        except Exception:
            pass

    @Slot(float)
    def setThrottle(self, value: float) -> None:  # noqa: N802
        try:
            if self._is_controller_connected():
                v = float(value)
                v = max(0.0, min(1.0, v))
                # For ViGEm, use left trigger
                if self._use_vigem and self._vigem:
                    self._vigem.set_left_trigger(v)
                else:
                    axis = str(self._config.get("axis_mapping.throttle", "z"))
                    if axis != "none":
                        normalized = v * 2.0 - 1.0
                        self._vjoy.update_axis(axis, normalized)
        except Exception:
            pass

    @Slot(float)
    def setRudder(self, value: float) -> None:  # noqa: N802
        try:
            if self._is_controller_connected():
                # Apply Rudder Settings dialog curve
                v = self._config.apply_rudder_sensitivity_curve(float(value))
                # For ViGEm, use right trigger (convert from -1..1 to 0..1)
                if self._use_vigem and self._vigem:
                    trigger_val = (v + 1.0) / 2.0
                    self._vigem.set_right_trigger(trigger_val)
                else:
                    axis = str(self._config.get("axis_mapping.rudder", "rz"))
                    if axis != "none":
                        self._set_axis_target(axis, v)
        except Exception:
            pass

    # ----- Internal smoothing helpers -----
    def _set_axis_target(self, axis: str, target: float) -> None:
        try:
            a = axis.lower()
            t = max(-1.0, min(1.0, float(target)))
            st = self._axis_state.get(a)
            if st is None:
                st = {"current": 0.0, "target": t}
                self._axis_state[a] = st
            else:
                st["target"] = t
            # If smoothing disabled, snap immediately
            if not bool(self._config.get("safety.enable_smoothing", True)):
                st["current"] = t
                if self._vjoy.is_connected:
                    self._vjoy.update_axis(a, t)
        except Exception:
            pass

    def _smoothing_tick(self) -> None:
        try:
            # Skip smoothing for ViGEm (it handles its own updates)
            if self._use_vigem:
                return
            if not self._vjoy or not self._vjoy.is_connected:
                return
            alpha = float(self._config.get("safety.smoothing_factor", 0.1))
            alpha = max(0.01, min(1.0, alpha))
            enabled = bool(self._config.get("safety.enable_smoothing", True))
            for a, st in list(self._axis_state.items()):
                cur = float(st.get("current", 0.0))
                tgt = float(st.get("target", 0.0))
                if enabled:
                    nxt = cur + (tgt - cur) * alpha
                    # snap if close to avoid lingering
                    if abs(nxt - tgt) < 1e-3:
                        nxt = tgt
                else:
                    nxt = tgt
                st["current"] = nxt
                self._vjoy.update_axis(a, nxt)
        except Exception:
            pass

    # ----- Button mode helpers for QML -----
    @Slot(int, result=bool)
    def isButtonToggle(self, button_id: int) -> bool:  # noqa: N802
        try:
            return bool(self._config.get(f"buttons.button_{int(button_id)}.toggle_mode", False))
        except Exception:
            return False

    # Settings openers (can be wired later or remain placeholders)
    @Slot()
    def openJoystickSettings(self) -> None:  # noqa: N802
        try:
            dlg = JoystickSettingsQt(self._config, None)
            dlg.exec()
        except Exception:
            pass

    @Slot()
    def openAxisSettings(self) -> None:  # noqa: N802
        """Open unified per-axis sensitivity settings dialog."""
        try:
            dlg = AxisSettingsQt(self._config, None)
            dlg.exec()
        except Exception:
            pass

    @Slot()
    def openButtonSettings(self) -> None:  # noqa: N802
        try:
            dlg = ButtonSettingsQt(self._config, None)
            if dlg.exec():
                # Bump version so QML re-evaluates bindings that depend on button modes
                self._buttons_version += 1
                self.buttonsVersionChanged.emit(self._buttons_version)
        except Exception:
            pass

    @Slot()
    def openSliderSettings(self) -> None:  # noqa: N802
        """Open slider/trigger sensitivity settings dialog."""
        try:
            dlg = SliderSettingsQt(self._config, None)
            dlg.exec()
        except Exception:
            pass

    @Slot()
    def openAxisMapping(self) -> None:  # noqa: N802
        try:
            dlg = AxisMappingQt(self._config, None)
            dlg.exec()
        except Exception:
            pass

    # ----- Expose some status -----
    @Slot(result=str)
    def getVersion(self) -> str:  # noqa: N802
        """Get the application version string."""
        try:
            import src as _src
            return _src.__version__
        except Exception:
            pass
        try:
            import importlib
            _m = importlib.import_module("src")
            return _m.__version__
        except Exception:
            return "1.4.0"

    @Slot(result=bool)
    def isVJoyConnected(self) -> bool:  # noqa: N802
        return self._is_controller_connected()
    
    @Slot(result=str)
    def getControllerType(self) -> str:  # noqa: N802
        """Get the type of controller interface being used."""
        if self._use_vigem:
            return "Xbox 360 (ViGEm)"
        return "vJoy (DirectInput)"

    # ----- Profile system -----
    @Slot(result=str)
    def getCurrentProfile(self) -> str:  # noqa: N802
        """Get the current profile ID."""
        return self._config.get_current_profile()

    @Slot(result=str)
    def getLayoutType(self) -> str:  # noqa: N802
        """Get the layout type of the current profile."""
        return self._config.get_layout_type()

    @Slot(result="QVariantList")
    def getAvailableProfiles(self) -> list:  # noqa: N802
        """Get list of available profiles for QML menu."""
        return self._config.get_available_profiles()

    @Slot(str, result=bool)
    def switchProfile(self, profile_id: str) -> bool:  # noqa: N802
        """Switch to a different profile."""
        success = self._config.switch_profile(profile_id)
        if success:
            self.profileChanged.emit(profile_id)
            self.layoutTypeChanged.emit(self._config.get_layout_type())
            # Bump buttons version so QML refreshes button labels/modes
            self._buttons_version += 1
            self.buttonsVersionChanged.emit(self._buttons_version)
        return success

    @Slot(int, result=str)
    def getButtonLabel(self, button_id: int) -> str:  # noqa: N802
        """Get the label for a button based on current profile."""
        return self._config.get_button_label(button_id)

    @Slot(result=bool)
    def saveCurrentProfile(self) -> bool:  # noqa: N802
        """Save current settings to the active profile."""
        success = self._config.save_current_profile()
        self.profileSaved.emit(success)
        return success

    @Slot(str, result=bool)
    def resetProfile(self, profile_id: str) -> bool:  # noqa: N802
        """Reset a profile to its default settings."""
        success = self._config.reset_profile(profile_id)
        if success and profile_id == self._config.get_current_profile():
            # Refresh UI if we reset the current profile
            self._buttons_version += 1
            self.buttonsVersionChanged.emit(self._buttons_version)
        return success

    @Slot(str, str, result=str)
    def duplicateProfile(self, source_id: str, new_name: str) -> str:  # noqa: N802
        """Duplicate a profile with a new name. Returns new profile ID or empty string."""
        new_id = self._config.duplicate_profile(source_id, new_name)
        if new_id:
            self.profilesListChanged.emit()
        return new_id if new_id else ""

    @Slot(str, str, result=str)
    def createProfileAs(self, name: str, description: str) -> str:  # noqa: N802
        """Create a new profile from current settings with given name and description."""
        new_id = self._config.create_profile_as(name, description)
        if new_id:
            self.profilesListChanged.emit()
        return new_id if new_id else ""

    @Slot(str, result=bool)
    def deleteProfile(self, profile_id: str) -> bool:  # noqa: N802
        """Delete a user-created profile."""
        success = self._config.delete_profile(profile_id)
        if success:
            self.profilesListChanged.emit()
        return success

    @Slot(str, result=bool)
    def isBuiltinProfile(self, profile_id: str) -> bool:  # noqa: N802
        """Check if a profile is a built-in profile."""
        return self._config.is_builtin_profile(profile_id)

    @Slot(result=str)
    def getUserProfilesPath(self) -> str:  # noqa: N802
        """Get the path to the user profiles directory."""
        return self._config.get_user_profiles_path()

    # ----- Custom layout system -----
    @Slot(result=str)
    def getCustomLayout(self) -> str:  # noqa: N802
        """Get custom layout widgets as JSON string for QML."""
        try:
            profile_data = self._config.get_current_profile_data()
            if profile_data and "custom_layout" in profile_data:
                import json
                widgets = profile_data["custom_layout"].get("widgets", [])
                return json.dumps(widgets)
        except Exception:
            pass
        return "[]"

    @Slot(result=int)
    def getCustomLayoutGridSnap(self) -> int:  # noqa: N802
        """Get grid snap size for custom layout."""
        try:
            profile_data = self._config.get_current_profile_data()
            if profile_data and "custom_layout" in profile_data:
                return int(profile_data["custom_layout"].get("grid_snap", 10))
        except Exception:
            pass
        return 10

    @Slot(result=bool)
    def getCustomLayoutShowGrid(self) -> bool:  # noqa: N802
        """Get whether grid is shown for custom layout."""
        try:
            profile_data = self._config.get_current_profile_data()
            if profile_data and "custom_layout" in profile_data:
                return bool(profile_data["custom_layout"].get("show_grid", True))
        except Exception:
            pass
        return True

    @Slot(str, int, bool)
    def saveCustomLayout(self, widgets_json: str, grid_snap: int, show_grid: bool) -> None:  # noqa: N802
        """Save custom layout widgets from QML (silent — no profileSaved signal)."""
        try:
            import json
            widgets = json.loads(widgets_json)
            self._config.save_custom_layout(widgets, int(grid_snap), bool(show_grid))
        except Exception as e:
            print(f"Error saving custom layout: {e}")

    @Slot(str, str, int, bool)
    def saveCustomLayoutAs(self, name: str, widgets_json: str, grid_snap: int, show_grid: bool) -> None:  # noqa: N802
        """Save custom layout as a new profile with a custom name."""
        try:
            import json
            import copy
            widgets = json.loads(widgets_json)
            # Duplicate current profile with new name
            profile_data = copy.deepcopy(self._config.get_current_profile_data() or {})
            profile_id = name.lower().replace(" ", "_").replace("-", "_")
            profile_data["name"] = name
            profile_data["description"] = f"Custom layout: {name}"
            profile_data["layout_type"] = "custom"
            if "custom_layout" not in profile_data:
                profile_data["custom_layout"] = {}
            profile_data["custom_layout"]["widgets"] = widgets
            profile_data["custom_layout"]["grid_snap"] = int(grid_snap)
            profile_data["custom_layout"]["show_grid"] = bool(show_grid)
            # Save as new profile
            self._config.save_profile_as(profile_id, profile_data)
            print(f"Saved custom layout as: {name} (id: {profile_id})")
            self.profileSaved.emit(True)
        except Exception as e:
            print(f"Error saving custom layout as '{name}': {e}")
            self.profileSaved.emit(False)

    @Slot()
    def openProfilesFolder(self) -> None:  # noqa: N802
        """Open the user profiles folder in the system file explorer."""
        import subprocess
        import sys
        path = self._config.get_user_profiles_path()
        if sys.platform == "win32":
            subprocess.Popen(["explorer", path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    # ----- Borderless gaming integration -----
    @Slot(result=bool)
    def isBorderlessAvailable(self) -> bool:  # noqa: N802
        """Check if borderless gaming features are available."""
        return BORDERLESS_AVAILABLE and sys.platform == "win32"

    @Slot(result=str)
    def getRunningWindows(self) -> str:  # noqa: N802
        """Get list of running windows as JSON for QML game picker.
        
        Returns JSON array of objects with: hwnd, title, className, pid,
        x, y, width, height, isBorderless.
        """
        import json
        if not BORDERLESS_AVAILABLE:
            return "[]"
        try:
            windows = _borderless.enumerate_windows()
            result = []
            for w in windows:
                result.append({
                    "hwnd": w.hwnd,
                    "title": w.title,
                    "className": w.class_name,
                    "pid": w.pid,
                    "x": w.x,
                    "y": w.y,
                    "width": w.width,
                    "height": w.height,
                    "isBorderless": w.is_borderless,
                })
            return json.dumps(result)
        except Exception as e:
            print(f"getRunningWindows failed: {e}")
            return "[]"

    @Slot(result=str)
    def getGameCompatibility(self) -> str:  # noqa: N802
        """Get game compatibility database as JSON for QML.
        
        Returns JSON array of objects with: name, status, inputMethod,
        notes, needsBorderless, needsCursorRelease, recommendedIntervalMs.
        """
        import json
        if not BORDERLESS_AVAILABLE:
            return "[]"
        try:
            games = _borderless.get_compatible_games()
            result = []
            for g in games:
                result.append({
                    "name": g.name,
                    "status": g.status,
                    "inputMethod": g.input_method,
                    "notes": g.notes,
                    "windowTitleHint": g.window_title_hint,
                    "needsBorderless": g.needs_borderless,
                    "needsCursorRelease": g.needs_cursor_release,
                    "recommendedIntervalMs": g.recommended_interval_ms,
                })
            return json.dumps(result)
        except Exception as e:
            print(f"getGameCompatibility failed: {e}")
            return "[]"

    @Slot(result=str)
    def autoDetectGame(self) -> str:  # noqa: N802
        """Auto-detect a running game from the compatibility database.
        
        Returns JSON object with window info and game compat data, or empty string.
        """
        import json
        if not BORDERLESS_AVAILABLE:
            return ""
        try:
            result = _borderless.auto_detect_game()
            if result:
                w, g = result
                return json.dumps({
                    "window": {
                        "hwnd": w.hwnd,
                        "title": w.title,
                        "className": w.class_name,
                    },
                    "game": {
                        "name": g.name,
                        "status": g.status,
                        "inputMethod": g.input_method,
                        "notes": g.notes,
                        "needsBorderless": g.needs_borderless,
                        "needsCursorRelease": g.needs_cursor_release,
                        "recommendedIntervalMs": g.recommended_interval_ms,
                    },
                })
        except Exception as e:
            print(f"autoDetectGame failed: {e}")
        return ""

    @Slot(int, result=bool)
    def makeGameBorderless(self, hwnd: int) -> bool:  # noqa: N802
        """Make a game window borderless fullscreen.
        
        Args:
            hwnd: Window handle of the game.
        
        Returns:
            True on success.
        """
        if not BORDERLESS_AVAILABLE:
            return False
        try:
            success = _borderless.make_borderless(hwnd)
            if success:
                self._borderless_game_hwnd = hwnd
                self.borderlessModeChanged.emit(hwnd, True)
            return success
        except Exception as e:
            print(f"makeGameBorderless failed: {e}")
            return False

    @Slot(int, result=bool)
    def restoreGameWindow(self, hwnd: int) -> bool:  # noqa: N802
        """Restore a game window's original decorations.
        
        Args:
            hwnd: Window handle previously passed to makeGameBorderless().
        
        Returns:
            True on success.
        """
        if not BORDERLESS_AVAILABLE:
            return False
        try:
            success = _borderless.restore_window(hwnd)
            if success:
                if self._borderless_game_hwnd == hwnd:
                    self._borderless_game_hwnd = 0
                self.borderlessModeChanged.emit(hwnd, False)
            return success
        except Exception as e:
            print(f"restoreGameWindow failed: {e}")
            return False

    @Slot(int, result=bool)
    def isGameBorderless(self, hwnd: int) -> bool:  # noqa: N802
        """Check if a game window has been made borderless by us."""
        if not BORDERLESS_AVAILABLE:
            return False
        return _borderless.is_borderless(hwnd)

    @Slot(int)
    def startCursorRelease(self, interval_ms: int = 50) -> None:  # noqa: N802
        """Start continuous ClipCursor release polling.
        
        This fights games that re-apply ClipCursor every frame.
        
        Args:
            interval_ms: Release interval in milliseconds (default 50).
        """
        if not BORDERLESS_AVAILABLE:
            return
        try:
            def _on_change(active: bool):
                self._cursor_release_active = active
                self.cursorReleaseChanged.emit(active)
            
            _borderless.start_cursor_release(interval_ms, _on_change)
        except Exception as e:
            print(f"startCursorRelease failed: {e}")

    @Slot()
    def stopCursorRelease(self) -> None:  # noqa: N802
        """Stop the continuous ClipCursor release."""
        if not BORDERLESS_AVAILABLE:
            return
        try:
            _borderless.stop_cursor_release()
            self._cursor_release_active = False
            self.cursorReleaseChanged.emit(False)
        except Exception as e:
            print(f"stopCursorRelease failed: {e}")

    @Slot(result=bool)
    def isCursorReleaseActive(self) -> bool:  # noqa: N802
        """Check if cursor release polling is currently active."""
        if not BORDERLESS_AVAILABLE:
            return False
        return _borderless.is_cursor_release_active()

    @Slot(result=str)
    def getClipCursorRect(self) -> str:  # noqa: N802
        """Get the current ClipCursor rectangle as JSON.
        
        Returns JSON string like '{"left":0,"top":0,"right":1920,"bottom":1080}'
        or empty string if no clip is active.
        """
        import json
        if not BORDERLESS_AVAILABLE:
            return ""
        try:
            rect = _borderless.get_clip_cursor_rect()
            if rect:
                return json.dumps({
                    "left": rect[0], "top": rect[1],
                    "right": rect[2], "bottom": rect[3],
                })
        except Exception as e:
            print(f"getClipCursorRect failed: {e}")
        return ""

    @Slot(int, int, result=bool)
    def applyBorderlessAndRelease(self, hwnd: int, interval_ms: int = 50) -> bool:  # noqa: N802
        """One-call: make game borderless AND start cursor release.
        
        This is the recommended approach for most games.
        
        Args:
            hwnd: Game window handle.
            interval_ms: Cursor release interval.
        
        Returns:
            True if borderless was applied successfully.
        """
        if not BORDERLESS_AVAILABLE:
            return False
        try:
            success = _borderless.make_borderless(hwnd)
            if success:
                self._borderless_game_hwnd = hwnd
                self.borderlessModeChanged.emit(hwnd, True)
                
                def _on_change(active: bool):
                    self._cursor_release_active = active
                    self.cursorReleaseChanged.emit(active)
                
                _borderless.start_cursor_release(interval_ms, _on_change)
            return success
        except Exception as e:
            print(f"applyBorderlessAndRelease failed: {e}")
            return False

    @Slot(int)
    def restoreAndStopRelease(self, hwnd: int) -> None:  # noqa: N802
        """Restore game window and stop cursor release."""
        if not BORDERLESS_AVAILABLE:
            return
        try:
            _borderless.stop_cursor_release()
            self._cursor_release_active = False
            self.cursorReleaseChanged.emit(False)
            
            success = _borderless.restore_window(hwnd)
            if success:
                if self._borderless_game_hwnd == hwnd:
                    self._borderless_game_hwnd = 0
                self.borderlessModeChanged.emit(hwnd, False)
        except Exception as e:
            print(f"restoreAndStopRelease failed: {e}")
