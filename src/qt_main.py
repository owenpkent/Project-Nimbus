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
    QSpacerItem,
    QSizePolicy,
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

        # Force UI scale to 100% at startup to avoid stale zoom effects
        # Do this before building the menu so the correct item is checked.
        self.config.set_scale_factor(1.0)
        self.config.save_config()

        # Window geometry from config
        self._apply_window_geometry_from_config()
        self.setWindowTitle("Project Nimbus - Virtual Controller (Qt Shell)")

        # Menu bar
        self._build_menubar()

        # Initialize VJoy
        self.vjoy = VJoyInterface(self.config)

        # Central UI - Use a grid layout for better control
        central = QWidget(self)
        root = QGridLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.left_stick = JoystickWidget(self.config, which="left", parent=central)
        self.right_stick = JoystickWidget(self.config, which="right", parent=central)

        # No more titled columns - just use joysticks directly

        # Create button panels
        left_buttons_panel = self._create_number_buttons_panel(ids=(1, 2, 3, 4), parent=central)
        right_buttons_panel = self._create_number_buttons_panel(ids=(5, 6, 7, 8), parent=central)

        # Throttle - 15% shorter to avoid rudder overlap
        self.throttle = SliderWidget(self.config, Qt.Vertical, label="Throttle", auto_center=False, parent=central, gentle_return=False)
        self.throttle.setMinimumWidth(self.config.get_scaled_int(54))
        self.throttle.setMaximumWidth(self.config.get_scaled_int(72))
        self.throttle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        # Set maximum height to make it 15% shorter
        max_throttle_height = int(self.config.get_scaled_int(280) * 0.85)  # 85% of joystick size
        self.throttle.setMaximumHeight(max_throttle_height)

        # Grid layout: 
        # Row 0: Left stick, Throttle, Right stick (no labels)
        # Row 1: Left buttons, Rudder + ARM/RTH, Right buttons  
        
        root.addWidget(self.left_stick, 0, 0, Qt.AlignCenter)
        root.addWidget(self.throttle, 0, 1, Qt.AlignCenter)
        root.addWidget(self.right_stick, 0, 2, Qt.AlignCenter)
        
        root.addWidget(left_buttons_panel, 1, 0, Qt.AlignCenter)
        root.addWidget(right_buttons_panel, 1, 2, Qt.AlignCenter)
        
        # Center column: Rudder above ARM/RTH buttons
        center_widget = QWidget(central)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        
        # Rudder
        self.rudder = SliderWidget(self.config, Qt.Horizontal, label="Rudder", auto_center=True, parent=central)
        self.rudder.setMinimumWidth(self.config.get_scaled_int(200))
        self.rudder.setMaximumWidth(self.config.get_scaled_int(300))
        self.rudder.setMinimumHeight(self.config.get_scaled_int(32))
        self.rudder.setMaximumHeight(self.config.get_scaled_int(44))
        center_layout.addWidget(self.rudder, 0, Qt.AlignCenter)
        
        # ARM/RTH buttons
        arm_rth_widget = QWidget(central)
        arm_rth_layout = QHBoxLayout(arm_rth_widget)
        arm_rth_layout.setContentsMargins(0, 0, 0, 0)
        arm_rth_layout.addStretch(1)
        
        self.arm_btn = QPushButton("ARM", central)
        self.rth_btn = QPushButton("RTH", central)
        btn_blue_style = (
            "QPushButton:pressed, QPushButton:checked {"
            "  background-color: rgb(50,100,200);"
            "  border: 1px solid rgb(100,150,255);"
            "}"
        )
        self.arm_btn.setStyleSheet(btn_blue_style)
        self.rth_btn.setStyleSheet(btn_blue_style)
        self.arm_btn.setMinimumWidth(self.config.get_scaled_int(80))
        self.rth_btn.setMinimumWidth(self.config.get_scaled_int(80))
        
        arm_rth_layout.addWidget(self.arm_btn)
        arm_rth_layout.addSpacing(12)
        arm_rth_layout.addWidget(self.rth_btn)
        arm_rth_layout.addStretch(1)
        
        center_layout.addWidget(arm_rth_widget, 0, Qt.AlignCenter)
        
        # Add center widget to middle column
        root.addWidget(center_widget, 1, 1, Qt.AlignCenter)
        
        # Add some spacing for the buttons row
        root.setRowMinimumHeight(1, self.config.get_scaled_int(100))  # Give buttons row more height
        
        # Set row stretch factors - give joysticks much more space
        root.setRowStretch(0, 5)  # Joysticks get much more space
        root.setRowStretch(1, 1)  # All buttons/controls row

        self.setCentralWidget(central)

        # Remove status bar to eliminate "Ready" message and resize grip
        self.setStatusBar(None)

        # Apply initial scaling to all widgets now that they exist
        self._apply_scaled_sizes()

        # Connections
        self.left_stick.valueChanged.connect(self._on_left_stick)
        self.right_stick.valueChanged.connect(self._on_right_stick)
        self.throttle.valueChanged.connect(self._on_throttle)
        self.rudder.valueChanged.connect(self._on_rudder)
        # ARM/RTH back to standard IDs
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

        # Apply new size immediately to the Qt window and widgets (so it feels responsive)
        self._apply_window_geometry_from_config()
        self._apply_scaled_sizes()
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
        # Enforce a strict 16:9 aspect ratio and disable manual resizing.
        # Prefer width from config/scale and derive height to maintain 16:9.
        h_16_9 = max(1, int(round(w * 9 / 16)))
        w_16_9 = max(1, int(round(h * 16 / 9)))

        # If height from config doesn't match 16:9, override it using width as source of truth.
        # This ensures zoom (which sets width) drives the size deterministically.
        h = h_16_9

        # Apply fixed size so users cannot manually resize the window.
        self.setFixedSize(w, h)

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
        # No margins needed - grid layout handles spacing
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
            # Apply blue pressed/checked style to number buttons only
            btn.setStyleSheet(
                "QPushButton:pressed, QPushButton:checked {"
                "  background-color: rgb(50,100,200);"
                "  border: 1px solid rgb(100,150,255);"
                "}"
            )
            grid.addWidget(btn, r, c)

        # Connect press/release now; toggle behavior will be configured in _apply_button_modes()
        for bid in ids:
            btn = self.number_buttons[bid]
            # Disconnect any previous specific callbacks to avoid duplicates
            if hasattr(btn, "_nimbus_press_cb") and btn._nimbus_press_cb is not None:
                try:
                    btn.pressed.disconnect(btn._nimbus_press_cb)
                except Exception:
                    pass
            if hasattr(btn, "_nimbus_release_cb") and btn._nimbus_release_cb is not None:
                try:
                    btn.released.disconnect(btn._nimbus_release_cb)
                except Exception:
                    pass
            if hasattr(btn, "_nimbus_toggle_cb") and btn._nimbus_toggle_cb is not None:
                try:
                    btn.toggled.disconnect(btn._nimbus_toggle_cb)
                except Exception:
                    pass
            # Default to momentary wiring; will adjust in _apply_button_modes
            btn.setCheckable(False)
            press_cb = (lambda b=bid: self._set_button(b, True))
            release_cb = (lambda b=bid: self._set_button(b, False))
            btn._nimbus_press_cb = press_cb
            btn._nimbus_release_cb = release_cb
            btn._nimbus_toggle_cb = None
            btn.pressed.connect(press_cb)
            btn.released.connect(release_cb)

        return panel

    def _apply_button_modes(self) -> None:
        if not hasattr(self, 'number_buttons'):
            return
        for bid, btn in self.number_buttons.items():
            toggle_mode = bool(self.config.get(f"buttons.button_{bid}.toggle_mode", False))
            # Disconnect specific previously stored callbacks to reconfigure cleanly
            if hasattr(btn, "_nimbus_press_cb") and btn._nimbus_press_cb is not None:
                try:
                    btn.pressed.disconnect(btn._nimbus_press_cb)
                except Exception:
                    pass
                btn._nimbus_press_cb = None
            if hasattr(btn, "_nimbus_release_cb") and btn._nimbus_release_cb is not None:
                try:
                    btn.released.disconnect(btn._nimbus_release_cb)
                except Exception:
                    pass
                btn._nimbus_release_cb = None
            if hasattr(btn, "_nimbus_toggle_cb") and btn._nimbus_toggle_cb is not None:
                try:
                    btn.toggled.disconnect(btn._nimbus_toggle_cb)
                except Exception:
                    pass
                btn._nimbus_toggle_cb = None
            if toggle_mode:
                btn.setCheckable(True)
                # Initialize checked state from config? default False
                btn.setChecked(False)
                toggle_cb = (lambda state, b=bid: self._set_button(b, bool(state)))
                btn._nimbus_toggle_cb = toggle_cb
                btn.toggled.connect(toggle_cb)
            else:
                btn.setCheckable(False)
                press_cb = (lambda b=bid: self._set_button(b, True))
                release_cb = (lambda b=bid: self._set_button(b, False))
                btn._nimbus_press_cb = press_cb
                btn._nimbus_release_cb = release_cb
                btn.pressed.connect(press_cb)
                btn.released.connect(release_cb)

    def _apply_scaled_sizes(self) -> None:
        """Reapply scaled minimum sizes to all widgets after a zoom change."""
        try:
            # Sticks
            if hasattr(self, 'left_stick'):
                self.left_stick.apply_scale()
            if hasattr(self, 'right_stick'):
                self.right_stick.apply_scale()
            # Sliders
            if hasattr(self, 'throttle'):
                self.throttle.apply_scale()
                # Keep throttle custom width constraints
                self.throttle.setMinimumWidth(self.config.get_scaled_int(54))
                self.throttle.setMaximumWidth(self.config.get_scaled_int(72))
                # Keep throttle 15% shorter than joysticks
                max_throttle_height = int(self.config.get_scaled_int(280) * 0.85)
                self.throttle.setMaximumHeight(max_throttle_height)
                self.throttle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            if hasattr(self, 'rudder'):
                self.rudder.apply_scale()
                # Fixed sizing for grid layout
                self.rudder.setMinimumWidth(self.config.get_scaled_int(200))
                self.rudder.setMaximumWidth(self.config.get_scaled_int(300))
                self.rudder.setMinimumHeight(self.config.get_scaled_int(32))
                self.rudder.setMaximumHeight(self.config.get_scaled_int(44))
            # Number buttons
            if hasattr(self, 'number_buttons'):
                size = self.config.get_scaled_int(26)  # Slightly smaller
                for btn in self.number_buttons.values():
                    btn.setMinimumSize(size, size)
            # ARM/RTH widths (smaller)
            if hasattr(self, 'arm_btn'):
                self.arm_btn.setMinimumWidth(self.config.get_scaled_int(80))
            if hasattr(self, 'rth_btn'):
                self.rth_btn.setMinimumWidth(self.config.get_scaled_int(80))
        except Exception:
            pass


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
