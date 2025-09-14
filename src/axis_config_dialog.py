"""
Axis Configuration Dialog for Project Nimbus.
Allows users to map UI joystick axes to VJoy axes.
"""

import pygame
from typing import Dict, Optional, Callable
from .config import ControllerConfig


class AxisConfigDialog:
    """
    Dialog window for configuring axis mappings between UI joysticks and VJoy axes.
    """
    
    def __init__(self, config: ControllerConfig, parent_surface: pygame.Surface):
        """
        Initialize the axis configuration dialog.
        
        Args:
            config: Configuration manager instance
            parent_surface: Parent pygame surface
        """
        self.config = config
        self.parent_surface = parent_surface
        self.font = pygame.font.SysFont("serif", 20)
        self.title_font = pygame.font.SysFont("serif", 26)
        
        # Dialog dimensions - balanced width to fit content without cutting off buttons
        self.width = 750
        self.height = 450
        self.x = (parent_surface.get_width() - self.width) // 2
        self.y = (parent_surface.get_height() - self.height) // 2
        
        # Available VJoy axes
        self.vjoy_axes = ["x", "y", "z", "rx", "ry", "rz", "slider1", "slider2"]
        self.vjoy_axis_names = {
            "x": "X Axis",
            "y": "Y Axis", 
            "z": "Z Axis",
            "rx": "RX Axis (Rotation X)",
            "ry": "RY Axis (Rotation Y)",
            "rz": "RZ Axis (Rotation Z)",
            "slider1": "Slider 1",
            "slider2": "Slider 2"
        }
        
        # UI axes
        self.ui_axes = ["left_x", "left_y", "right_x", "right_y"]
        self.ui_axis_names = {
            "left_x": "Left Joystick X",
            "left_y": "Left Joystick Y",
            "right_x": "Right Joystick X", 
            "right_y": "Right Joystick Y"
        }
        
        # Current mappings
        self.current_mappings = {}
        self.load_current_mappings()
        
        # UI state
        self.selected_ui_axis = None
        self.dropdown_open = None
        self.is_visible = False
        
        # Buttons
        self.buttons = self._create_buttons()
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.button_color = (60, 60, 60)
        self.button_hover_color = (80, 80, 80)
        self.dropdown_color = (50, 50, 50)
        self.selected_color = (100, 150, 200)
    
    def load_current_mappings(self) -> None:
        """Load current axis mappings from configuration."""
        mapping_config = self.config.get("axis_mapping", {})
        for ui_axis in self.ui_axes:
            self.current_mappings[ui_axis] = mapping_config.get(ui_axis, "none")
    
    def save_mappings(self) -> None:
        """Save current mappings to configuration."""
        for ui_axis, vjoy_axis in self.current_mappings.items():
            self.config.set(f"axis_mapping.{ui_axis}", vjoy_axis)
        self.config.save_config()
    
    def _create_buttons(self) -> Dict[str, pygame.Rect]:
        """Create button rectangles."""
        button_width = 80
        button_height = 30
        
        return {
            "ok": pygame.Rect(self.x + self.width - 180, self.y + self.height - 80, button_width, button_height),
            "cancel": pygame.Rect(self.x + self.width - 90, self.y + self.height - 80, button_width, button_height),
            "reset": pygame.Rect(self.x + 20, self.y + self.height - 80, button_width, button_height)
        }
    
    def show(self) -> None:
        """Show the dialog."""
        self.is_visible = True
        self.load_current_mappings()
    
    def hide(self) -> None:
        """Hide the dialog."""
        self.is_visible = False
        self.dropdown_open = None
        self.selected_ui_axis = None
    
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
            mouse_x, mouse_y = event.pos
            
            # Check if click is outside dialog (close dialog)
            dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if not dialog_rect.collidepoint(mouse_x, mouse_y):
                self.hide()
                return True
            
            # Check button clicks
            for button_name, button_rect in self.buttons.items():
                if button_rect.collidepoint(mouse_x, mouse_y):
                    return self._handle_button_click(button_name)
            
            # Check axis mapping clicks
            return self._handle_axis_click(mouse_x, mouse_y)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
        
        return True  # Consume all events when dialog is open
    
    def _handle_button_click(self, button_name: str) -> bool:
        """Handle button clicks."""
        if button_name == "ok":
            self.save_mappings()
            self.hide()
        elif button_name == "cancel":
            self.load_current_mappings()  # Revert changes
            self.hide()
        elif button_name == "reset":
            self._reset_to_defaults()
    
    def _handle_axis_click(self, mouse_x: int, mouse_y: int) -> bool:
        """Handle clicks on axis mapping rows."""
        row_height = 50
        start_y = self.y + 100
        
        for i, ui_axis in enumerate(self.ui_axes):
            row_y = start_y + i * row_height
            dropdown_rect = pygame.Rect(self.x + 320, row_y + 10, 250, 30)
            
            if dropdown_rect.collidepoint(mouse_x, mouse_y):
                if self.dropdown_open == ui_axis:
                    self.dropdown_open = None
                else:
                    self.dropdown_open = ui_axis
                return True
            
            # Check dropdown options if open
            if self.dropdown_open == ui_axis:
                option_y = row_y + 40
                for j, vjoy_axis in enumerate(["none"] + self.vjoy_axes):
                    option_rect = pygame.Rect(self.x + 320, option_y + j * 30, 250, 28)
                    if option_rect.collidepoint(mouse_x, mouse_y):
                        self.current_mappings[ui_axis] = vjoy_axis
                        self.dropdown_open = None
                        return True
        
        # Close dropdown if clicking elsewhere
        self.dropdown_open = None
        return True
    
    def _reset_to_defaults(self) -> None:
        """Reset mappings to default values."""
        defaults = {
            "left_x": "x",
            "left_y": "y", 
            "right_x": "rx",
            "right_y": "ry"
        }
        self.current_mappings.update(defaults)
    
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
        
        # Draw title - moved down more to avoid overlap with title bar
        title_text = self.title_font.render("Configure Axis Mapping", True, self.text_color)
        title_rect = title_text.get_rect(center=(self.x + self.width // 2, self.y + 70))
        surface.blit(title_text, title_rect)
        
        # Draw instructions
        instruction_text = self.font.render("Map UI joystick axes to VJoy axes:", True, self.text_color)
        surface.blit(instruction_text, (self.x + 20, self.y + 105))
        
        # Draw axis mappings (dropdowns without open options)
        self._draw_axis_mappings(surface)
        
        # Draw buttons
        self._draw_buttons(surface)
        
        # Draw open dropdown options last (on top of everything)
        self._draw_open_dropdown(surface)
    
    def _draw_axis_mappings(self, surface: pygame.Surface) -> None:
        """Draw the axis mapping interface."""
        row_height = 50
        start_y = self.y + 145
        
        for i, ui_axis in enumerate(self.ui_axes):
            row_y = start_y + i * row_height
            
            # Draw UI axis label
            label_text = self.font.render(self.ui_axis_names[ui_axis], True, self.text_color)
            surface.blit(label_text, (self.x + 30, row_y + 15))
            
            # Draw arrow
            arrow_text = self.font.render("→", True, self.text_color)
            surface.blit(arrow_text, (self.x + 300, row_y + 15))
            
            # Draw VJoy axis dropdown - positioned to fit within dialog bounds
            current_mapping = self.current_mappings.get(ui_axis, "none")
            dropdown_rect = pygame.Rect(self.x + 340, row_y + 10, 280, 30)
            
            # Dropdown background
            dropdown_color = self.button_hover_color if self.dropdown_open == ui_axis else self.button_color
            pygame.draw.rect(surface, dropdown_color, dropdown_rect)
            pygame.draw.rect(surface, self.border_color, dropdown_rect, 1)
            
            # Dropdown text
            if current_mapping == "none":
                display_text = "Not Mapped"
            else:
                display_text = self.vjoy_axis_names.get(current_mapping, current_mapping.upper())
            
            dropdown_text = self.font.render(display_text, True, self.text_color)
            text_rect = dropdown_text.get_rect(center=(dropdown_rect.centerx - 10, dropdown_rect.centery))
            surface.blit(dropdown_text, text_rect)
            
            # Dropdown arrow
            arrow_text = self.font.render("▼", True, self.text_color)
            surface.blit(arrow_text, (dropdown_rect.right - 20, dropdown_rect.centery - 8))
    
    def _draw_dropdown_options(self, surface: pygame.Surface, dropdown_rect: pygame.Rect, ui_axis: str) -> None:
        """Draw dropdown options for axis selection."""
        option_y = dropdown_rect.bottom
        options = ["none"] + self.vjoy_axes
        
        # Draw a solid background for the entire dropdown area first
        total_height = len(options) * 30
        background_rect = pygame.Rect(dropdown_rect.x, option_y, dropdown_rect.width, total_height)
        pygame.draw.rect(surface, self.bg_color, background_rect)
        pygame.draw.rect(surface, self.border_color, background_rect, 2)
        
        for i, vjoy_axis in enumerate(options):
            option_rect = pygame.Rect(dropdown_rect.x, option_y + i * 30, dropdown_rect.width, 28)
            
            # Option background
            is_current = self.current_mappings.get(ui_axis) == vjoy_axis
            option_color = self.selected_color if is_current else self.dropdown_color
            pygame.draw.rect(surface, option_color, option_rect)
            pygame.draw.rect(surface, self.border_color, option_rect, 1)
            
            # Option text
            if vjoy_axis == "none":
                display_text = "Not Mapped"
            else:
                display_text = self.vjoy_axis_names.get(vjoy_axis, vjoy_axis.upper())
            
            option_text = self.font.render(display_text, True, self.text_color)
            text_rect = option_text.get_rect(center=option_rect.center)
            surface.blit(option_text, text_rect)
    
    def _draw_open_dropdown(self, surface: pygame.Surface) -> None:
        """Draw the currently open dropdown options on top of everything else."""
        if not self.dropdown_open:
            return
        
        # Find the dropdown rect for the open dropdown
        row_height = 50
        start_y = self.y + 100
        
        for i, ui_axis in enumerate(self.ui_axes):
            if ui_axis == self.dropdown_open:
                row_y = start_y + i * row_height
                dropdown_rect = pygame.Rect(self.x + 320, row_y + 10, 250, 30)
                self._draw_dropdown_options(surface, dropdown_rect, ui_axis)
                break
    
    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """Draw dialog buttons."""
        button_texts = {
            "ok": "OK",
            "cancel": "Cancel", 
            "reset": "Reset"
        }
        
        for button_name, button_rect in self.buttons.items():
            # Button background
            pygame.draw.rect(surface, self.button_color, button_rect)
            pygame.draw.rect(surface, self.border_color, button_rect, 1)
            
            # Button text
            button_text = self.font.render(button_texts[button_name], True, self.text_color)
            text_rect = button_text.get_rect(center=button_rect.center)
            surface.blit(button_text, text_rect)
