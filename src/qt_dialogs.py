from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QWidget,
    QGridLayout,
    QCheckBox,
    QDialogButtonBox,
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor

from .config import ControllerConfig


class _LabeledSlider(QWidget):
    def __init__(self, title: str, min_val: int, max_val: int, value: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel(f"{title}: {value}%", self)
        self._slider = QSlider(Qt.Horizontal, self)
        self._slider.setRange(min_val, max_val)
        self._slider.setValue(value)
        self._title = title
        self._slider.valueChanged.connect(self._on_changed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)
        lay.addWidget(self._slider)

    def _on_changed(self, v: int) -> None:
        self._label.setText(f"{self._title}: {v}%")

    def value(self) -> int:
        return int(self._slider.value())

    def setValue(self, v: int) -> None:
        self._slider.setValue(int(v))


class _CurvePreview(QWidget):
    """
    Draws a live XY curve preview based on sensitivity, deadzone, and extremity deadzone.
    Matches the behavior of the existing Pygame dialogs.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.sensitivity = 50.0
        self.deadzone = 10.0
        self.extremity = 5.0

    def setParams(self, sensitivity: float, deadzone: float, extremity: float) -> None:
        changed = (
            abs(self.sensitivity - sensitivity) > 1e-6 or
            abs(self.deadzone - deadzone) > 1e-6 or
            abs(self.extremity - extremity) > 1e-6
        )
        self.sensitivity = float(sensitivity)
        self.deadzone = float(deadzone)
        self.extremity = float(extremity)
        if changed:
            self.update()

    def _calc_output(self, input_value: float) -> float:
        # Ported from pygame dialogs
        deadzone = (self.deadzone / 100.0) * 0.25
        extremity_deadzone = self.extremity / 100.0
        sensitivity = self.sensitivity / 100.0

        if abs(input_value) < deadzone:
            return 0.0

        sign = 1.0 if input_value >= 0 else -1.0
        abs_input = abs(input_value)
        available_range = 1.0 - deadzone
        normalized_input = (abs_input - deadzone) / max(1e-6, available_range)

        if abs(sensitivity - 0.5) < 1e-9:
            output = normalized_input
        elif sensitivity < 0.5:
            power = 1.0 + (0.5 - sensitivity) * 6.0
            output = pow(normalized_input, power)
        else:
            power = 1.0 - (sensitivity - 0.5) * 1.8
            output = pow(normalized_input, max(0.1, power))

        if extremity_deadzone > 0:
            max_output = 1.0 - extremity_deadzone
            output *= max_output

        return output * sign

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # Background
        p.fillRect(self.rect(), QColor(30, 30, 30))

        # Graph rect with margins
        margin = 16
        gx = margin
        gy = margin
        gw = max(1, self.width() - margin * 2)
        gh = max(1, self.height() - margin * 2)

        # Border
        p.setPen(QPen(QColor(100, 100, 100), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(gx, gy, gw, gh)

        # Axes
        cx = gx + gw // 2
        cy = gy + gh // 2
        p.setPen(QPen(QColor(150, 150, 150), 2))
        p.drawLine(gx, cy, gx + gw, cy)
        p.drawLine(cx, gy, cx, gy + gh)

        # Grid (optional light)
        p.setPen(QPen(QColor(60, 60, 60), 1))
        for i in range(1, 5):
            # verticals
            x = gx + i * gw // 5
            p.drawLine(x, gy, x, gy + gh)
            # horizontals
            y = gy + i * gh // 5
            p.drawLine(gx, y, gx + gw, y)

        # Curve points
        p.setPen(QPen(QColor(100, 150, 255), 3))

        def to_screen(ix: float, oy: float) -> tuple[int, int]:
            # ix in [-1,1] maps to x across gw
            # oy in [-1,1] maps to y across gh (invert for screen)
            x = cx + int(ix * (gw / 2))
            y = cy - int(oy * (gh / 2))
            return x, y

        # Positive side 0..1
        prev = None
        for i in range(0, 201):
            iv = i / 200.0
            ov = self._calc_output(iv)
            x, y = to_screen(iv, ov)
            if prev is not None:
                p.drawLine(prev[0], prev[1], x, y)
            prev = (x, y)

        # Negative side -1..0
        prev = None
        for i in range(0, 201):
            iv = -i / 200.0
            ov = self._calc_output(iv)
            x, y = to_screen(iv, ov)
            if prev is not None:
                p.drawLine(prev[0], prev[1], x, y)
            prev = (x, y)


class JoystickSettingsQt(QDialog):
    def __init__(self, config: ControllerConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Joystick Settings")
        self.config = config

        self.sensitivity = int(self.config.get("joystick_settings.sensitivity", 50.0))
        self.deadzone = int(self.config.get("joystick_settings.deadzone", 10.0))
        self.extremity = int(self.config.get("joystick_settings.extremity_deadzone", 5.0))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.sens_slider = _LabeledSlider("Sensitivity", 0, 100, self.sensitivity, self)
        self.dead_slider = _LabeledSlider("Deadzone", 0, 100, self.deadzone, self)
        self.ext_slider = _LabeledSlider("Extremity Deadzone", 0, 100, self.extremity, self)
        layout.addWidget(self.sens_slider)
        layout.addWidget(self.dead_slider)
        layout.addWidget(self.ext_slider)

        # Curve preview
        self.preview = _CurvePreview(self)
        self.preview.setParams(self.sensitivity, self.deadzone, self.extremity)
        layout.addWidget(self.preview)

        # Live updates
        def _update_preview(_: int) -> None:
            self.preview.setParams(
                float(self.sens_slider.value()),
                float(self.dead_slider.value()),
                float(self.ext_slider.value()),
            )
        self.sens_slider._slider.valueChanged.connect(_update_preview)
        self.dead_slider._slider.valueChanged.connect(_update_preview)
        self.ext_slider._slider.valueChanged.connect(_update_preview)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults, parent=self)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._reset)
        layout.addWidget(btns)

    def _reset(self) -> None:
        self.sens_slider.setValue(50)
        self.dead_slider.setValue(10)
        self.ext_slider.setValue(5)

    def _accept(self) -> None:
        self.config.set("joystick_settings.sensitivity", float(self.sens_slider.value()))
        self.config.set("joystick_settings.deadzone", float(self.dead_slider.value()))
        self.config.set("joystick_settings.extremity_deadzone", float(self.ext_slider.value()))
        self.config.save_config()
        self.accept()


class RudderSettingsQt(QDialog):
    def __init__(self, config: ControllerConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rudder Settings")
        self.config = config

        self.sensitivity = int(self.config.get("rudder_settings.sensitivity", 50.0))
        self.deadzone = int(self.config.get("rudder_settings.deadzone", 10.0))
        self.extremity = int(self.config.get("rudder_settings.extremity_deadzone", 5.0))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.sens_slider = _LabeledSlider("Sensitivity", 0, 100, self.sensitivity, self)
        self.dead_slider = _LabeledSlider("Deadzone", 0, 100, self.deadzone, self)
        self.ext_slider = _LabeledSlider("Extremity Deadzone", 0, 100, self.extremity, self)
        layout.addWidget(self.sens_slider)
        layout.addWidget(self.dead_slider)
        layout.addWidget(self.ext_slider)

        # Curve preview
        self.preview = _CurvePreview(self)
        self.preview.setParams(self.sensitivity, self.deadzone, self.extremity)
        layout.addWidget(self.preview)

        # Live updates
        def _update_preview(_: int) -> None:
            self.preview.setParams(
                float(self.sens_slider.value()),
                float(self.dead_slider.value()),
                float(self.ext_slider.value()),
            )
        self.sens_slider._slider.valueChanged.connect(_update_preview)
        self.dead_slider._slider.valueChanged.connect(_update_preview)
        self.ext_slider._slider.valueChanged.connect(_update_preview)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults, parent=self)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._reset)
        layout.addWidget(btns)

    def _reset(self) -> None:
        self.sens_slider.setValue(50)
        self.dead_slider.setValue(10)
        self.ext_slider.setValue(5)

    def _accept(self) -> None:
        self.config.set("rudder_settings.sensitivity", float(self.sens_slider.value()))
        self.config.set("rudder_settings.deadzone", float(self.dead_slider.value()))
        self.config.set("rudder_settings.extremity_deadzone", float(self.ext_slider.value()))
        self.config.save_config()
        self.accept()


class ButtonSettingsQt(QDialog):
    def __init__(self, config: ControllerConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Button Settings")
        self.config = config

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        header1 = QLabel("Button")
        header2 = QLabel("Toggle")
        header1.setStyleSheet("font-weight: 600;")
        header2.setStyleSheet("font-weight: 600;")
        grid.addWidget(header1, 0, 0)
        grid.addWidget(header2, 0, 1)

        self.checks: dict[int, QCheckBox] = {}
        button_names = {
            1: "Button 1", 2: "Button 2", 3: "Button 3", 4: "Button 4",
            5: "Button 5", 6: "Button 6", 7: "Button 7", 8: "Button 8",
            9: "ARM", 10: "RTH"
        }
        for i in range(1, 11):
            name_lbl = QLabel(button_names[i])
            chk = QCheckBox()
            chk.setChecked(bool(self.config.get(f"buttons.button_{i}.toggle_mode", False)))
            self.checks[i] = chk
            grid.addWidget(name_lbl, i, 0)
            grid.addWidget(chk, i, 1)

        layout.addLayout(grid)

        btns = QDialogButtonBox(QDialogButtonBox.Close | QDialogButtonBox.Save, parent=self)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self._save)
        layout.addWidget(btns)

    def _save(self) -> None:
        for i, chk in self.checks.items():
            self.config.set(f"buttons.button_{i}.toggle_mode", bool(chk.isChecked()))
        self.config.save_config()
        self.accept()
