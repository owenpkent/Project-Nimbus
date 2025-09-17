"""
Button Settings Dialog for Project Nimbus.
Allows users to configure button modes (momentary vs toggle) for each button.
"""

import pygame
from typing import Dict, Optional, List, Tuple
from .config import ControllerConfig


class ToggleSwitch:
    """A toggle switch UI component."""
    
    def __init__(self, x: int, y: int, width: int, height: int, initial_state: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.state = initial_state
        self.is_hovered = False
        self.is_dragging = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the toggle switch."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the toggle switch."""
        # Switch background - much brighter colors for better visibility
        bg_color = (0, 200, 0) if self.state else (200, 60, 60)  # Bright green ON, red OFF
        if self.is_hovered:
            bg_color = tuple(min(255, c + 30) for c in bg_color)
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=self.rect.height // 2)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=self.rect.height // 2)
        
        # Switch handle
        handle_radius = self.rect.height // 2 - 2
        handle_x = self.rect.right - handle_radius - 2 if self.state else self.rect.left + handle_radius + 2
        handle_y = self.rect.centery
        pygame.draw.circle(surface, (255, 255, 255), (handle_x, handle_y), handle_radius)
        pygame.draw.circle(surface, (150, 150, 150), (handle_x, handle_y), handle_radius, 2)


class ButtonSettingsDialog:
    """
    Dialog window for configuring button modes (momentary vs toggle).
    """
    
    def __init__(self, config: ControllerConfig, parent_surface: pygame.Surface):
        """
        Initialize the button settings dialog.
        
        Args:
            config: Configuration manager instance
            parent_surface: Parent pygame surface
        """
        self.config = config
        self.parent_surface = parent_surface
        self.font = pygame.font.SysFont("serif", config.get_scaled_int(18))
        self.title_font = pygame.font.SysFont("serif", config.get_scaled_int(24))
        self.small_font = pygame.font.SysFont("serif", config.get_scaled_int(14))
        
        # Dialog dimensions
        parent_width = parent_surface.get_width()
        parent_height = parent_surface.get_height()
        
        self.width = min(config.get_scaled_int(500), parent_width - config.get_scaled_int(40))
        self.height = min(config.get_scaled_int(600), parent_height - config.get_scaled_int(40))
        self.x = (parent_width - self.width) // 2
        self.y = (parent_height - self.height) // 2
        
        # UI state
        self.is_visible = False
        
        # Button configurations - load from config or use defaults
        self.button_modes = {}
        for i in range(1, 11):  # Buttons 1-10
            self.button_modes[i] = self.config.get(f"buttons.button_{i}.toggle_mode", False)
        
        # Create toggle switches
        self.toggle_switches = {}
        self._create_toggle_switches()
        
        # Close button
        close_btn_size = config.get_scaled_int(30)
        self.close_button = pygame.Rect(
            self.x + self.width - close_btn_size - config.get_scaled_int(10),
            self.y + config.get_scaled_int(10),
            close_btn_size, close_btn_size
        )
    
    def _create_toggle_switches(self) -> None:
        """Create toggle switches for each button."""
        switch_width = self.config.get_scaled_int(60)
        switch_height = self.config.get_scaled_int(25)
        
        start_y = self.y + self.config.get_scaled_int(80)
        row_height = self.config.get_scaled_int(45)
        
        for i in range(1, 11):
            switch_x = self.x + self.width - switch_width - self.config.get_scaled_int(30)
            switch_y = start_y + (i - 1) * row_height
            
            self.toggle_switches[i] = ToggleSwitch(
                switch_x, switch_y, switch_width, switch_height, 
                self.button_modes[i]
            )
    
    def show(self) -> None:
        """Show the dialog."""
        self.is_visible = True
    
    def hide(self) -> None:
        """Hide the dialog."""
        self.is_visible = False
        self._save_settings()
    
    def _save_settings(self) -> None:
        """Save button settings to configuration."""
        for button_id, switch in self.toggle_switches.items():
            self.button_modes[button_id] = switch.state
            self.config.set(f"buttons.button_{button_id}.toggle_mode", switch.state)
        
        self.config.save_config()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle events for the dialog.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled, False otherwise
        """
        if not self.is_visible:
            return False
        
        # Handle close button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_button.collidepoint(event.pos):
                self.hide()
                return True
        
        # Handle toggle switches
        for switch in self.toggle_switches.values():
            if switch.handle_event(event):
                return True
        
        # Consume all events when dialog is visible
        return True
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the dialog.
        
        Args:
            surface: Surface to draw on
        """
        if not self.is_visible:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Draw dialog background
        dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (40, 40, 40), dialog_rect)
        pygame.draw.rect(surface, (100, 150, 255), dialog_rect, 2)
        
        # Draw title
        title_text = self.title_font.render("Button Settings", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=self.x + self.width // 2, y=self.y + self.config.get_scaled_int(15))
        surface.blit(title_text, title_rect)
        
        # Draw close button
        pygame.draw.rect(surface, (150, 50, 50), self.close_button)
        pygame.draw.rect(surface, (200, 200, 200), self.close_button, 2)
        close_text = self.small_font.render("×", True, (255, 255, 255))
        close_rect = close_text.get_rect(center=self.close_button.center)
        surface.blit(close_text, close_rect)
        
        # Draw column headers
        header_y = self.y + self.config.get_scaled_int(55)
        button_header = self.font.render("Button", True, (200, 200, 200))
        mode_header = self.font.render("Mode", True, (200, 200, 200))
        toggle_header = self.font.render("Toggle", True, (200, 200, 200))
        
        surface.blit(button_header, (self.x + self.config.get_scaled_int(20), header_y))
        surface.blit(mode_header, (self.x + self.config.get_scaled_int(150), header_y))
        surface.blit(toggle_header, (self.x + self.width - self.config.get_scaled_int(100), header_y))
        
        # Draw button list and toggle switches
        start_y = self.y + self.config.get_scaled_int(80)
        row_height = self.config.get_scaled_int(45)
        
        button_names = {
            1: "Button 1", 2: "Button 2", 3: "Button 3", 4: "Button 4",
            5: "Button 5", 6: "Button 6", 7: "Button 7", 8: "Button 8",
            9: "ARM", 10: "RTH"
        }
        
        for i in range(1, 11):
            row_y = start_y + (i - 1) * row_height
            
            # Draw button name
            button_text = self.font.render(button_names[i], True, (255, 255, 255))
            surface.blit(button_text, (self.x + self.config.get_scaled_int(20), row_y + self.config.get_scaled_int(5)))
            
            # Draw current mode
            mode_text = "Toggle" if self.toggle_switches[i].state else "Momentary"
            mode_color = (0, 255, 0) if self.toggle_switches[i].state else (255, 150, 150)  # Bright green for toggle, light red for momentary
            mode_surface = self.font.render(mode_text, True, mode_color)
            surface.blit(mode_surface, (self.x + self.config.get_scaled_int(150), row_y + self.config.get_scaled_int(5)))
            
            # Draw toggle switch
            self.toggle_switches[i].draw(surface)
        
        # Draw instructions
        instructions = [
            "Momentary: Button is active only while pressed",
            "Toggle: Button stays active until pressed again"
        ]
        
        instruction_y = start_y + 10 * row_height + self.config.get_scaled_int(20)
        for i, instruction in enumerate(instructions):
            text_surface = self.small_font.render(instruction, True, (180, 180, 180))
            surface.blit(text_surface, (self.x + self.config.get_scaled_int(20), instruction_y + i * self.config.get_scaled_int(20)))
    
    def get_button_mode(self, button_id: int) -> bool:
        """
        Get the toggle mode for a specific button.
        
        Args:
            button_id: Button ID (1-10)
            
        Returns:
            True if toggle mode, False if momentary mode
        """
        return self.button_modes.get(button_id, False)
