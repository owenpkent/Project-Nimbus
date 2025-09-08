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


class Button:
    """Simple button class for UI controls."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font: pygame.font.Font, config: ControllerConfig):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.config = config
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
            color = self.config.get("ui.button_hover_color", (100, 25, 25))
        elif self.is_hovered:
            color = self.config.get("ui.button_hover_color", (100, 25, 25))
        else:
            color = self.config.get("ui.button_color", (60, 15, 15))
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, self.config.get("ui.text_color", (255, 255, 255)), self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.config.get("ui.text_color", (255, 255, 255)))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


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
        self.height = self.config.get("ui.window_height", 600)
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
        left_center_y = self.height // 2 + 20
        right_center_x = 3 * self.width // 4
        right_center_y = self.height // 2 + 20
        
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
        
        # Set up axis configuration dialog
        self.axis_config_dialog = AxisConfigDialog(self.config, self.screen)
        
        # Application state
        self.running = True
        self.clock = pygame.time.Clock()
        self.last_update_time = 0.0
        
        # Status display
        self.show_debug_info = False
        
        # Menu system
        self.menu_bar_height = 30
        self.menu_items = self._setup_menu_items()
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
    
    def _setup_menu_items(self) -> dict:
        """Set up menu structure."""
        return {
            "File": ["Configure Axes", "Exit"]
        }
    
    def _setup_buttons(self) -> None:
        """Set up UI buttons."""
        self.buttons = []
        button_width = 80
        button_height = 30
        
        # Left joystick controls (adjusted for menu bar)
        left_center_x = self.width // 4
        left_center_y = self.height // 2 + 20
        joystick_radius = self.config.get("ui.joystick_size", 300) // 2
        
        # Left Lock X button
        self.left_lock_x_btn = Button(
            left_center_x - joystick_radius - 10 - button_width,
            left_center_y - joystick_radius - 50,
            button_width, button_height,
            "Lock X", self.font, self.config
        )
        
        # Left RESET button
        self.left_reset_btn = Button(
            left_center_x - button_width // 2,
            left_center_y + joystick_radius + 10,
            button_width, button_height,
            "RESET", self.font, self.config
        )
        
        # Left Lock Y button
        self.left_lock_y_btn = Button(
            left_center_x + joystick_radius + 10,
            left_center_y - joystick_radius - 50,
            button_width, button_height,
            "Lock Y", self.font, self.config
        )
        
        # Right joystick controls (adjusted for menu bar)
        right_center_x = 3 * self.width // 4
        right_center_y = self.height // 2 + 20
        
        # Right Lock X button
        self.right_lock_x_btn = Button(
            right_center_x - joystick_radius - 10 - button_width,
            right_center_y - joystick_radius - 50,
            button_width, button_height,
            "Lock X", self.font, self.config
        )
        
        # Right RESET button
        self.right_reset_btn = Button(
            right_center_x - button_width // 2,
            right_center_y + joystick_radius + 10,
            button_width, button_height,
            "RESET", self.font, self.config
        )
        
        # Right Lock Y button
        self.right_lock_y_btn = Button(
            right_center_x + joystick_radius + 10,
            right_center_y - joystick_radius - 50,
            button_width, button_height,
            "Lock Y", self.font, self.config
        )
        
        # Additional control buttons (bottom center)
        center_x = self.width // 2
        bottom_y = self.height - 100
        
        # Emergency stop button
        self.emergency_btn = Button(
            center_x - button_width - 10,
            bottom_y - 50,
            button_width, button_height,
            "EMERGENCY", self.font, self.config
        )
        
        # Center all button
        self.center_all_btn = Button(
            center_x + 10,
            bottom_y - 50,
            button_width, button_height,
            "CENTER ALL", self.font, self.config
        )
        
        # Store all buttons for easy iteration
        self.all_buttons = [
            self.left_lock_x_btn, self.left_reset_btn, self.left_lock_y_btn,
            self.right_lock_x_btn, self.right_reset_btn, self.right_lock_y_btn,
            self.emergency_btn, self.center_all_btn
        ]
    
    def _on_left_joystick_changed(self, x: float, y: float) -> None:
        """Handle left joystick value changes."""
        # Get axis mappings from configuration
        left_x_axis = self.config.get("axis_mapping.left_x", "x")
        left_y_axis = self.config.get("axis_mapping.left_y", "y")
        
        # Update VJoy with new values using configured mappings
        if self.vjoy.is_connected:
            if left_x_axis != "none":
                self.vjoy.update_axis(left_x_axis, x)
            if left_y_axis != "none":
                self.vjoy.update_axis(left_y_axis, y)
    
    def _on_right_joystick_changed(self, x: float, y: float) -> None:
        """Handle right joystick value changes."""
        # Get axis mappings from configuration
        right_x_axis = self.config.get("axis_mapping.right_x", "rx")
        right_y_axis = self.config.get("axis_mapping.right_y", "ry")
        
        # Update VJoy with new values using configured mappings
        if self.vjoy.is_connected:
            if right_x_axis != "none":
                self.vjoy.update_axis(right_x_axis, x)
            if right_y_axis != "none":
                self.vjoy.update_axis(right_y_axis, y)
    
    def _show_axis_config(self) -> None:
        """Show the axis configuration dialog."""
        self.axis_config_dialog.show()
    
    def _exit_application(self) -> None:
        """Exit the application."""
        self.running = False
    
    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            # Let axis config dialog handle events first
            if self.axis_config_dialog.handle_event(event):
                continue
                
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.active_menu:
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
                    # Handle button events
                    for button in self.all_buttons:
                        button.handle_event(event)
                    
                    self.left_joystick.handle_mouse_up(event.pos)
                    self.right_joystick.handle_mouse_up(event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
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
                if self.active_menu == menu_name:
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
            print("EMERGENCY STOP ACTIVATED")
        
        elif button == self.center_all_btn:
            self.left_joystick.center()
            self.right_joystick.center()
    
    def update(self) -> None:
        """Update application state."""
        current_time = time.time()
        
        # Rate limiting for updates
        if current_time - self.last_update_time < 1.0 / 60.0:  # 60 FPS max
            return
        
        self.last_update_time = current_time
        
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
        
        # Draw title (adjusted for menu bar)
        title_text = self.title_font.render("Project Nimbus - Virtual Controller", True, 
                                           self.config.get("ui.text_color", (255, 255, 255)))
        title_rect = title_text.get_rect(center=(self.width // 2, self.menu_bar_height + 20))
        self.screen.blit(title_text, title_rect)
        
        # Draw joystick labels (adjusted for menu bar)
        left_label = self.font.render("Left Stick", True, self.config.get("ui.text_color", (255, 255, 255)))
        left_rect = left_label.get_rect(center=(self.width // 4, self.menu_bar_height + 80))
        self.screen.blit(left_label, left_rect)
        
        right_label = self.font.render("Right Stick", True, self.config.get("ui.text_color", (255, 255, 255)))
        right_rect = right_label.get_rect(center=(3 * self.width // 4, self.menu_bar_height + 80))
        self.screen.blit(right_label, right_rect)
        
        # Draw joysticks
        self.left_joystick.draw(self.screen)
        self.right_joystick.draw(self.screen)
        
        # Draw buttons
        for button in self.all_buttons:
            button.draw(self.screen)
        
        # Draw status information
        self._draw_status()
        
        # Draw debug information if enabled
        if self.show_debug_info:
            self._draw_debug_info()
        
        # Draw axis configuration dialog
        self.axis_config_dialog.draw(self.screen)
        
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
        x_offset = self.width - 300
        y_offset = self.menu_bar_height + 10
        text_color = self.config.get("ui.text_color", (255, 255, 255))
        
        # VJoy status
        vjoy_status = self.vjoy.get_status()
        status_text = "VJoy: Connected" if vjoy_status['connected'] else "VJoy: Disconnected"
        if vjoy_status['failsafe_active']:
            status_text += " (FAILSAFE ACTIVE)"
        
        status_surface = self.font.render(status_text, True, text_color)
        self.screen.blit(status_surface, (x_offset, y_offset))
        
        # Joystick values
        left_x, left_y = self.left_joystick.get_position()
        right_x, right_y = self.right_joystick.get_position()
        
        left_text = f"Left: X={left_x:.3f}, Y={left_y:.3f}"
        right_text = f"Right: X={right_x:.3f}, Y={right_y:.3f}"
        
        left_surface = self.font.render(left_text, True, text_color)
        right_surface = self.font.render(right_text, True, text_color)
        
        self.screen.blit(left_surface, (x_offset, y_offset + 25))
        self.screen.blit(right_surface, (x_offset, y_offset + 50))
    
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
