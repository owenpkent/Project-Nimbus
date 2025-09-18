from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenuBar,
    QMenu,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PySide6.QtGui import QIcon, QAction, QActionGroup
from PySide6.QtCore import Qt
import sys

from .config import ControllerConfig
from .vjoy_interface import VJoyInterface
from .qt_widgets import JoystickWidget, SliderWidget
from .qt_dialogs import JoystickSettingsQt, ButtonSettingsQt, RudderSettingsQt


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Load configuration
        self.config = ControllerConfig()
        is_valid, error = self.config.validate_config()
        if not is_valid:
            QMessageBox.critical(self, "Configuration Error", error)
            # Fall back to defaults but continue to show window

        # Window geometry from config
        self._apply_window_geometry_from_config()
        self.setWindowTitle("Project Nimbus - Virtual Controller (Qt Shell)")

        # Menu bar
        self._build_menubar()

        # Initialize VJoy
        self.vjoy = VJoyInterface(self.config)

        # Central UI
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # Top row: Left and Right joysticks with 1-4 / 5-8 buttons under each
        sticks_row = QHBoxLayout()
        sticks_row.setSpacing(12)

        self.left_stick = JoystickWidget(self.config, which="left", parent=central)
        self.right_stick = JoystickWidget(self.config, which="right", parent=central)

        # Helper to add title and child
        def titled_column(title: str, child: QWidget, below: QWidget | None = None) -> QWidget:
            c = QWidget(central)
            v = QVBoxLayout(c)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(6)
            lbl = QLabel(title, c)
            lbl.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            v.addWidget(lbl)
            v.addWidget(child)
            if below is not None:
                v.addWidget(below)
            return c

        # Create number buttons 1-8 (2x2 under each stick)
        left_buttons_panel = self._create_number_buttons_panel(ids=(1, 2, 3, 4), parent=central)
        right_buttons_panel = self._create_number_buttons_panel(ids=(5, 6, 7, 8), parent=central)

        sticks_row.addWidget(titled_column("Left Stick", self.left_stick, left_buttons_panel), 1)
        sticks_row.addWidget(titled_column("Right Stick", self.right_stick, right_buttons_panel), 1)
        root.addLayout(sticks_row, 1)

        # Middle: throttle (vertical) centered
        throttle_row = QHBoxLayout()
        throttle_row.setSpacing(12)
        throttle_row.addStretch(1)
        self.throttle = SliderWidget(self.config, Qt.Vertical, label="Throttle", auto_center=False, parent=central)
        throttle_row.addWidget(self.throttle)
        throttle_row.addStretch(1)
        root.addLayout(throttle_row)

        # Bottom: ARM/RTH buttons above rudder slider
        bottom = QVBoxLayout()
        bottom.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.arm_btn = QPushButton("ARM", central)
        self.rth_btn = QPushButton("RTH", central)
        self.arm_btn.setMinimumWidth(self.config.get_scaled_int(100))
        self.rth_btn.setMinimumWidth(self.config.get_scaled_int(100))
        btn_row.addWidget(self.arm_btn)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.rth_btn)
        btn_row.addStretch(1)
        bottom.addLayout(btn_row)

        self.rudder = SliderWidget(self.config, Qt.Horizontal, label="Rudder", auto_center=True, parent=central)
        bottom.addWidget(self.rudder)
        root.addLayout(bottom)

        self.setCentralWidget(central)

        self.statusBar().showMessage("Ready")

        # Connections
        self.left_stick.valueChanged.connect(self._on_left_stick)
        self.right_stick.valueChanged.connect(self._on_right_stick)
        self.throttle.valueChanged.connect(self._on_throttle)
        self.rudder.valueChanged.connect(self._on_rudder)
        self.arm_btn.pressed.connect(lambda: self._set_button(9, True))
        self.arm_btn.released.connect(lambda: self._set_button(9, False))
        self.rth_btn.pressed.connect(lambda: self._set_button(10, True))
        self.rth_btn.released.connect(lambda: self._set_button(10, False))

        # Apply current toggle/momentary modes for buttons 1-8
        self._apply_button_modes()

    # ----- Menu construction -----
    def _build_menubar(self) -> None:
        menubar: QMenuBar = self.menuBar()

        # File menu
        file_menu: QMenu = menubar.addMenu("&File")

        # Configure Axes placeholder (wired later to show existing dialog or new Qt dialog)
        self._action_configure_axes = QAction("Configure Axes", self)
        self._action_configure_axes.setShortcut("C")
        self._action_configure_axes.triggered.connect(self._on_configure_axes)
        file_menu.addAction(self._action_configure_axes)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu: QMenu = menubar.addMenu("&View")
        size_menu: QMenu = view_menu.addMenu("Size")

        # Size options and checkable group
        self._scale_group = QActionGroup(self)
        self._scale_group.setExclusive(True)

        self._scale_options = [
            ("50%", 0.5), ("75%", 0.75), ("90%", 0.9), ("100%", 1.0),
            ("110%", 1.1), ("125%", 1.25), ("150%", 1.5), ("175%", 1.75), ("200%", 2.0),
        ]

        current_scale = float(self.config.get("ui.scale_factor", 1.0))
        for label, factor in self._scale_options:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setData(factor)
            if abs(factor - current_scale) < 1e-6:
                act.setChecked(True)
            act.triggered.connect(self._on_scale_selected)
            self._scale_group.addAction(act)
            size_menu.addAction(act)

        # Settings menus (each opens a dialog)
        js_menu: QMenu = menubar.addMenu("&Joystick Settings")
        js_open = QAction("Open...", self)
        js_open.triggered.connect(self._open_joystick_settings)
        js_menu.addAction(js_open)

        btn_menu: QMenu = menubar.addMenu("&Button Settings")
        btn_open = QAction("Open...", self)
        btn_open.triggered.connect(self._open_button_settings)
        btn_menu.addAction(btn_open)

        rud_menu: QMenu = menubar.addMenu("&Rudder Settings")
        rud_open = QAction("Open...", self)
        rud_open.triggered.connect(self._open_rudder_settings)
        rud_menu.addAction(rud_open)

    # ----- Actions -----
    def _on_configure_axes(self) -> None:
        QMessageBox.information(
            self,
            "Configure Axes",
            "This will open the existing Axis Config dialog once integrated with Qt.",
        )

    def _on_scale_selected(self) -> None:
        action = self.sender()
        if not isinstance(action, QAction):
            return
        factor = float(action.data())

        # Update config and persist
        self.config.set_scale_factor(factor)
        self.config.save_config()

        # Apply new size immediately to the Qt window (so it feels responsive)
        self._apply_window_geometry_from_config()
        self.statusBar().showMessage(f"UI scale set to {int(factor * 100)}%", 2000)

        # Note: Pygame canvas and widgets will be resized when we embed them.

    # ----- Settings dialogs -----
    def _open_joystick_settings(self) -> None:
        dlg = JoystickSettingsQt(self.config, self)
        dlg.exec()

    def _open_button_settings(self) -> None:
        dlg = ButtonSettingsQt(self.config, self)
        if dlg.exec():
            self.statusBar().showMessage("Button settings saved", 2000)
            # Refresh button behaviors after settings change
            self._apply_button_modes()

    def _open_rudder_settings(self) -> None:
        dlg = RudderSettingsQt(self.config, self)
        dlg.exec()

    # ----- Input handlers -----
    def _apply_joystick_curve(self, x: float, y: float, which: str) -> tuple[float, float]:
        px = self.config.apply_sensitivity_curve(x, which, 'x')
        py = self.config.apply_sensitivity_curve(y, which, 'y')
        return px, py

    def _on_left_stick(self, x: float, y: float) -> None:
        x, y = self._apply_joystick_curve(x, y, 'left')
        if self.vjoy.is_connected:
            left_x_axis = self.config.get("axis_mapping.left_x", "x")
            left_y_axis = self.config.get("axis_mapping.left_y", "y")
            if left_x_axis != "none":
                self.vjoy.update_axis(left_x_axis, x)
            if left_y_axis != "none":
                self.vjoy.update_axis(left_y_axis, y)

    def _on_right_stick(self, x: float, y: float) -> None:
        x, y = self._apply_joystick_curve(x, y, 'right')
        if self.vjoy.is_connected:
            right_x_axis = self.config.get("axis_mapping.right_x", "rx")
            right_y_axis = self.config.get("axis_mapping.right_y", "ry")
            if right_x_axis != "none":
                self.vjoy.update_axis(right_x_axis, x)
            if right_y_axis != "none":
                self.vjoy.update_axis(right_y_axis, y)

    def _on_throttle(self, value: float) -> None:
        throttle_axis = self.config.get("axis_mapping.throttle", "z")
        if self.vjoy.is_connected and throttle_axis != "none":
            self.vjoy.update_axis(throttle_axis, value)

    def _on_rudder(self, value: float) -> None:
        # For now, apply same sensitivity approach as joysticks on X (optional to add dedicated curve later)
        processed = self.config.apply_sensitivity_curve(value, 'right', 'x')
        rudder_axis = self.config.get("axis_mapping.rudder", "rz")
        if self.vjoy.is_connected and rudder_axis != "none":
            self.vjoy.update_axis(rudder_axis, processed)

    def _set_button(self, button_id: int, pressed: bool) -> None:
        if self.vjoy.is_connected:
            self.vjoy.set_button(button_id, pressed)

    def _apply_window_geometry_from_config(self) -> None:
        w = int(self.config.get("ui.window_width", 1024))
        h = int(self.config.get("ui.window_height", 850))
        # Use resize so the OS window manager handles scaling appropriately
        self.resize(w, h)

    def closeEvent(self, event) -> None:
        try:
            if hasattr(self, 'vjoy') and self.vjoy:
                self.vjoy.shutdown()
        finally:
            super().closeEvent(event)

    # ----- Buttons 1-8 helpers -----
    def _create_number_buttons_panel(self, ids: tuple[int, int, int, int], parent: QWidget) -> QWidget:
        panel = QWidget(parent)
        grid = QGridLayout(panel)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        # Ensure storage dict exists
        if not hasattr(self, 'number_buttons'):
            self.number_buttons: dict[int, QPushButton] = {}

        size = self.config.get_scaled_int(40)
        for idx, bid in enumerate(ids):
            r = idx // 2
            c = idx % 2
            btn = QPushButton(str(bid), panel)
            btn.setMinimumSize(size, size)
            self.number_buttons[bid] = btn
            grid.addWidget(btn, r, c)

        # Connect press/release now; toggle behavior will be configured in _apply_button_modes()
        for bid in ids:
            btn = self.number_buttons[bid]
            # Disconnect any previous to avoid duplicates
            try:
                btn.pressed.disconnect()
                btn.released.disconnect()
                btn.toggled.disconnect()
            except Exception:
                pass
            # Default to momentary wiring; will adjust in _apply_button_modes
            btn.setCheckable(False)
            btn.pressed.connect(lambda b=bid: self._set_button(b, True))
            btn.released.connect(lambda b=bid: self._set_button(b, False))

        return panel

    def _apply_button_modes(self) -> None:
        if not hasattr(self, 'number_buttons'):
            return
        for bid, btn in self.number_buttons.items():
            toggle_mode = bool(self.config.get(f"buttons.button_{bid}.toggle_mode", False))
            # Disconnect signals to reconfigure cleanly
            try:
                btn.pressed.disconnect()
                btn.released.disconnect()
                btn.toggled.disconnect()
            except Exception:
                pass
            if toggle_mode:
                btn.setCheckable(True)
                # Initialize checked state from config? default False
                btn.setChecked(False)
                btn.toggled.connect(lambda state, b=bid: self._set_button(b, bool(state)))
            else:
                btn.setCheckable(False)
                btn.pressed.connect(lambda b=bid: self._set_button(b, True))
                btn.released.connect(lambda b=bid: self._set_button(b, False))


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
