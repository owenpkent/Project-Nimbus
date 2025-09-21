"""
Configuration module for the virtual controller.
Handles sensitivity curves, dead zones, and other controller parameters.
"""

import json
import os
from typing import Dict, Any, Tuple
import numpy as np


class ControllerConfig:
    """
    Manages configuration settings for the virtual controller.
    
    This class handles loading, saving, and applying configuration settings
    including sensitivity curves, dead zones, and UI parameters.
    """
    
    def __init__(self, config_file: str = "controller_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """
        Load default configuration settings.
        
        Returns:
            Dictionary containing default configuration
        """
        return {
            "joysticks": {
                "left": {
                    "dead_zone": 0.1,
                    "sensitivity": 1.0,
                    "curve_type": "linear",  # linear, exponential, logarithmic
                    "curve_power": 2.0,
                    "invert_x": False,
                    "invert_y": False,
                    "max_range": 1.0
                },
                "right": {
                    "dead_zone": 0.1,
                    "sensitivity": 1.0,
                    "curve_type": "linear",
                    "curve_power": 2.0,
                    "invert_x": False,
                    "invert_y": False,
                    "max_range": 1.0
                }
            },
            "ui": {
                "window_width": 614,
                "window_height": 311,
                "joystick_size": 280,
                "background_color": (20, 20, 20),
                "joystick_bg_color": (80, 20, 20),
                "joystick_fg_color": (255, 50, 50),
                "button_color": (60, 15, 15),
                "button_hover_color": (100, 25, 25),
                "text_color": (255, 255, 255),
                "font_size": 14,
                "scale_factor": 1.0
            },
            "vjoy": {
                "device_id": 1,
                "update_rate": 60,  # Hz
                "axis_range": 32767  # VJoy axis range
            },
            "axis_mapping": {
                "left_x": "x",      # Left joystick X -> VJoy X axis
                "left_y": "y",      # Left joystick Y -> VJoy Y axis
                "right_x": "rx",    # Right joystick X -> VJoy RX axis
                "right_y": "ry"     # Right joystick Y -> VJoy RY axis
            },
            "safety": {
                "enable_failsafe": True,
                "failsafe_timeout": 5.0,  # seconds
                "max_update_rate": 100,  # Hz
                "enable_smoothing": True,
                "smoothing_factor": 0.1
            }
        }
    
    def load_config(self) -> None:
        """Load configuration from file if it exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self._merge_config(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                print("Using default configuration.")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config file: {e}")
    
    def _merge_config(self, loaded_config: Dict[str, Any]) -> None:
        """
        Merge loaded configuration with defaults.
        
        Args:
            loaded_config: Configuration loaded from file
        """
        def merge_dict(default: Dict, loaded: Dict) -> Dict:
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        self.config = merge_dict(self.config, loaded_config)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Path to the configuration key (e.g., "joysticks.left.dead_zone")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Path to the configuration key
            value: Value to set
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        config_ref[keys[-1]] = value
    
    def apply_sensitivity_curve(self, value: float, joystick: str, axis: str) -> float:
        """
        Apply sensitivity curve to input value.
        
        Args:
            value: Raw input value (-1.0 to 1.0)
            joystick: Joystick identifier ("left" or "right")
            axis: Axis identifier ("x" or "y")
            
        Returns:
            Processed value with sensitivity curve applied
        """
        if abs(value) < self.get(f"joysticks.{joystick}.dead_zone", 0.1):
            return 0.0
        
        # Remove dead zone
        sign = 1 if value >= 0 else -1
        abs_value = abs(value)
        dead_zone = self.get(f"joysticks.{joystick}.dead_zone", 0.1)
        
        # Scale to remove dead zone
        if abs_value > dead_zone:
            scaled_value = (abs_value - dead_zone) / (1.0 - dead_zone)
        else:
            return 0.0
        
        # Apply sensitivity curve
        curve_type = self.get(f"joysticks.{joystick}.curve_type", "linear")
        curve_power = self.get(f"joysticks.{joystick}.curve_power", 2.0)
        
        if curve_type == "exponential":
            processed_value = np.power(scaled_value, curve_power)
        elif curve_type == "logarithmic":
            processed_value = np.log(1 + scaled_value * (np.e - 1)) / np.log(np.e)
        else:  # linear
            processed_value = scaled_value
        
        # Apply sensitivity multiplier
        sensitivity = self.get(f"joysticks.{joystick}.sensitivity", 1.0)
        processed_value *= sensitivity
        
        # Apply inversion if needed
        invert_key = f"joysticks.{joystick}.invert_{axis}"
        if self.get(invert_key, False):
            sign *= -1
        
        # Clamp to max range
        max_range = self.get(f"joysticks.{joystick}.max_range", 1.0)
        processed_value = min(processed_value, max_range)
        
        return sign * processed_value
    
    def get_vjoy_value(self, normalized_value: float) -> int:
        """
        Convert normalized value (-1.0 to 1.0) to VJoy axis value.
        
        Args:
            normalized_value: Normalized input value
            
        Returns:
            VJoy axis value
        """
        axis_range = self.get("vjoy.axis_range", 32767)
        return int((normalized_value + 1.0) * axis_range / 2.0)
    
    def get_scaled_value(self, base_value: float) -> float:
        """
        Get scaled value based on current UI scale factor.
        
        Args:
            base_value: Base value to scale
            
        Returns:
            Scaled value
        """
        scale_factor = self.get("ui.scale_factor", 1.0)
        return base_value * scale_factor
    
    def get_scaled_int(self, base_value: int) -> int:
        """
        Get scaled integer value based on current UI scale factor.
        
        Args:
            base_value: Base integer value to scale
            
        Returns:
            Scaled integer value
        """
        return int(self.get_scaled_value(float(base_value)))
    
    def set_scale_factor(self, scale_factor: float) -> None:
        """
        Set UI scale factor and update related UI values.
        
        Args:
            scale_factor: New scale factor (0.5 to 2.0)
        """
        # Clamp scale factor to reasonable range
        scale_factor = max(0.5, min(2.0, scale_factor))
        self.set("ui.scale_factor", scale_factor)
        
        # Update scaled window dimensions using a custom compact resolution.
        base_width = 614
        base_height = 311
        width = int(base_width * scale_factor)
        height = int(base_height * scale_factor)
        self.set("ui.window_width", width)
        self.set("ui.window_height", height)
        
        # Update scaled joystick size
        base_joystick_size = 280
        self.set("ui.joystick_size", int(base_joystick_size * scale_factor))
        
        # Update scaled font size
        base_font_size = 16
        self.set("ui.font_size", int(base_font_size * scale_factor))

    def validate_config(self) -> Tuple[bool, str]:
        """
        Validate current configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required sections
            required_sections = ["joysticks", "ui", "vjoy", "safety"]
            for section in required_sections:
                if section not in self.config:
                    return False, f"Missing required section: {section}"
            
            # Validate joystick configurations
            for joystick in ["left", "right"]:
                if joystick not in self.config["joysticks"]:
                    return False, f"Missing joystick configuration: {joystick}"
                
                # Check dead zone range
                dead_zone = self.get(f"joysticks.{joystick}.dead_zone", 0.1)
                if not 0.0 <= dead_zone <= 0.5:
                    return False, f"Invalid dead zone for {joystick}: {dead_zone}"
                
                # Check sensitivity range
                sensitivity = self.get(f"joysticks.{joystick}.sensitivity", 1.0)
                if not 0.1 <= sensitivity <= 5.0:
                    return False, f"Invalid sensitivity for {joystick}: {sensitivity}"
            
            # Validate VJoy settings
            device_id = self.get("vjoy.device_id", 1)
            if not 1 <= device_id <= 16:
                return False, f"Invalid VJoy device ID: {device_id}"
            
            # Validate scale factor
            scale_factor = self.get("ui.scale_factor", 1.0)
            if not 0.5 <= scale_factor <= 2.0:
                return False, f"Invalid scale factor: {scale_factor}"
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"
