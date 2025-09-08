"""
Virtual joystick implementation for the controller interface.
Handles mouse input, position tracking, and visual representation.
"""

import pygame
import math
from typing import Tuple, Optional, Callable
from config import ControllerConfig


class VirtualJoystick:
    """
    A virtual joystick that can be controlled with mouse input.
    
    This class handles the visual representation and input processing
    for a virtual joystick control, including dead zones and sensitivity curves.
    """
    
    def __init__(self, center_x: int, center_y: int, radius: int, 
                 config: ControllerConfig, joystick_id: str):
        """
        Initialize the virtual joystick.
        
        Args:
            center_x: X coordinate of joystick center
            center_y: Y coordinate of joystick center
            radius: Radius of the joystick area
            config: Configuration manager instance
            joystick_id: Identifier for this joystick ("left" or "right")
        """
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.config = config
        self.joystick_id = joystick_id
        
        # Current position (normalized -1.0 to 1.0)
        self.x_pos = 0.0
        self.y_pos = 0.0
        
        # Raw position (before sensitivity curves)
        self.raw_x = 0.0
        self.raw_y = 0.0
        
        # Lock states for axes
        self.x_locked = False
        self.y_locked = False
        
        # Mouse interaction state
        self.is_dragging = False
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        # Smoothing for stability
        self.prev_x = 0.0
        self.prev_y = 0.0
        
        # Callbacks for value changes
        self.on_value_changed: Optional[Callable[[float, float], None]] = None
    
    def handle_mouse_down(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle mouse button down event.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if the joystick handled the event
        """
        mouse_x, mouse_y = mouse_pos
        distance = math.sqrt((mouse_x - self.center_x) ** 2 + (mouse_y - self.center_y) ** 2)
        
        if distance <= self.radius:
            self.is_dragging = True
            # Calculate offset from center to mouse for smooth dragging
            self.mouse_offset_x = mouse_x - self.center_x
            self.mouse_offset_y = mouse_y - self.center_y
            self._update_position_from_offset()
            return True
        
        return False
    
    def handle_mouse_up(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Handle mouse button up event.
        
        Args:
            mouse_pos: Mouse position (x, y)
        """
        if self.is_dragging:
            self.is_dragging = False
            # Don't auto-center - let the user control when to reset
    
    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Handle mouse motion event.
        
        Args:
            mouse_pos: Mouse position (x, y)
        """
        if self.is_dragging:
            mouse_x, mouse_y = mouse_pos
            self.mouse_offset_x = mouse_x - self.center_x
            self.mouse_offset_y = mouse_y - self.center_y
            self._update_position_from_offset()
    
    def _update_position_from_offset(self) -> None:
        """Update joystick position based on mouse offset."""
        # Limit to joystick radius
        distance = math.sqrt(self.mouse_offset_x ** 2 + self.mouse_offset_y ** 2)
        
        if distance > self.radius:
            # Normalize to radius
            self.mouse_offset_x = (self.mouse_offset_x / distance) * self.radius
            self.mouse_offset_y = (self.mouse_offset_y / distance) * self.radius
        
        # Convert to normalized coordinates (-1.0 to 1.0)
        new_raw_x = self.mouse_offset_x / self.radius
        new_raw_y = -self.mouse_offset_y / self.radius  # Invert Y for standard coordinate system
        
        # Apply locks
        if not self.x_locked:
            self.raw_x = new_raw_x
        if not self.y_locked:
            self.raw_y = new_raw_y
        
        # Apply sensitivity curves and smoothing
        self._apply_processing()
    
    def _apply_processing(self) -> None:
        """Apply sensitivity curves, dead zones, and smoothing."""
        # Apply sensitivity curves
        processed_x = self.config.apply_sensitivity_curve(self.raw_x, self.joystick_id, "x")
        processed_y = self.config.apply_sensitivity_curve(self.raw_y, self.joystick_id, "y")
        
        # Apply smoothing if enabled
        if self.config.get("safety.enable_smoothing", True):
            smoothing_factor = self.config.get("safety.smoothing_factor", 0.1)
            processed_x = self.prev_x + (processed_x - self.prev_x) * smoothing_factor
            processed_y = self.prev_y + (processed_y - self.prev_y) * smoothing_factor
        
        # Update positions
        old_x, old_y = self.x_pos, self.y_pos
        self.x_pos = processed_x
        self.y_pos = processed_y
        self.prev_x = processed_x
        self.prev_y = processed_y
        
        # Trigger callback if values changed significantly
        if (abs(self.x_pos - old_x) > 0.001 or abs(self.y_pos - old_y) > 0.001) and self.on_value_changed:
            self.on_value_changed(self.x_pos, self.y_pos)
    
    def set_position(self, x: float, y: float) -> None:
        """
        Set joystick position programmatically.
        
        Args:
            x: X position (-1.0 to 1.0)
            y: Y position (-1.0 to 1.0)
        """
        if not self.x_locked:
            self.raw_x = max(-1.0, min(1.0, x))
        if not self.y_locked:
            self.raw_y = max(-1.0, min(1.0, y))
        
        self._apply_processing()
    
    def center(self) -> None:
        """Center the joystick position."""
        if not self.x_locked:
            self.raw_x = 0.0
        if not self.y_locked:
            self.raw_y = 0.0
        
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        self._apply_processing()
    
    def lock_axis(self, axis: str, locked: bool) -> None:
        """
        Lock or unlock an axis.
        
        Args:
            axis: Axis to lock ("x" or "y")
            locked: Whether to lock the axis
        """
        if axis.lower() == "x":
            self.x_locked = locked
            if locked:
                self.raw_x = 0.0
        elif axis.lower() == "y":
            self.y_locked = locked
            if locked:
                self.raw_y = 0.0
        
        self._apply_processing()
    
    def get_position(self) -> Tuple[float, float]:
        """
        Get current processed joystick position.
        
        Returns:
            Tuple of (x, y) positions (-1.0 to 1.0)
        """
        return self.x_pos, self.y_pos
    
    def get_raw_position(self) -> Tuple[float, float]:
        """
        Get current raw joystick position (before processing).
        
        Returns:
            Tuple of (x, y) raw positions (-1.0 to 1.0)
        """
        return self.raw_x, self.raw_y
    
    def get_display_position(self) -> Tuple[int, int]:
        """
        Get position for display purposes.
        
        Returns:
            Tuple of (x, y) pixel coordinates for drawing
        """
        display_x = self.center_x + int(self.raw_x * self.radius)
        display_y = self.center_y - int(self.raw_y * self.radius)  # Invert Y for display
        return display_x, display_y
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the joystick on the given surface.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Get colors from config
        bg_color = self.config.get("ui.joystick_bg_color", (80, 20, 20))
        fg_color = self.config.get("ui.joystick_fg_color", (255, 50, 50))
        
        # Draw outer circle (background)
        pygame.draw.circle(surface, bg_color, (self.center_x, self.center_y), self.radius, 3)
        
        # Draw dead zone indicator
        dead_zone = self.config.get(f"joysticks.{self.joystick_id}.dead_zone", 0.1)
        dead_zone_radius = int(self.radius * dead_zone)
        if dead_zone_radius > 0:
            dead_zone_color = (bg_color[0] // 2, bg_color[1] // 2, bg_color[2] // 2)
            pygame.draw.circle(surface, dead_zone_color, (self.center_x, self.center_y), dead_zone_radius, 1)
        
        # Draw center cross
        cross_size = 10
        pygame.draw.line(surface, (100, 100, 100), 
                        (self.center_x - cross_size, self.center_y),
                        (self.center_x + cross_size, self.center_y), 1)
        pygame.draw.line(surface, (100, 100, 100),
                        (self.center_x, self.center_y - cross_size),
                        (self.center_x, self.center_y + cross_size), 1)
        
        # Draw joystick position
        display_x, display_y = self.get_display_position()
        
        # Draw connection line
        if self.raw_x != 0 or self.raw_y != 0:
            pygame.draw.line(surface, (fg_color[0] // 2, fg_color[1] // 2, fg_color[2] // 2),
                           (self.center_x, self.center_y), (display_x, display_y), 2)
        
        # Draw joystick knob
        knob_radius = 8
        pygame.draw.circle(surface, fg_color, (display_x, display_y), knob_radius)
        pygame.draw.circle(surface, (255, 255, 255), (display_x, display_y), knob_radius, 2)
        
        # Draw lock indicators
        if self.x_locked:
            lock_color = (255, 255, 0)
            pygame.draw.line(surface, lock_color,
                           (self.center_x - self.radius - 10, self.center_y),
                           (self.center_x + self.radius + 10, self.center_y), 3)
        
        if self.y_locked:
            lock_color = (255, 255, 0)
            pygame.draw.line(surface, lock_color,
                           (self.center_x, self.center_y - self.radius - 10),
                           (self.center_x, self.center_y + self.radius + 10), 3)
    
    def is_point_inside(self, point: Tuple[int, int]) -> bool:
        """
        Check if a point is inside the joystick area.
        
        Args:
            point: Point to check (x, y)
            
        Returns:
            True if point is inside joystick area
        """
        x, y = point
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return distance <= self.radius
