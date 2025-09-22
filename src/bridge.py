from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer

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
    buttonsVersionChanged = Signal(int)

    def __init__(self, config: ControllerConfig, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._vjoy = VJoyInterface(self._config)
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

    # ----- Buttons version property (to refresh QML toggle states) -----
    def _get_buttons_version(self) -> int:
        return int(self._buttons_version)

    buttonsVersion = Property(int, _get_buttons_version, notify=buttonsVersionChanged)

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
            if self._vjoy.is_connected:
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
                # Apply Rudder Settings dialog curve
                v = self._config.apply_rudder_sensitivity_curve(float(value))
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
            if not self._vjoy.is_connected:
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
