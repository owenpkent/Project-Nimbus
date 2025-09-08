"""
Joystick Settings Dialog for Project Nimbus.
Allows users to configure sensitivity, deadzone, and extremity deadzone with XY graph visualization.
"""

import pygame
import math
from typing import Dict, Optional, List, Tuple
from config import ControllerConfig


class JoystickSettingsDialog:
    """
    Dialog window for configuring joystick sensitivity, deadzone, and extremity deadzone with XY graph.
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
        self.small_font = pygame.font.Font(None, 18)
        
        # Dialog dimensions - ensure it fits in parent window with margin
        parent_width = parent_surface.get_width()
        parent_height = parent_surface.get_height()
        
        self.width = min(1000, parent_width - 40)  # 20px margin on each side
        self.height = min(650, parent_height - 40)  # 20px margin top/bottom
        self.x = (parent_width - self.width) // 2
        self.y = (parent_height - self.height) // 2
        
        # UI state
        self.is_visible = False
        self.dragging_slider = None
        
        # Settings (0-100% ranges)
        self.sensitivity = 50.0  # 0-100%
        self.deadzone = 10.0     # 0-100%
        self.extremity_deadzone = 5.0  # 0-100%
        
        # Graph area - adjust size based on dialog dimensions
        graph_size = min(400, self.height - 200)  # Ensure graph fits with room for buttons
        self.graph_rect = pygame.Rect(self.x + 50, self.y + 80, graph_size, graph_size)
        
        # Slider definitions - position relative to dialog size
        # Ensure sliders start far enough right to avoid graph overlap
        min_slider_x = self.graph_rect.right + 80  # 80px gap from graph
        slider_start_x = max(min_slider_x, self.x + 550)
        slider_width = min(250, self.width - (slider_start_x - self.x) - 50)
        
        self.sliders = {
            "sensitivity": {
                "rect": pygame.Rect(slider_start_x, self.y + 120, slider_width, 20),
                "value": self.sensitivity,
                "min": 0.0,
                "max": 100.0,
                "label": "Sensitivity"
            },
            "deadzone": {
                "rect": pygame.Rect(slider_start_x, self.y + 180, slider_width, 20),
                "value": self.deadzone,
                "min": 0.0,
                "max": 100.0,
                "label": "Deadzone"
            },
            "extremity_deadzone": {
                "rect": pygame.Rect(slider_start_x, self.y + 240, slider_width, 20),
                "value": self.extremity_deadzone,
                "min": 0.0,
                "max": 100.0,
                "label": "Extremity Deadzone"
            }
        }
        
        # Buttons - ensure they're always visible at bottom with margin
        button_y = self.y + self.height - 50
        self.buttons = {
            "ok": pygame.Rect(self.x + self.width - 220, button_y, 100, 40),
            "cancel": pygame.Rect(self.x + self.width - 110, button_y, 100, 40),
            "reset": pygame.Rect(self.x + 50, button_y, 100, 40)
        }
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.button_color = (60, 60, 60)
        self.button_hover_color = (80, 80, 80)
        self.slider_color = (80, 80, 80)
        self.slider_handle_color = (100, 150, 255)
        self.graph_bg_color = (30, 30, 30)
        self.grid_color = (60, 60, 60)
        self.curve_color = (100, 150, 255)
        self.axis_color = (150, 150, 150)
        
        # Load current settings
        self.load_current_settings()
    
    def calculate_curve_output(self, input_value: float) -> float:
        """
        Calculate the output value based on input and current settings.
        
        Args:
            input_value: Input value from -1.0 to 1.0
            
        Returns:
            Output value from -1.0 to 1.0
        """
        # Convert percentages to normalized values
        # Scale deadzone to be less aggressive - use square root to make it less linear
        deadzone = (self.deadzone / 100.0) * 0.25  # Reduce maximum deadzone to 25% of slider value
        extremity_deadzone = self.extremity_deadzone / 100.0
        sensitivity = self.sensitivity / 100.0
        
        # Apply deadzone
        if abs(input_value) < deadzone:
            return 0.0
        
        # Normalize input after deadzone but before extremity deadzone
        sign = 1.0 if input_value >= 0 else -1.0
        abs_input = abs(input_value)
        
        # Calculate available range after deadzone
        available_range = 1.0 - deadzone
        normalized_input = (abs_input - deadzone) / available_range
        
        # Apply sensitivity curve
        if sensitivity == 0.5:
            # 50% = perfectly linear
            output = normalized_input
        elif sensitivity < 0.5:
            # Less than 50% = flatter curve (higher power)
            power = 1.0 + (0.5 - sensitivity) * 6.0  # Range from 1.0 to 4.0
            output = pow(normalized_input, power)
        else:
            # Greater than 50% = steeper curve (lower power)
            power = 1.0 - (sensitivity - 0.5) * 1.8  # Range from 1.0 to 0.1
            output = pow(normalized_input, power)
        
        # Apply extremity deadzone - scale output to stay within the non-extremity range
        if extremity_deadzone > 0:
            # Scale output to fit within (0, 1-extremity_deadzone) range
            max_output = 1.0 - extremity_deadzone
            output = output * max_output
        
        return output * sign
    
    def load_current_settings(self) -> None:
        """Load current joystick settings from configuration."""
        self.sensitivity = self.config.get("joystick_settings.sensitivity", 50.0)
        self.deadzone = self.config.get("joystick_settings.deadzone", 10.0)
        self.extremity_deadzone = self.config.get("joystick_settings.extremity_deadzone", 5.0)
        
        # Update slider values
        self.sliders["sensitivity"]["value"] = self.sensitivity
        self.sliders["deadzone"]["value"] = self.deadzone
        self.sliders["extremity_deadzone"]["value"] = self.extremity_deadzone
    
    def save_settings(self) -> None:
        """Save current settings to configuration."""
        self.config.set("joystick_settings.sensitivity", self.sensitivity)
        self.config.set("joystick_settings.deadzone", self.deadzone)
        self.config.set("joystick_settings.extremity_deadzone", self.extremity_deadzone)
        self.config.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset settings to default values."""
        self.sensitivity = 50.0
        self.deadzone = 10.0
        self.extremity_deadzone = 5.0
        
        # Update slider values
        self.sliders["sensitivity"]["value"] = self.sensitivity
        self.sliders["deadzone"]["value"] = self.deadzone
        self.sliders["extremity_deadzone"]["value"] = self.extremity_deadzone
    
    def show(self) -> None:
        """Show the dialog."""
        self.is_visible = True
        self.load_current_settings()
    
    def hide(self) -> None:
        """Hide the dialog."""
        self.is_visible = False
        self.dragging_slider = None
    
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
                
                # Handle slider clicks
                for slider_name, slider_data in self.sliders.items():
                    if slider_data["rect"].collidepoint(mouse_x, mouse_y):
                        self.dragging_slider = slider_name
                        self._handle_slider_click(slider_name, mouse_x)
                        return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_slider = None
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider:
                mouse_x, mouse_y = event.pos
                self._handle_slider_click(self.dragging_slider, mouse_x)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
        
        return True
    
    def _handle_slider_click(self, slider_name: str, mouse_x: int) -> None:
        """Handle slider click to update value."""
        slider = self.sliders[slider_name]
        rect = slider["rect"]
        
        # Calculate relative position (0.0 to 1.0)
        relative_x = (mouse_x - rect.x) / rect.width
        relative_x = max(0.0, min(1.0, relative_x))
        
        # Convert to slider value range
        value_range = slider["max"] - slider["min"]
        new_value = slider["min"] + (relative_x * value_range)
        
        # Update both slider and instance variable
        slider["value"] = new_value
        if slider_name == "sensitivity":
            self.sensitivity = new_value
        elif slider_name == "deadzone":
            self.deadzone = new_value
        elif slider_name == "extremity_deadzone":
            self.extremity_deadzone = new_value
    
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
        
        # Draw XY graph
        self._draw_graph(surface)
        
        # Draw sliders
        self._draw_sliders(surface)
        
        # Draw buttons
        self._draw_buttons(surface)
    
    def _draw_graph(self, surface: pygame.Surface) -> None:
        """Draw the XY sensitivity curve graph."""
        # Draw graph background
        pygame.draw.rect(surface, self.graph_bg_color, self.graph_rect)
        pygame.draw.rect(surface, self.border_color, self.graph_rect, 2)
        
        # Draw grid
        grid_spacing = 40
        for i in range(1, 10):
            x = self.graph_rect.x + i * grid_spacing
            y = self.graph_rect.y + i * grid_spacing
            if x < self.graph_rect.right:
                pygame.draw.line(surface, self.grid_color, (x, self.graph_rect.y), (x, self.graph_rect.bottom), 1)
            if y < self.graph_rect.bottom:
                pygame.draw.line(surface, self.grid_color, (self.graph_rect.x, y), (self.graph_rect.right, y), 1)
        
        # Draw axes
        center_x = self.graph_rect.centerx
        center_y = self.graph_rect.centery
        pygame.draw.line(surface, self.axis_color, (self.graph_rect.x, center_y), (self.graph_rect.right, center_y), 2)
        pygame.draw.line(surface, self.axis_color, (center_x, self.graph_rect.y), (center_x, self.graph_rect.bottom), 2)
        
        # Draw axis labels
        input_label = self.small_font.render("Input", True, self.text_color)
        surface.blit(input_label, (self.graph_rect.right - 40, center_y + 10))
        
        output_label = self.small_font.render("Output", True, self.text_color)
        rotated_label = pygame.transform.rotate(output_label, 90)
        surface.blit(rotated_label, (center_x - 25, self.graph_rect.y + 10))
        
        # Draw sensitivity curve
        points = []
        graph_width = self.graph_rect.width // 2
        graph_height = self.graph_rect.height // 2
        
        # Positive side of curve
        for i in range(201):  # 0 to 200 for smooth curve
            input_val = i / 200.0  # 0.0 to 1.0
            output_val = self.calculate_curve_output(input_val)
            
            # Convert to screen coordinates
            screen_x = center_x + int(input_val * graph_width)
            screen_y = center_y - int(output_val * graph_height)
            points.append((screen_x, screen_y))
        
        # Negative side of curve
        for i in range(1, 201):  # -1.0 to 0.0
            input_val = -i / 200.0
            output_val = self.calculate_curve_output(input_val)
            
            # Convert to screen coordinates
            screen_x = center_x + int(input_val * graph_width)
            screen_y = center_y - int(output_val * graph_height)
            points.insert(0, (screen_x, screen_y))
        
        # Draw the curve
        if len(points) > 1:
            pygame.draw.lines(surface, self.curve_color, False, points, 3)
        
        # Draw deadzone indicators
        deadzone_pixels = int((self.deadzone / 100.0) * graph_width)
        extremity_deadzone_pixels = int((self.extremity_deadzone / 100.0) * graph_width)
        
        # Deadzone rectangles
        if deadzone_pixels > 0:
            deadzone_rect = pygame.Rect(center_x - deadzone_pixels, center_y - 2, deadzone_pixels * 2, 4)
            pygame.draw.rect(surface, (255, 100, 100), deadzone_rect)
        
        # Extremity deadzone indicators
        if extremity_deadzone_pixels > 0:
            left_extremity = pygame.Rect(self.graph_rect.x, center_y - 2, extremity_deadzone_pixels, 4)
            right_extremity = pygame.Rect(self.graph_rect.right - extremity_deadzone_pixels, center_y - 2, extremity_deadzone_pixels, 4)
            pygame.draw.rect(surface, (255, 150, 100), left_extremity)
            pygame.draw.rect(surface, (255, 150, 100), right_extremity)
    
    def _draw_sliders(self, surface: pygame.Surface) -> None:
        """Draw slider controls."""
        for slider_name, slider_data in self.sliders.items():
            rect = slider_data["rect"]
            label = slider_data["label"]
            value = slider_data["value"]
            
            # Draw label - position to the left of slider but ensure no graph overlap
            label_text = self.font.render(f"{label}:", True, self.text_color)
            label_width = label_text.get_width()
            label_x = max(self.graph_rect.right + 10, rect.x - label_width - 10)
            surface.blit(label_text, (label_x, rect.y - 2))
            
            # Draw slider track
            pygame.draw.rect(surface, self.slider_color, rect)
            pygame.draw.rect(surface, self.border_color, rect, 1)
            
            # Draw slider handle
            value_ratio = (value - slider_data["min"]) / (slider_data["max"] - slider_data["min"])
            handle_x = rect.x + int(value_ratio * rect.width)
            handle_rect = pygame.Rect(handle_x - 8, rect.y - 4, 16, rect.height + 8)
            pygame.draw.rect(surface, self.slider_handle_color, handle_rect)
            pygame.draw.rect(surface, self.border_color, handle_rect, 2)
            
            # Draw value text
            value_text = self.small_font.render(f"{value:.1f}%", True, self.text_color)
            surface.blit(value_text, (rect.right + 15, rect.y - 2))
    
    
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
            pygame.draw.rect(surface, self.border_color, rect, 2)
            
            # Button text
            text = button_texts[button_name]
            button_text = self.font.render(text, True, self.text_color)
            text_rect = button_text.get_rect(center=rect.center)
            surface.blit(button_text, text_rect)
