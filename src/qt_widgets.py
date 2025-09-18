from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtWidgets import QWidget

from .config import ControllerConfig


class JoystickWidget(QWidget):
    valueChanged = Signal(float, float)  # x, y in [-1, 1]

    def __init__(self, config: ControllerConfig, which: str = "left", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.which = which
        self._value = QPointF(0.0, 0.0)  # normalized [-1,1]
        self.setMouseTracking(True)
        size = self.config.get_scaled_int(300)
        self.setMinimumSize(size, size)

    # --- Public API ---
    def center(self) -> None:
        self._value = QPointF(0.0, 0.0)
        self.valueChanged.emit(0.0, 0.0)
        self.update()

    # --- Events ---
    def _norm_from_pos(self, pos: QPointF) -> QPointF:
        r = min(self.width(), self.height()) / 2.0
        cx, cy = self.width() / 2.0, self.height() / 2.0
        dx = (pos.x() - cx) / r
        dy = (pos.y() - cy) / r
        # Clamp to unit circle
        mag2 = dx * dx + dy * dy
        if mag2 > 1.0:
            mag = mag2 ** 0.5
            dx /= mag
            dy /= mag
        # Convert to conventional joystick: up is +Y in our app? Existing uses -1..1 with natural mapping; keep y positive up by inverting dy
        return QPointF(dx, -dy)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._value = self._norm_from_pos(event.position())
            self.valueChanged.emit(self._value.x(), self._value.y())
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            self._value = self._norm_from_pos(event.position())
            self.valueChanged.emit(self._value.x(), self._value.y())
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            # Recenters on release (matches existing SPACE behavior; can be adjusted to lock modes later)
            self.center()

    # --- Painting ---
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # Background
        bg = self.config.get("ui.background_color", (20, 20, 20))
        p.fillRect(self.rect(), QColor(*bg))

        # Joystick base circle
        r = min(self.width(), self.height()) / 2.0 - self.config.get_scaled_int(8)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        base_color = QColor(*self.config.get("ui.joystick_bg_color", (80, 20, 20)))
        p.setPen(QPen(QColor(100, 150, 255), 2))
        p.setBrush(QBrush(base_color))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Crosshair
        p.setPen(QPen(QColor(50, 100, 200), 2))
        p.drawLine(int(cx - r), int(cy), int(cx + r), int(cy))
        p.drawLine(int(cx), int(cy - r), int(cx), int(cy + r))

        # Handle
        handle_r = self.config.get_scaled_int(16)
        hx = cx + self._value.x() * r
        hy = cy - self._value.y() * r
        p.setPen(QPen(QColor(100, 150, 255), 2))
        p.setBrush(QBrush(QColor(50, 100, 200)))
        p.drawEllipse(QPointF(hx, hy), handle_r, handle_r)


class SliderWidget(QWidget):
    valueChanged = Signal(float)  # value in [-1, 1]

    def __init__(self, config: ControllerConfig, orientation: Qt.Orientation, label: str = "", auto_center: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.orientation = orientation
        self.label = label
        self.auto_center = auto_center
        self._value = 0.0
        self.setMouseTracking(True)
        if self.orientation == Qt.Horizontal:
            self.setMinimumSize(self.config.get_scaled_int(240), self.config.get_scaled_int(36))
        else:
            self.setMinimumSize(self.config.get_scaled_int(40), self.config.get_scaled_int(260))

    def setValue(self, v: float) -> None:
        v = max(-1.0, min(1.0, v))
        if abs(v - self._value) > 1e-6:
            self._value = v
            self.valueChanged.emit(self._value)
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._update_from_pos(event.position())

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            self._update_from_pos(event.position())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.auto_center:
            self.setValue(0.0)

    def _update_from_pos(self, pos: QPointF) -> None:
        if self.orientation == Qt.Horizontal:
            t = (pos.x() - self.config.get_scaled_int(8)) / max(1, self.width() - self.config.get_scaled_int(16))
            self.setValue(t * 2.0 - 1.0)
        else:
            t = (pos.y() - self.config.get_scaled_int(8)) / max(1, self.height() - self.config.get_scaled_int(16))
            self.setValue(-(t * 2.0 - 1.0))

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        bg = self.config.get("ui.background_color", (20, 20, 20))
        p.fillRect(self.rect(), QColor(*bg))

        track_color = QColor(15, 30, 60)
        accent = QColor(100, 150, 255)
        hover = QColor(50, 100, 200)

        pad = self.config.get_scaled_int(8)
        if self.orientation == Qt.Horizontal:
            track = QRectF(pad, self.height() / 2 - self.config.get_scaled_int(6), self.width() - 2 * pad, self.config.get_scaled_int(12))
            p.fillRect(track, track_color)
            # Center line
            p.fillRect(QRectF(self.width() / 2 - 1, track.top(), 2, track.height()), hover)
            # Handle
            handle_w = self.config.get_scaled_int(18)
            cx = pad + (self._value + 1.0) / 2.0 * (self.width() - 2 * pad)
            handle = QRectF(cx - handle_w / 2, track.top() - self.config.get_scaled_int(6), handle_w, track.height() + self.config.get_scaled_int(12))
        else:
            track = QRectF(self.width() / 2 - self.config.get_scaled_int(6), pad, self.config.get_scaled_int(12), self.height() - 2 * pad)
            p.fillRect(track, track_color)
            # Center line
            p.fillRect(QRectF(track.left(), self.height() / 2 - 1, track.width(), 2), hover)
            # Handle
            handle_h = self.config.get_scaled_int(18)
            cy = pad + (1.0 - (self._value + 1.0) / 2.0) * (self.height() - 2 * pad)
            handle = QRectF(track.left() - self.config.get_scaled_int(6), cy - handle_h / 2, track.width() + self.config.get_scaled_int(12), handle_h)

        p.setPen(QPen(accent, 2))
        p.setBrush(QBrush(hover))
        p.drawRoundedRect(handle, 4, 4)
