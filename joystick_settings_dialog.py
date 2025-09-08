"""
Joystick Settings Dialog for Project Nimbus.
Allows users to configure sensitivity curves, dead zones, and other joystick parameters.
"""

import pygame
from typing import Dict, Optional, List, Tuple
from config import ControllerConfig


class JoystickSettingsDialog:
    """
    Dialog window for configuring joystick sensitivity curves, dead zones, and other parameters.
    """
    
    def __init__(self, config: ControllerConfig, parent_surface: pygame.Surface):
        """
        Initialize the joystick settings dialog.
        
        Args:
            config: Configuration manager instance
            parent_surface: Parent pygame surface
        """
        self.config = config
        self.parent_surface = parent_surface
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)
        
        # Dialog dimensions
        self.width = 800
        self.height = 600
        self.x = (parent_surface.get_width() - self.width) // 2
        self.y = (parent_surface.get_height() - self.height) // 2
        
        # Available curve types
        self.curve_types = ["linear", "quadratic", "cubic", "exponential"]
        self.curve_type_names = {
            "linear": "Linear",
            "quadratic": "Quadratic", 
            "cubic": "Cubic",
            "exponential": "Exponential"
        }
        
        # Joystick identifiers
        self.joysticks = ["left", "right"]
        self.joystick_names = {
            "left": "Left Joystick",
            "right": "Right Joystick"
        }
        
        # UI state
        self.is_visible = False
        self.selected_joystick = "left"
        self.dropdown_open = None
        
        # Current settings (loaded from config)
        self.current_settings = {}
        
        # UI elements
        self.buttons = self._create_buttons()
        self.sliders = self._create_sliders()
        self.dropdowns = self._create_dropdowns()
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.button_color = (60, 60, 60)
        self.button_hover_color = (80, 80, 80)
        self.dropdown_color = (50, 50, 50)
        self.selected_color = (100, 150, 200)
        self.slider_color = (80, 80, 80)
        self.slider_handle_color = (150, 150, 150)
        
        # Load current settings
        self.load_current_settings()
    
    def _create_buttons(self) -> Dict[str, pygame.Rect]:
        """Create button rectangles."""
        button_width = 100
        button_height = 35
        
        return {
            "ok": pygame.Rect(self.x + self.width - 220, self.y + self.height - 50, button_width, button_height),
            "cancel": pygame.Rect(self.x + self.width - 110, self.y + self.height - 50, button_width, button_height),
            "reset": pygame.Rect(self.x + 20, self.y + self.height - 50, button_width, button_height),
            "left_tab": pygame.Rect(self.x + 20, self.y + 60, 120, 30),
            "right_tab": pygame.Rect(self.x + 150, self.y + 60, 120, 30)
        }
    
    def _create_sliders(self) -> Dict[str, Dict]:
        """Create slider definitions."""
        slider_width = 200
        slider_height = 20
        start_y = self.y + 150
        
        return {
            "dead_zone": {
                "rect": pygame.Rect(self.x + 200, start_y, slider_width, slider_height),
                "min": 0.0,
                "max": 0.5,
                "value": 0.1
            },
            "sensitivity": {
                "rect": pygame.Rect(self.x + 200, start_y + 60, slider_width, slider_height),
                "min": 0.1,
                "max": 3.0,
                "value": 1.0
            },
            "curve_power": {
                "rect": pygame.Rect(self.x + 200, start_y + 180, slider_width, slider_height),
                "min": 1.0,
                "max": 5.0,
                "value": 2.0
            },
            "max_range": {
                "rect": pygame.Rect(self.x + 200, start_y + 240, slider_width, slider_height),
                "min": 0.5,
                "max": 1.0,
                "value": 1.0
            }
        }
    
    def _create_dropdowns(self) -> Dict[str, pygame.Rect]:
        """Create dropdown rectangles."""
        return {
            "curve_type": pygame.Rect(self.x + 200, self.y + 270, 200, 30)
        }
    
    def load_current_settings(self) -> None:
        """Load current joystick settings from configuration."""
        for joystick in self.joysticks:
            self.current_settings[joystick] = {
                "dead_zone": self.config.get(f"joysticks.{joystick}.dead_zone", 0.1),
                "sensitivity": self.config.get(f"joysticks.{joystick}.sensitivity", 1.0),
                "curve_type": self.config.get(f"joysticks.{joystick}.curve_type", "linear"),
                "curve_power": self.config.get(f"joysticks.{joystick}.curve_power", 2.0),
                "max_range": self.config.get(f"joysticks.{joystick}.max_range", 1.0),
                "invert_x": self.config.get(f"joysticks.{joystick}.invert_x", False),
                "invert_y": self.config.get(f"joysticks.{joystick}.invert_y", False)
            }
        
        # Update slider values for selected joystick
        self._update_slider_values()
    
    def _update_slider_values(self) -> None:
        """Update slider values based on selected joystick."""
        settings = self.current_settings[self.selected_joystick]
        self.sliders["dead_zone"]["value"] = settings["dead_zone"]
        self.sliders["sensitivity"]["value"] = settings["sensitivity"]
        self.sliders["curve_power"]["value"] = settings["curve_power"]
        self.sliders["max_range"]["value"] = settings["max_range"]
    
    def save_settings(self) -> None:
        """Save current settings to configuration."""
        for joystick, settings in self.current_settings.items():
            for key, value in settings.items():
                self.config.set(f"joysticks.{joystick}.{key}", value)
        self.config.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset settings to default values."""
        defaults = {
            "dead_zone": 0.1,
            "sensitivity": 1.0,
            "curve_type": "linear",
            "curve_power": 2.0,
            "max_range": 1.0,
            "invert_x": False,
            "invert_y": False
        }
        
        for joystick in self.joysticks:
            self.current_settings[joystick].update(defaults)
        
        self._update_slider_values()
    
    def show(self) -> None:
        """Show the dialog."""
        self.is_visible = True
        self.load_current_settings()
    
    def hide(self) -> None:
        """Hide the dialog."""
        self.is_visible = False
        self.dropdown_open = None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events for the dialog.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled by dialog
        """
        if not self.is_visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = event.pos
                
                # Check if click is outside dialog
                dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                if not dialog_rect.collidepoint(mouse_x, mouse_y):
                    return True  # Consume event but don't close dialog
                
                # Handle button clicks
                if self.buttons["ok"].collidepoint(mouse_x, mouse_y):
                    self.save_settings()
                    self.hide()
                    return True
                elif self.buttons["cancel"].collidepoint(mouse_x, mouse_y):
                    self.hide()
                    return True
                elif self.buttons["reset"].collidepoint(mouse_x, mouse_y):
                    self.reset_to_defaults()
                    return True
                elif self.buttons["left_tab"].collidepoint(mouse_x, mouse_y):
                    self._save_current_slider_values()
                    self.selected_joystick = "left"
                    self._update_slider_values()
                    return True
                elif self.buttons["right_tab"].collidepoint(mouse_x, mouse_y):
                    self._save_current_slider_values()
                    self.selected_joystick = "right"
                    self._update_slider_values()
                    return True
                
                # Handle slider clicks
                for slider_name, slider_data in self.sliders.items():
                    if slider_data["rect"].collidepoint(mouse_x, mouse_y):
                        self._handle_slider_click(slider_name, mouse_x)
                        return True
                
                # Handle dropdown clicks
                for dropdown_name, dropdown_rect in self.dropdowns.items():
                    if dropdown_rect.collidepoint(mouse_x, mouse_y):
                        self.dropdown_open = dropdown_name if self.dropdown_open != dropdown_name else None
                        return True
                
                # Handle dropdown option clicks
                if self.dropdown_open == "curve_type":
                    option_y = self.dropdowns["curve_type"].bottom
                    for i, curve_type in enumerate(self.curve_types):
                        option_rect = pygame.Rect(
                            self.dropdowns["curve_type"].x,
                            option_y + i * 25,
                            self.dropdowns["curve_type"].width,
                            25
                        )
                        if option_rect.collidepoint(mouse_x, mouse_y):
                            self.current_settings[self.selected_joystick]["curve_type"] = curve_type
                            self.dropdown_open = None
                            return True
                
                # Close dropdown if clicking elsewhere
                self.dropdown_open = None
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
        
        return True
    
    def _save_current_slider_values(self) -> None:
        """Save current slider values to settings."""
        settings = self.current_settings[self.selected_joystick]
        settings["dead_zone"] = self.sliders["dead_zone"]["value"]
        settings["sensitivity"] = self.sliders["sensitivity"]["value"]
        settings["curve_power"] = self.sliders["curve_power"]["value"]
        settings["max_range"] = self.sliders["max_range"]["value"]
    
    def _handle_slider_click(self, slider_name: str, mouse_x: int) -> None:
        """Handle slider click to update value."""
        slider = self.sliders[slider_name]
        rect = slider["rect"]
        
        # Calculate relative position (0.0 to 1.0)
        relative_x = (mouse_x - rect.x) / rect.width
        relative_x = max(0.0, min(1.0, relative_x))
        
        # Convert to slider value range
        value_range = slider["max"] - slider["min"]
        slider["value"] = slider["min"] + (relative_x * value_range)
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog if visible."""
        if not self.is_visible:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Draw dialog background
        dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, dialog_rect)
        pygame.draw.rect(surface, self.border_color, dialog_rect, 2)
        
        # Draw title
        title_text = self.title_font.render("Joystick Settings", True, self.text_color)
        title_rect = title_text.get_rect(centerx=self.x + self.width // 2, y=self.y + 15)
        surface.blit(title_text, title_rect)
        
        # Draw joystick tabs
        self._draw_tabs(surface)
        
        # Draw settings for selected joystick
        self._draw_settings(surface)
        
        # Draw buttons
        self._draw_buttons(surface)
        
        # Draw dropdown options if open
        if self.dropdown_open:
            self._draw_dropdown_options(surface)
    
    def _draw_tabs(self, surface: pygame.Surface) -> None:
        """Draw joystick selection tabs."""
        for joystick in self.joysticks:
            button_key = f"{joystick}_tab"
            rect = self.buttons[button_key]
            
            # Tab background
            is_selected = joystick == self.selected_joystick
            tab_color = self.selected_color if is_selected else self.button_color
            pygame.draw.rect(surface, tab_color, rect)
            pygame.draw.rect(surface, self.border_color, rect, 1)
            
            # Tab text
            tab_text = self.font.render(self.joystick_names[joystick], True, self.text_color)
            text_rect = tab_text.get_rect(center=rect.center)
            surface.blit(tab_text, text_rect)
    
    def _draw_settings(self, surface: pygame.Surface) -> None:
        """Draw settings controls for selected joystick."""
        start_y = self.y + 120
        label_x = self.x + 30
        
        # Dead Zone
        dead_zone_label = self.font.render("Dead Zone:", True, self.text_color)
        surface.blit(dead_zone_label, (label_x, start_y + 30))
        self._draw_slider(surface, "dead_zone")
        
        # Sensitivity
        sensitivity_label = self.font.render("Sensitivity:", True, self.text_color)
        surface.blit(sensitivity_label, (label_x, start_y + 90))
        self._draw_slider(surface, "sensitivity")
        
        # Curve Type
        curve_label = self.font.render("Curve Type:", True, self.text_color)
        surface.blit(curve_label, (label_x, start_y + 150))
        self._draw_dropdown(surface, "curve_type")
        
        # Curve Power (only show for non-linear curves)
        current_curve = self.current_settings[self.selected_joystick]["curve_type"]
        if current_curve != "linear":
            power_label = self.font.render("Curve Power:", True, self.text_color)
            surface.blit(power_label, (label_x, start_y + 210))
            self._draw_slider(surface, "curve_power")
        
        # Max Range
        range_label = self.font.render("Max Range:", True, self.text_color)
        surface.blit(range_label, (label_x, start_y + 270))
        self._draw_slider(surface, "max_range")
    
    def _draw_slider(self, surface: pygame.Surface, slider_name: str) -> None:
        """Draw a slider control."""
        slider = self.sliders[slider_name]
        rect = slider["rect"]
        
        # Slider track
        pygame.draw.rect(surface, self.slider_color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)
        
        # Slider handle
        value_ratio = (slider["value"] - slider["min"]) / (slider["max"] - slider["min"])
        handle_x = rect.x + int(value_ratio * rect.width)
        handle_rect = pygame.Rect(handle_x - 5, rect.y - 2, 10, rect.height + 4)
        pygame.draw.rect(surface, self.slider_handle_color, handle_rect)
        
        # Value text
        value_text = self.small_font.render(f"{slider['value']:.2f}", True, self.text_color)
        surface.blit(value_text, (rect.right + 10, rect.y))
    
    def _draw_dropdown(self, surface: pygame.Surface, dropdown_name: str) -> None:
        """Draw a dropdown control."""
        rect = self.dropdowns[dropdown_name]
        
        # Dropdown background
        pygame.draw.rect(surface, self.dropdown_color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)
        
        # Current value text
        if dropdown_name == "curve_type":
            current_value = self.current_settings[self.selected_joystick]["curve_type"]
            display_text = self.curve_type_names[current_value]
        else:
            display_text = "Unknown"
        
        text_surface = self.font.render(display_text, True, self.text_color)
        surface.blit(text_surface, (rect.x + 5, rect.y + 5))
        
        # Dropdown arrow
        arrow_text = self.font.render("▼", True, self.text_color)
        surface.blit(arrow_text, (rect.right - 20, rect.y + 5))
    
    def _draw_dropdown_options(self, surface: pygame.Surface) -> None:
        """Draw dropdown options."""
        if self.dropdown_open == "curve_type":
            dropdown_rect = self.dropdowns["curve_type"]
            option_y = dropdown_rect.bottom
            
            # Background for all options
            total_height = len(self.curve_types) * 25
            background_rect = pygame.Rect(dropdown_rect.x, option_y, dropdown_rect.width, total_height)
            pygame.draw.rect(surface, self.bg_color, background_rect)
            pygame.draw.rect(surface, self.border_color, background_rect, 2)
            
            # Individual options
            for i, curve_type in enumerate(self.curve_types):
                option_rect = pygame.Rect(dropdown_rect.x, option_y + i * 25, dropdown_rect.width, 25)
                
                # Highlight current selection
                is_current = self.current_settings[self.selected_joystick]["curve_type"] == curve_type
                if is_current:
                    pygame.draw.rect(surface, self.selected_color, option_rect)
                
                pygame.draw.rect(surface, self.border_color, option_rect, 1)
                
                # Option text
                option_text = self.font.render(self.curve_type_names[curve_type], True, self.text_color)
                surface.blit(option_text, (option_rect.x + 5, option_rect.y + 2))
    
    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """Draw dialog buttons."""
        button_texts = {
            "ok": "OK",
            "cancel": "Cancel", 
            "reset": "Reset"
        }
        
        for button_name in ["ok", "cancel", "reset"]:
            rect = self.buttons[button_name]
            
            # Button background
            pygame.draw.rect(surface, self.button_color, rect)
            pygame.draw.rect(surface, self.border_color, rect, 1)
            
            # Button text
            text = button_texts[button_name]
            button_text = self.font.render(text, True, self.text_color)
            text_rect = button_text.get_rect(center=rect.center)
            surface.blit(button_text, text_rect)
