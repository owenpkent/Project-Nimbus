from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Slot, Signal, Property

from .config import ControllerConfig
from .vjoy_interface import VJoyInterface
from .qt_dialogs import AxisMappingQt, JoystickSettingsQt, ButtonSettingsQt, RudderSettingsQt


class ControllerBridge(QObject):
    """
    QObject bridge that connects QML UI to Python back end (VJoy + Config).
    Exposed to QML as context property "controller" in qt_qml_app.py
    """

    scaleFactorChanged = Signal(float)
    vjoyConnectionChanged = Signal(bool)
    debugBordersChanged = Signal(bool)

    def __init__(self, config: ControllerConfig, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._vjoy = VJoyInterface(self._config)
        self._scale = float(self._config.get("ui.scale_factor", 1.0))
        self._debug_borders = bool(self._config.get("ui.debug_borders", False))
        # Emit initial status
        self.vjoyConnectionChanged.emit(bool(self._vjoy.is_connected))

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

    # ----- Slots callable from QML -----
    @Slot(str, float)
    def setAxis(self, axis: str, value: float) -> None:  # noqa: N802 (Qt slot naming)
        """
        Set an axis value coming from QML (-1.0 .. 1.0 recommended).
        """
        try:
            self._vjoy.update_axis(axis.lower(), float(value))
        except Exception:
            pass

    @Slot(int, bool)
    def setButton(self, button_id: int, pressed: bool) -> None:  # noqa: N802
        try:
            self._vjoy.set_button(int(button_id), bool(pressed))
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
            if self._vjoy.is_connected:
                ax = str(self._config.get("axis_mapping.left_x", "x"))
                ay = str(self._config.get("axis_mapping.left_y", "y"))
                if ax != "none":
                    self._vjoy.update_axis(ax, px)
                if ay != "none":
                    self._vjoy.update_axis(ay, py)
        except Exception:
            pass

    @Slot(float, float)
    def setRightStick(self, x: float, y: float) -> None:  # noqa: N802
        try:
            px = self._config.apply_sensitivity_curve(float(x), 'right', 'x')
            py = self._config.apply_sensitivity_curve(float(y), 'right', 'y')
            if self._vjoy.is_connected:
                ax = str(self._config.get("axis_mapping.right_x", "rx"))
                ay = str(self._config.get("axis_mapping.right_y", "ry"))
                if ax != "none":
                    self._vjoy.update_axis(ax, px)
                if ay != "none":
                    self._vjoy.update_axis(ay, py)
        except Exception:
            pass

    @Slot(float)
    def setThrottle(self, value: float) -> None:  # noqa: N802
        try:
            axis = str(self._config.get("axis_mapping.throttle", "z"))
            if self._vjoy.is_connected and axis != "none":
                # Expect QML to send 0..1; convert to -1..1
                v = float(value)
                v = max(0.0, min(1.0, v))
                normalized = v * 2.0 - 1.0
                self._vjoy.update_axis(axis, normalized)
        except Exception:
            pass

    @Slot(float)
    def setRudder(self, value: float) -> None:  # noqa: N802
        try:
            axis = str(self._config.get("axis_mapping.rudder", "rz"))
            if self._vjoy.is_connected and axis != "none":
                # Apply same sensitivity approach as joysticks on X
                v = self._config.apply_sensitivity_curve(float(value), 'right', 'x')
                self._vjoy.update_axis(axis, v)
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
    def openButtonSettings(self) -> None:  # noqa: N802
        try:
            dlg = ButtonSettingsQt(self._config, None)
            if dlg.exec():
                # Could emit a signal if QML needs to refresh button modes
                pass
        except Exception:
            pass

    @Slot()
    def openRudderSettings(self) -> None:  # noqa: N802
        try:
            dlg = RudderSettingsQt(self._config, None)
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
    @Slot(result=bool)
    def isVJoyConnected(self) -> bool:  # noqa: N802
        return bool(self._vjoy.is_connected)
