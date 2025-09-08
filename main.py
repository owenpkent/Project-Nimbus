"""
Main application for the virtual controller interface.
Provides a dual joystick layout with lock/unlock and reset functionality.
"""

import pygame
import sys
import time
from typing import Optional, List, Tuple
from config import ControllerConfig
from virtual_joystick import VirtualJoystick
from vjoy_interface import VJoyInterface
from axis_config_dialog import AxisConfigDialog
from joystick_settings_dialog import JoystickSettingsDialog


class Button:
    """Simple button class for UI controls."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font: pygame.font.Font, config: ControllerConfig, button_id: int = 0):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.config = config
        self.button_id = button_id
        self.is_pressed = False
        self.is_hovered = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the button."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed:
                self.is_pressed = False
                if self.rect.collidepoint(event.pos):
                    return True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the button."""
        # Choose color based on state
        if self.is_pressed:
            color = (25, 50, 100)
        elif self.is_hovered:
            color = (25, 50, 100)
        else:
            color = (15, 30, 60)
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (100, 150, 255), self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.config.get("ui.text_color", (255, 255, 255)))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class Slider:
    """Slider control for throttle and rudder."""
    
    def __init__(self, x: int, y: int, width: int, height: int, orientation: str, 
                 config: ControllerConfig, label: str = "", auto_center: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.orientation = orientation  # "horizontal" or "vertical"
        self.config = config
        self.label = label
        self.value = 0.0  # -1.0 to 1.0
        self.is_dragging = False
        self.is_hovered = False
        self.auto_center = auto_center
        
        # Drag reference point tracking
        self.drag_start_pos = 0
        self.initial_value = 0.0
        
        # Calculate slider handle dimensions
        if orientation == "horizontal":
            self.handle_width = 20
            self.handle_height = height
        else:  # vertical
            self.handle_width = width
            self.handle_height = 20
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the slider."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                # Store drag start position and current value
                if self.orientation == "horizontal":
                    self.drag_start_pos = event.pos[0]
                else:  # vertical
                    self.drag_start_pos = event.pos[1]
                self.initial_value = self.value
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_dragging:
                self.is_dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_dragging:
                self._update_value_from_drag(event.pos)
                return True
        
        return False
    
    def _update_value_from_drag(self, mouse_pos: Tuple[int, int]) -> None:
        """Update slider value based on drag movement from initial position."""
        if self.orientation == "horizontal":
            # Horizontal slider (rudder) - calculate relative movement
            delta = mouse_pos[0] - self.drag_start_pos
            # Convert delta to value change (-1.0 to 1.0 range)
            value_change = (delta / self.rect.width) * 2.0
            new_value = self.initial_value + value_change
        else:
            # Vertical slider (throttle) - calculate relative movement
            delta = mouse_pos[1] - self.drag_start_pos
            # Convert delta to value change (inverted for natural up/down)
            value_change = -(delta / self.rect.height) * 2.0
            new_value = self.initial_value + value_change
        
        # Clamp to valid range
        self.value = max(-1.0, min(1.0, new_value))
    
    def _update_value_from_mouse(self, mouse_pos: Tuple[int, int]) -> None:
        """Update slider value based on mouse position."""
        # This method is deprecated - using drag-based movement instead
        pass
    
    def get_handle_rect(self) -> pygame.Rect:
        """Get the rectangle for the slider handle."""
        if self.orientation == "horizontal":
            # Handle position based on value (-1 to 1 mapped to slider width)
            handle_x = self.rect.x + int((self.value + 1.0) / 2.0 * (self.rect.width - self.handle_width))
            return pygame.Rect(handle_x, self.rect.y, self.handle_width, self.handle_height)
        else:
            # Handle position based on value (1 to -1 mapped to slider height)
            handle_y = self.rect.y + int((1.0 - self.value) / 2.0 * (self.rect.height - self.handle_height))
            return pygame.Rect(self.rect.x, handle_y, self.handle_width, self.handle_height)
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the slider."""
        # Draw slider track
        track_color = (15, 30, 60)
        pygame.draw.rect(surface, track_color, self.rect)
        
        # Draw center line
        center_color = (50, 100, 200)
        if self.orientation == "vertical":
            center_x = self.rect.x + self.rect.width // 2
            pygame.draw.line(surface, center_color, 
                           (center_x, self.rect.y), 
                           (center_x, self.rect.y + self.rect.height), 2)
        else:
            center_y = self.rect.y + self.rect.height // 2
            pygame.draw.line(surface, center_color,
                           (self.rect.x, center_y),
                           (self.rect.x + self.rect.width, center_y), 2)
        
        # Draw handle (square)
        handle_rect = self.get_handle_rect()
        handle_color = (50, 100, 200) if self.is_hovered or self.is_dragging else (100, 150, 255)
        pygame.draw.rect(surface, handle_color, handle_rect)
        pygame.draw.rect(surface, (100, 150, 255), handle_rect, 2)
    
    def update(self) -> None:
        """Update slider state - auto-center if enabled and not being dragged."""
        if self.auto_center and not self.is_dragging:
            # Gradually move towards center
            if abs(self.value) > 0.01:  # Small deadzone to prevent jitter
                self.value *= 0.95  # Decay factor - adjust for centering speed
                if abs(self.value) < 0.01:
                    self.value = 0.0


class VirtualControllerApp:
    """Main application class for the virtual controller interface."""
    
    def __init__(self):
        """Initialize the application."""
        # Initialize Pygame
        pygame.init()
        
        # Load configuration
        self.config = ControllerConfig()
        
        # Validate configuration
        is_valid, error_msg = self.config.validate_config()
        if not is_valid:
            print(f"Configuration error: {error_msg}")
            sys.exit(1)
        
        # Set up display
        self.width = self.config.get("ui.window_width", 1024)
        self.height = self.config.get("ui.window_height", 850)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Project Nimbus - Virtual Controller")
        
        # Set up font
        font_size = self.config.get("ui.font_size", 16)
        self.font = pygame.font.Font(None, font_size)
        self.title_font = pygame.font.Font(None, font_size + 8)
        
        # Initialize VJoy interface
        self.vjoy = VJoyInterface(self.config)
        
        # Set up joysticks
        joystick_size = self.config.get("ui.joystick_size", 300)
        joystick_radius = joystick_size // 2
        
        # Set up joysticks (adjusted for menu bar)
        left_center_x = self.width // 4
        left_center_y = self.height // 2 - 50
        right_center_x = 3 * self.width // 4
        right_center_y = self.height // 2 - 50
        
        # Draw joystick labels (moved higher)
        left_label = f"Left Stick"
        right_label = f"Right Stick"
        
        # Left joystick info
        left_text = self.font.render(left_label, True, (255, 255, 255))
        self.screen.blit(left_text, (left_center_x - 50, left_center_y - joystick_radius - 100))
        
        # Right joystick info
        right_text = self.font.render(right_label, True, (255, 255, 255))
        self.screen.blit(right_text, (right_center_x - 50, right_center_y - joystick_radius - 100))
        
        self.left_joystick = VirtualJoystick(
            left_center_x, left_center_y, joystick_radius, self.config, "left"
        )
        self.right_joystick = VirtualJoystick(
            right_center_x, right_center_y, joystick_radius, self.config, "right"
        )
        
        # Set up callbacks
        self.left_joystick.on_value_changed = self._on_left_joystick_changed
        self.right_joystick.on_value_changed = self._on_right_joystick_changed
        
        # Set up buttons
        self._setup_buttons()
        
        # Set up dialogs
        self.axis_config_dialog = AxisConfigDialog(self.config, self.screen)
        self.joystick_settings_dialog = JoystickSettingsDialog(self.config, self.screen)
        
        # Application state
        self.running = True
        self.clock = pygame.time.Clock()
        self.last_update_time = 0.0
        
        # Status display
        self.show_debug_info = False
        
        # Menu system
        self.menu_bar_height = 30
        self.menu_items = self._get_menu_items()
        self.active_menu = None
        self.menu_rects = {}
        
        print("Virtual Controller initialized successfully")
        print("Controls:")
        print("  - Drag joysticks with mouse")
        print("  - Use Lock X/Y buttons to lock axes")
        print("  - Use RESET buttons to center joysticks")
        print("  - Press ESC to exit")
        print("  - Press F1 to toggle debug info")
        print("  - Use File > Configure Axes to map joystick axes")
    
    def _get_menu_items(self) -> dict:
        """Get menu items for the menu bar."""
        return {
            "File": ["Configure Axes", "Exit"],
            "Joystick Settings": []
        }
    
    def _setup_buttons(self) -> None:
        """Set up UI buttons."""
        self.buttons = []
        button_width = 80
        button_height = 30
        
        # Left joystick controls (adjusted for menu bar)
        left_center_x = self.width // 4
        left_center_y = self.height // 2 - 50
        joystick_radius = self.config.get("ui.joystick_size", 300) // 2
        
        # Left Lock X button (above joystick)
        self.left_lock_x_btn = Button(
            left_center_x - button_width - 10,
            left_center_y - joystick_radius - 60,
            button_width, button_height,
            "Lock X", self.font, self.config
        )
        
        # Left Lock Y button (above joystick)
        self.left_lock_y_btn = Button(
            left_center_x + 10,
            left_center_y - joystick_radius - 60,
            button_width, button_height,
            "Lock Y", self.font, self.config
        )
        
        # Left RESET button
        self.left_reset_btn = Button(
            left_center_x - button_width // 2,
            left_center_y + joystick_radius + 10,
            button_width, button_height,
            "RESET", self.font, self.config
        )
        
        # Left joystick buttons (2x2 grid below left joystick, centered)
        left_button_start_y = left_center_y + joystick_radius + 70
        button_size = 40
        button_spacing = 50
        self.left_buttons = []
        for i in range(4):
            row = i // 2
            col = i % 2
            btn = Button(
                left_center_x - button_size - 5 + (col * (button_size + 10)),
                left_button_start_y + (row * (button_size + 10)),
                button_size, button_size,
                f"{i+1}", self.font, self.config, button_id=i+1
            )
            self.left_buttons.append(btn)
        
        # Right joystick controls (adjusted for menu bar)
        right_center_x = 3 * self.width // 4
        right_center_y = self.height // 2 - 50
        
        # Right Lock X button (above joystick)
        self.right_lock_x_btn = Button(
            right_center_x - button_width - 10,
            right_center_y - joystick_radius - 60,
            button_width, button_height,
            "Lock X", self.font, self.config
        )
        
        # Right Lock Y button (above joystick)
        self.right_lock_y_btn = Button(
            right_center_x + 10,
            right_center_y - joystick_radius - 60,
            button_width, button_height,
            "Lock Y", self.font, self.config
        )
        
        # Right RESET button
        self.right_reset_btn = Button(
            right_center_x - button_width // 2,
            right_center_y + joystick_radius + 10,
            button_width, button_height,
            "RESET", self.font, self.config
        )
        
        # Right joystick buttons (2x2 grid below right joystick, centered)
        right_button_start_y = right_center_y + joystick_radius + 70
        self.right_buttons = []
        for i in range(4):
            row = i // 2
            col = i % 2
            btn = Button(
                right_center_x - button_size - 5 + (col * (button_size + 10)),
                right_button_start_y + (row * (button_size + 10)),
                button_size, button_size,
                f"{i+5}", self.font, self.config, button_id=i+5
            )
            self.right_buttons.append(btn)
        
        # Throttle slider (vertical, center between joysticks) - no auto-center
        center_x = self.width // 2
        self.throttle_slider = Slider(
            center_x - 20, 80, 40, 300, "vertical", self.config, "Throttle", auto_center=False
        )
        # Set throttle to zero (bottom position)
        self.throttle_slider.value = -1.0
        
        # Rudder slider (horizontal, bottom center) - auto-centers when not dragging
        center_x = self.width // 2
        self.rudder_slider = Slider(
            center_x - 150, self.height - 80, 300, 40, "horizontal", self.config, "Rudder", auto_center=True
        )
        
        # Emergency and Center All buttons (below throttle with more spacing)
        button_y = self.height - 120
        self.emergency_btn = Button(
            center_x - 100, button_y, 80, 30,
            "EMERGENCY", self.font, self.config
        )
        self.center_all_btn = Button(
            center_x + 20, button_y, 80, 30,
            "CENTER ALL", self.font, self.config
        )
        
        # Store all buttons for easy iteration
        self.all_buttons = [
            self.left_lock_x_btn, self.left_reset_btn, self.left_lock_y_btn,
            self.right_lock_x_btn, self.right_reset_btn, self.right_lock_y_btn,
            self.emergency_btn, self.center_all_btn
        ] + self.left_buttons + self.right_buttons
    
    def _apply_sensitivity_curve(self, input_value: float) -> float:
        """
        Apply sensitivity curve to joystick input value.
        
        Args:
            input_value: Raw joystick input from -1.0 to 1.0
            
        Returns:
            Processed value with sensitivity curve applied
        """
        # Get sensitivity settings from joystick settings dialog
        if hasattr(self, 'joystick_settings_dialog'):
            return self.joystick_settings_dialog.calculate_curve_output(input_value)
        else:
            # Fallback to raw input if dialog not available
            return input_value
    
    def _on_left_joystick_changed(self, x: float, y: float) -> None:
        """Handle left joystick value changes."""
        # Apply sensitivity curve to input values
        processed_x = self._apply_sensitivity_curve(x)
        processed_y = self._apply_sensitivity_curve(y)
        
        # Get axis mappings from configuration
        left_x_axis = self.config.get("axis_mapping.left_x", "x")
        left_y_axis = self.config.get("axis_mapping.left_y", "y")
        
        # Update VJoy with processed values using configured mappings
        if self.vjoy.is_connected:
            if left_x_axis != "none":
                self.vjoy.update_axis(left_x_axis, processed_x)
            if left_y_axis != "none":
                self.vjoy.update_axis(left_y_axis, processed_y)
    
    def _on_right_joystick_changed(self, x: float, y: float) -> None:
        """Handle right joystick value changes."""
        # Apply sensitivity curve to input values
        processed_x = self._apply_sensitivity_curve(x)
        processed_y = self._apply_sensitivity_curve(y)
        
        # Get axis mappings from configuration
        right_x_axis = self.config.get("axis_mapping.right_x", "rx")
        right_y_axis = self.config.get("axis_mapping.right_y", "ry")
        
        # Update VJoy with processed values using configured mappings
        if self.vjoy.is_connected:
            if right_x_axis != "none":
                self.vjoy.update_axis(right_x_axis, processed_x)
            if right_y_axis != "none":
                self.vjoy.update_axis(right_y_axis, processed_y)
    
    def _on_throttle_changed(self, value: float) -> None:
        """Handle throttle slider value changes."""
        # Map throttle to Z axis (or configured axis)
        throttle_axis = self.config.get("axis_mapping.throttle", "z")
        if self.vjoy.is_connected and throttle_axis != "none":
            self.vjoy.update_axis(throttle_axis, value)
    
    def _on_rudder_changed(self, value: float) -> None:
        """Handle rudder slider value changes."""
        # Map rudder to RZ axis (or configured axis)
        rudder_axis = self.config.get("axis_mapping.rudder", "rz")
        if self.vjoy.is_connected and rudder_axis != "none":
            self.vjoy.update_axis(rudder_axis, value)
    
    def _show_axis_config(self) -> None:
        """Show the axis configuration dialog."""
        self.axis_config_dialog.show()
    
    def _show_joystick_settings(self) -> None:
        """Show the joystick settings dialog."""
        self.joystick_settings_dialog.show()
    
    def _exit_application(self) -> None:
        """Exit the application."""
        self.running = False
    
    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            # Handle quit events first, before dialogs
            if event.type == pygame.QUIT:
                self.running = False
                continue
            
            # Let dialogs handle events
            if self.axis_config_dialog.handle_event(event):
                continue
            if self.joystick_settings_dialog.handle_event(event):
                continue
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Close any open dialogs first, then menus, then app
                    if self.axis_config_dialog.is_visible:
                        self.axis_config_dialog.hide()
                    elif self.joystick_settings_dialog.is_visible:
                        self.joystick_settings_dialog.hide()
                    elif self.active_menu:
                        self.active_menu = None
                    else:
                        self.running = False
                elif event.key == pygame.K_F1:
                    self.show_debug_info = not self.show_debug_info
                elif event.key == pygame.K_SPACE:
                    # Space bar centers both joysticks
                    self.left_joystick.center()
                    self.right_joystick.center()
                elif event.key == pygame.K_c:
                    # C key shows axis config dialog
                    self._show_axis_config()
            
            # Handle joystick events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check menu bar clicks first
                    if self._handle_menu_click(event.pos):
                        continue
                    
                    # Check slider events first
                    if self.throttle_slider.handle_event(event):
                        self._on_throttle_changed(self.throttle_slider.value)
                        continue
                    if self.rudder_slider.handle_event(event):
                        self._on_rudder_changed(self.rudder_slider.value)
                        continue
                    
                    # Check button clicks
                    button_clicked = False
                    for button in self.all_buttons:
                        if button.handle_event(event):
                            self._handle_button_click(button)
                            button_clicked = True
                            break
                    
                    # Check joysticks if no button was clicked
                    if not button_clicked:
                        if not self.left_joystick.handle_mouse_down(event.pos):
                            self.right_joystick.handle_mouse_down(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    # Handle slider events
                    self.throttle_slider.handle_event(event)
                    self.rudder_slider.handle_event(event)
                    
                    # Handle button releases for joystick buttons
                    for button in self.left_buttons + self.right_buttons:
                        if button.rect.collidepoint(event.pos) and button.is_pressed:
                            if self.vjoy.is_connected:
                                self.vjoy.set_button(button.button_id, False)
                                print(f"Button {button.button_id} released")
                    
                    # Handle button events
                    for button in self.all_buttons:
                        button.handle_event(event)
                    
                    self.left_joystick.handle_mouse_up(event.pos)
                    self.right_joystick.handle_mouse_up(event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle slider events
                if self.throttle_slider.handle_event(event):
                    self._on_throttle_changed(self.throttle_slider.value)
                if self.rudder_slider.handle_event(event):
                    self._on_rudder_changed(self.rudder_slider.value)
                
                # Handle button hover events
                for button in self.all_buttons:
                    button.handle_event(event)
                
                self.left_joystick.handle_mouse_motion(event.pos)
                self.right_joystick.handle_mouse_motion(event.pos)
    
    def _handle_menu_click(self, pos: Tuple[int, int]) -> bool:
        """Handle menu bar clicks. Returns True if click was handled."""
        mouse_x, mouse_y = pos
        
        # First check if we're clicking on submenu items (if menu is open)
        if self.active_menu and self.active_menu in self.menu_items:
            if self._handle_submenu_click(pos):
                return True
        
        # Check if click is in menu bar area
        if mouse_y > self.menu_bar_height:
            if self.active_menu:
                self.active_menu = None
            return False
        
        # Check main menu items
        x_offset = 10
        for menu_name in self.menu_items.keys():
            menu_width = len(menu_name) * 10 + 20
            menu_rect = pygame.Rect(x_offset, 0, menu_width, self.menu_bar_height)
            if menu_rect.collidepoint(mouse_x, mouse_y):
                # Handle direct menu actions (no submenu)
                if menu_name == "Joystick Settings":
                    self._show_joystick_settings()
                    self.active_menu = None
                    return True
                elif self.active_menu == menu_name:
                    self.active_menu = None
                else:
                    self.active_menu = menu_name
                return True
            
            x_offset += menu_width
        
        # Close menu if clicking elsewhere in menu bar
        self.active_menu = None
        return True
    
    def _handle_submenu_click(self, pos: Tuple[int, int]) -> bool:
        """Handle submenu item clicks."""
        mouse_x, mouse_y = pos
        # Calculate submenu position
        x_offset = 10
        for menu_name in self.menu_items.keys():
            if menu_name == self.active_menu:
                break
            x_offset += len(menu_name) * 10 + 20
        
        # Check submenu items
        submenu_y = self.menu_bar_height
        for i, item in enumerate(self.menu_items[self.active_menu]):
            item_rect = pygame.Rect(x_offset, submenu_y + i * 25, 150, 25)
            if item_rect.collidepoint(mouse_x, mouse_y):
                if item == "Configure Axes":
                    self._show_axis_config()
                elif item == "Joystick Settings":
                    self._show_joystick_settings()
                elif item == "Exit":
                    pygame.quit()
                    sys.exit()
                
                self.active_menu = None
                return True
        
        return False
    
    def _handle_button_clicks(self) -> None:
        """Handle button clicks."""
        # This method is no longer needed as button events are handled directly in handle_events
        pass
    
    def _handle_button_click(self, button: Button) -> None:
        """Handle button click events."""
        if button == self.left_lock_x_btn:
            self.left_joystick.lock_axis("x", not self.left_joystick.x_locked)
            button.text = "Unlock X" if self.left_joystick.x_locked else "Lock X"
        
        elif button == self.left_lock_y_btn:
            self.left_joystick.lock_axis("y", not self.left_joystick.y_locked)
            button.text = "Unlock Y" if self.left_joystick.y_locked else "Lock Y"
        
        elif button == self.left_reset_btn:
            self.left_joystick.center()
        
        elif button == self.right_lock_x_btn:
            self.right_joystick.lock_axis("x", not self.right_joystick.x_locked)
            button.text = "Unlock X" if self.right_joystick.x_locked else "Lock X"
        
        elif button == self.right_lock_y_btn:
            self.right_joystick.lock_axis("y", not self.right_joystick.y_locked)
            button.text = "Unlock Y" if self.right_joystick.y_locked else "Lock Y"
        
        elif button == self.right_reset_btn:
            self.right_joystick.center()
        
        elif button == self.emergency_btn:
            self.vjoy.emergency_stop()
            self.left_joystick.center()
            self.right_joystick.center()
            self.throttle_slider.value = 0.0
            self.rudder_slider.value = 0.0
        
        elif button == self.center_all_btn:
            self.left_joystick.center()
            self.right_joystick.center()
            self.throttle_slider.value = 0.0
            self.rudder_slider.value = 0.0
        
        # Handle joystick buttons (1-8)
        elif button in self.left_buttons or button in self.right_buttons:
            # Send button press to VJoy (don't toggle, just send press state)
            if self.vjoy.is_connected:
                self.vjoy.set_button(button.button_id, True)
                print(f"Button {button.button_id} pressed")
    
    def update(self) -> None:
        """Update application state."""
        current_time = time.time()
        
        # Rate limiting for updates
        if current_time - self.last_update_time < 1.0 / 60.0:  # 60 FPS max
            return
        
        self.last_update_time = current_time
        
        # Update joysticks for auto-centering
        self.left_joystick.update()
        self.right_joystick.update()
        
        # Update sliders for auto-centering
        self.rudder_slider.update()
        if self.rudder_slider.auto_center:
            self._on_rudder_changed(self.rudder_slider.value)
        
        # Throttle doesn't auto-center, so no update needed
        self.throttle_slider.update()
        
        # Update button states based on joystick locks
        self.left_lock_x_btn.text = "Unlock X" if self.left_joystick.x_locked else "Lock X"
        self.left_lock_y_btn.text = "Unlock Y" if self.left_joystick.y_locked else "Lock Y"
        self.right_lock_x_btn.text = "Unlock X" if self.right_joystick.x_locked else "Lock X"
        self.right_lock_y_btn.text = "Unlock Y" if self.right_joystick.y_locked else "Lock Y"
    
    def draw(self) -> None:
        """Draw the application."""
        # Clear screen
        bg_color = self.config.get("ui.background_color", (20, 20, 20))
        self.screen.fill(bg_color)
        
        # Draw menu bar
        self._draw_menu_bar()
        
        
        
        # Draw joysticks
        self.left_joystick.draw(self.screen)
        self.right_joystick.draw(self.screen)
        
        # Draw buttons
        for button in self.all_buttons:
            button.draw(self.screen)
        
        # Draw sliders
        self.throttle_slider.draw(self.screen)
        self.rudder_slider.draw(self.screen)
        
        # Draw slider labels with better positioning to avoid overlap
        throttle_label = self.font.render("Throttle", True, self.config.get("ui.text_color", (255, 255, 255)))
        throttle_rect = throttle_label.get_rect(center=(self.throttle_slider.rect.centerx, self.throttle_slider.rect.y - 25))
        self.screen.blit(throttle_label, throttle_rect)
        
        rudder_label = self.font.render("Rudder", True, self.config.get("ui.text_color", (255, 255, 255)))
        rudder_rect = rudder_label.get_rect(center=(self.rudder_slider.rect.centerx, self.rudder_slider.rect.bottom + 15))
        self.screen.blit(rudder_label, rudder_rect)
        
        # Draw status information
        self._draw_status()
        
        # Draw debug information if enabled
        if self.show_debug_info:
            self._draw_debug_info()
        
        # Draw dialogs
        self.axis_config_dialog.draw(self.screen)
        self.joystick_settings_dialog.draw(self.screen)
        
        # Update display
        pygame.display.flip()
    
    def _draw_menu_bar(self) -> None:
        """Draw the menu bar."""
        # Menu bar background
        menu_bg_color = (60, 60, 60)
        menu_rect = pygame.Rect(0, 0, self.width, self.menu_bar_height)
        pygame.draw.rect(self.screen, menu_bg_color, menu_rect)
        pygame.draw.line(self.screen, (100, 100, 100), (0, self.menu_bar_height), (self.width, self.menu_bar_height))
        
        # Draw menu items
        x_offset = 10
        text_color = (255, 255, 255)
        
        for menu_name in self.menu_items.keys():
            menu_width = len(menu_name) * 10 + 20
            menu_rect = pygame.Rect(x_offset, 0, menu_width, self.menu_bar_height)
            
            # Highlight active menu
            if self.active_menu == menu_name:
                pygame.draw.rect(self.screen, (80, 80, 80), menu_rect)
            
            # Draw menu text
            menu_text = self.font.render(menu_name, True, text_color)
            text_rect = menu_text.get_rect(center=menu_rect.center)
            self.screen.blit(menu_text, text_rect)
            
            x_offset += menu_width
        
        # Draw submenu if active
        if self.active_menu and self.active_menu in self.menu_items:
            self._draw_submenu()
    
    def _draw_submenu(self) -> None:
        """Draw the active submenu."""
        # Calculate submenu position
        x_offset = 10
        for menu_name in self.menu_items.keys():
            menu_width = len(menu_name) * 10 + 20
            if menu_name == self.active_menu:
                break
            x_offset += menu_width
        
        submenu_items = self.menu_items[self.active_menu]
        submenu_width = 150
        submenu_height = len(submenu_items) * 25 + 10
        
        # Submenu background
        submenu_rect = pygame.Rect(x_offset, self.menu_bar_height, submenu_width, submenu_height)
        pygame.draw.rect(self.screen, (50, 50, 50), submenu_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), submenu_rect, 1)
        
        # Draw submenu items
        submenu_y = self.menu_bar_height + 5
        text_color = (255, 255, 255)
        
        for item_name in submenu_items:
            item_height = 25
            item_rect = pygame.Rect(x_offset, submenu_y, submenu_width, item_height)
            
            # Check if mouse is hovering over item
            mouse_pos = pygame.mouse.get_pos()
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (70, 70, 70), item_rect)
            
            # Draw item text
            item_text = self.font.render(item_name, True, text_color)
            text_rect = item_text.get_rect(center=(item_rect.centerx, item_rect.centery))
            self.screen.blit(item_text, text_rect)
            
            submenu_y += item_height
    
    def _draw_status(self) -> None:
        """Draw status information."""
        text_color = self.config.get("ui.text_color", (255, 255, 255))
        
        # VJoy status in lower right corner
        vjoy_status = self.vjoy.get_status()
        status_text = "VJoy: Connected" if vjoy_status['connected'] else "VJoy: Disconnected"
        if vjoy_status['failsafe_active']:
            status_text += " (FAILSAFE ACTIVE)"
        
        status_surface = self.font.render(status_text, True, text_color)
        status_rect = status_surface.get_rect()
        status_rect.bottomright = (self.width - 10, self.height - 10)
        self.screen.blit(status_surface, status_rect)
        
    
    def _draw_debug_info(self) -> None:
        """Draw debug information."""
        debug_y = 100
        text_color = (255, 255, 0)  # Yellow for debug info
        
        # Configuration info
        debug_lines = [
            f"Update Rate: {self.config.get('vjoy.update_rate', 60)} Hz",
            f"Left Dead Zone: {self.config.get('joysticks.left.dead_zone', 0.1):.3f}",
            f"Right Dead Zone: {self.config.get('joysticks.right.dead_zone', 0.1):.3f}",
            f"Left Sensitivity: {self.config.get('joysticks.left.sensitivity', 1.0):.3f}",
            f"Right Sensitivity: {self.config.get('joysticks.right.sensitivity', 1.0):.3f}",
            f"Failsafe: {'Enabled' if self.config.get('safety.enable_failsafe', True) else 'Disabled'}",
        ]
        
        for i, line in enumerate(debug_lines):
            debug_surface = self.font.render(line, True, text_color)
            self.screen.blit(debug_surface, (self.width - 300, debug_y + i * 20))
    
    def run(self) -> None:
        """Main application loop."""
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(60)  # 60 FPS
        
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        
        except Exception as e:
            print(f"Application error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Clean shutdown of the application."""
        print("Shutting down application...")
        
        # Save configuration
        self.config.save_config()
        
        # Shutdown VJoy interface
        self.vjoy.shutdown()
        
        # Quit Pygame
        pygame.quit()
        
        print("Shutdown complete")


def main():
    """Main entry point."""
    try:
        app = VirtualControllerApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
