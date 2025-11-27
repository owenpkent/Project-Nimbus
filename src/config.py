"""
Configuration module for the virtual controller.
Handles sensitivity curves, dead zones, and other controller parameters.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import numpy as np

# App name for user data directory
APP_NAME = "ProjectNimbus"


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
        
        # Profile system - set up directories
        self._bundled_profiles_dir = self._get_bundled_profiles_dir()
        self._user_data_dir = self._get_user_data_dir()
        self._user_profiles_dir = self._user_data_dir / "profiles"
        
        # Ensure user profiles directory exists and has default profiles
        self._ensure_user_profiles()
        
        self._current_profile: Optional[str] = self.config.get("current_profile", "flight_simulator")
    
    @staticmethod
    def _get_user_data_dir() -> Path:
        """
        Get the user data directory for storing profiles and settings.
        
        Returns:
            Path to user data directory (e.g., %APPDATA%/ProjectNimbus on Windows)
        """
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        
        return base / APP_NAME
    
    def _get_bundled_profiles_dir(self) -> Path:
        """
        Get the directory containing bundled default profiles.
        
        Handles both development mode and PyInstaller frozen mode.
        
        Returns:
            Path to bundled profiles directory
        """
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running in development
            base_path = Path(__file__).resolve().parent.parent
        
        return base_path / "profiles"
    
    def _ensure_user_profiles(self) -> None:
        """
        Ensure user profiles directory exists and contains default profiles.
        
        Copies bundled profiles to user directory if they don't exist.
        """
        # Create user profiles directory
        self._user_profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy bundled profiles if they don't exist in user directory
        if self._bundled_profiles_dir.exists():
            for profile_file in self._bundled_profiles_dir.glob("*.json"):
                user_profile_path = self._user_profiles_dir / profile_file.name
                if not user_profile_path.exists():
                    shutil.copy2(profile_file, user_profile_path)
    
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
                "joystick_size": 336,
                "background_color": (20, 20, 20),
                "joystick_bg_color": (80, 20, 20),
                "joystick_fg_color": (255, 50, 50),
                "button_color": (60, 15, 15),
                "button_hover_color": (100, 25, 25),
                "text_color": (255, 255, 255),
                "font_size": 14,
                "scale_factor": 1.0,
                "debug_borders": False
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
                "right_y": "ry",    # Right joystick Y -> VJoy RY axis
                "throttle": "z",    # Throttle -> VJoy Z axis (default)
                "rudder": "rz"      # Rudder -> VJoy RZ axis (default)
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
        # If the new dialog-based settings exist, prefer them for QML path so
        # runtime behavior matches the Joystick Settings preview exactly.
        try:
            if self.get("joystick_settings.sensitivity", None) is not None:
                return self.apply_joystick_dialog_curve(value)
        except Exception:
            pass
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

    def apply_joystick_dialog_curve(self, value: float) -> float:
        """
        Apply curve using percent-based settings from the Joystick Settings dialog.

        Matches the math in qt_dialogs._CurvePreview._calc_output so the live
        preview and runtime feel identical.
        """
        try:
            sensitivity_pct = float(self.get("joystick_settings.sensitivity", 50.0))
            deadzone_pct = float(self.get("joystick_settings.deadzone", 10.0))
            extremity_pct = float(self.get("joystick_settings.extremity_deadzone", 5.0))

            # Convert percentages to the preview's internal units
            deadzone = (deadzone_pct / 100.0) * 0.25
            extremity_deadzone = extremity_pct / 100.0
            sensitivity = sensitivity_pct / 100.0

            v = float(value)
            if abs(v) < deadzone:
                return 0.0

            sign = 1.0 if v >= 0 else -1.0
            abs_input = abs(v)
            available_range = 1.0 - deadzone
            normalized_input = (abs_input - deadzone) / max(1e-6, available_range)

            if abs(sensitivity - 0.5) < 1e-9:
                output = normalized_input
            elif sensitivity < 0.5:
                power = 1.0 + (0.5 - sensitivity) * 6.0
                output = float(np.power(normalized_input, power))
            else:
                power = 1.0 - (sensitivity - 0.5) * 1.8
                output = float(np.power(normalized_input, max(0.1, power)))

            if extremity_deadzone > 0:
                max_output = 1.0 - extremity_deadzone
                output *= max_output

            return output * sign
        except Exception:
            # Fallback to identity on any error
            return float(value)

    def apply_rudder_sensitivity_curve(self, value: float) -> float:
        """
        Apply curve using percent-based settings from the Rudder Settings dialog.
        Mirrors apply_joystick_dialog_curve but reads rudder_settings.* keys.
        """
        try:
            sensitivity_pct = float(self.get("rudder_settings.sensitivity", 50.0))
            deadzone_pct = float(self.get("rudder_settings.deadzone", 10.0))
            extremity_pct = float(self.get("rudder_settings.extremity_deadzone", 5.0))

            deadzone = (deadzone_pct / 100.0) * 0.25
            extremity_deadzone = extremity_pct / 100.0
            sensitivity = sensitivity_pct / 100.0

            v = float(value)
            if abs(v) < deadzone:
                return 0.0

            sign = 1.0 if v >= 0 else -1.0
            abs_input = abs(v)
            available_range = 1.0 - deadzone
            normalized_input = (abs_input - deadzone) / max(1e-6, available_range)

            if abs(sensitivity - 0.5) < 1e-9:
                output = normalized_input
            elif sensitivity < 0.5:
                power = 1.0 + (0.5 - sensitivity) * 6.0
                output = float(np.power(normalized_input, power))
            else:
                power = 1.0 - (sensitivity - 0.5) * 1.8
                output = float(np.power(normalized_input, max(0.1, power)))

            if extremity_deadzone > 0:
                max_output = 1.0 - extremity_deadzone
                output *= max_output

            return output * sign
        except Exception:
            return float(value)
    
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
        
        # Update scaled joystick size (20% larger base)
        base_joystick_size = 336
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

    # -------------------------------------------------------------------------
    # Profile System
    # -------------------------------------------------------------------------

    def get_available_profiles(self) -> List[Dict[str, str]]:
        """
        Get list of available profiles from the user profiles directory.
        
        Returns:
            List of dicts with 'id', 'name', 'description', 'layout_type', 'is_builtin' keys
        """
        profiles = []
        if not self._user_profiles_dir.exists():
            return profiles
        
        # Get list of built-in profile IDs
        builtin_ids = set()
        if self._bundled_profiles_dir.exists():
            builtin_ids = {f.stem for f in self._bundled_profiles_dir.glob("*.json")}
        
        for profile_file in self._user_profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profiles.append({
                        "id": profile_file.stem,
                        "name": data.get("name", profile_file.stem),
                        "description": data.get("description", ""),
                        "layout_type": data.get("layout_type", "flight_sim"),
                        "is_builtin": profile_file.stem in builtin_ids
                    })
            except (json.JSONDecodeError, IOError):
                continue
        
        return profiles

    def get_current_profile(self) -> str:
        """Get the current profile ID."""
        return self._current_profile or "flight_simulator"

    def get_current_profile_data(self) -> Optional[Dict[str, Any]]:
        """Load and return the current profile's full data."""
        return self.load_profile(self.get_current_profile())

    def load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a profile by ID from user profiles directory.
        
        Args:
            profile_id: Profile identifier (filename without .json)
            
        Returns:
            Profile data dict or None if not found
        """
        profile_path = self._user_profiles_dir / f"{profile_id}.json"
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def switch_profile(self, profile_id: str) -> bool:
        """
        Switch to a different profile.
        
        Args:
            profile_id: Profile identifier to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        profile_data = self.load_profile(profile_id)
        if profile_data is None:
            return False
        
        # Update current profile
        self._current_profile = profile_id
        self.set("current_profile", profile_id)
        
        # Apply profile settings to config
        self._apply_profile_settings(profile_data)
        
        # Save config
        self.save_config()
        return True

    def _apply_profile_settings(self, profile_data: Dict[str, Any]) -> None:
        """
        Apply profile settings to the current configuration.
        
        Args:
            profile_data: Profile data dictionary
        """
        # Apply axis mapping
        if "axis_mapping" in profile_data:
            for key, value in profile_data["axis_mapping"].items():
                self.set(f"axis_mapping.{key}", value)
        
        # Apply button settings (preserve toggle_mode from profile)
        if "buttons" in profile_data:
            for btn_key, btn_data in profile_data["buttons"].items():
                if isinstance(btn_data, dict):
                    for setting_key, setting_value in btn_data.items():
                        self.set(f"buttons.{btn_key}.{setting_key}", setting_value)
        
        # Apply joystick settings
        if "joystick_settings" in profile_data:
            for key, value in profile_data["joystick_settings"].items():
                self.set(f"joystick_settings.{key}", value)
        
        # Apply rudder settings
        if "rudder_settings" in profile_data:
            for key, value in profile_data["rudder_settings"].items():
                self.set(f"rudder_settings.{key}", value)

    def get_button_label(self, button_id: int) -> str:
        """
        Get the label for a button based on current profile.
        
        Args:
            button_id: Button number (1-based)
            
        Returns:
            Button label string
        """
        profile_data = self.get_current_profile_data()
        if profile_data and "buttons" in profile_data:
            btn_key = f"button_{button_id}"
            btn_data = profile_data["buttons"].get(btn_key, {})
            if isinstance(btn_data, dict):
                return btn_data.get("label", str(button_id))
        return str(button_id)

    def get_layout_type(self) -> str:
        """Get the layout type of the current profile."""
        profile_data = self.get_current_profile_data()
        if profile_data:
            return profile_data.get("layout_type", "flight_sim")
        return "flight_sim"

    def save_current_profile(self) -> bool:
        """
        Save current settings to the active profile.
        
        Updates the user's profile file with current joystick/rudder settings,
        button configurations, and axis mappings.
        
        Returns:
            True if save was successful, False otherwise
        """
        profile_id = self.get_current_profile()
        profile_path = self._user_profiles_dir / f"{profile_id}.json"
        
        # Load existing profile data to preserve structure
        profile_data = self.load_profile(profile_id)
        if profile_data is None:
            return False
        
        # Update with current settings
        profile_data["joystick_settings"] = {
            "sensitivity": self.get("joystick_settings.sensitivity", 35.0),
            "deadzone": self.get("joystick_settings.deadzone", 0.0),
            "extremity_deadzone": self.get("joystick_settings.extremity_deadzone", 38.0),
        }
        
        profile_data["rudder_settings"] = {
            "sensitivity": self.get("rudder_settings.sensitivity", 50.0),
            "deadzone": self.get("rudder_settings.deadzone", 10.0),
            "extremity_deadzone": self.get("rudder_settings.extremity_deadzone", 5.0),
        }
        
        # Update button toggle modes
        if "buttons" in profile_data:
            for btn_key in profile_data["buttons"]:
                toggle_mode = self.get(f"buttons.{btn_key}.toggle_mode", False)
                if isinstance(profile_data["buttons"][btn_key], dict):
                    profile_data["buttons"][btn_key]["toggle_mode"] = toggle_mode
        
        # Update axis mapping
        if "axis_mapping" in profile_data:
            for axis_key in profile_data["axis_mapping"]:
                value = self.get(f"axis_mapping.{axis_key}")
                if value is not None:
                    profile_data["axis_mapping"][axis_key] = value
        
        # Save to file
        try:
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=4)
            return True
        except IOError:
            return False

    def reset_profile(self, profile_id: str) -> bool:
        """
        Reset a profile to its default (bundled) settings.
        
        Only works for built-in profiles that have a bundled version.
        
        Args:
            profile_id: Profile identifier to reset
            
        Returns:
            True if reset was successful, False otherwise
        """
        bundled_path = self._bundled_profiles_dir / f"{profile_id}.json"
        user_path = self._user_profiles_dir / f"{profile_id}.json"
        
        if not bundled_path.exists():
            return False  # Can't reset non-built-in profiles
        
        try:
            shutil.copy2(bundled_path, user_path)
            
            # If this is the current profile, reload settings
            if profile_id == self._current_profile:
                profile_data = self.load_profile(profile_id)
                if profile_data:
                    self._apply_profile_settings(profile_data)
                    self.save_config()
            
            return True
        except IOError:
            return False

    def duplicate_profile(self, source_id: str, new_name: str) -> Optional[str]:
        """
        Create a copy of an existing profile with a new name.
        
        Args:
            source_id: Profile ID to copy from
            new_name: Display name for the new profile
            
        Returns:
            New profile ID if successful, None otherwise
        """
        source_data = self.load_profile(source_id)
        if source_data is None:
            return None
        
        # Generate new ID from name
        new_id = new_name.lower().replace(" ", "_")
        new_id = "".join(c for c in new_id if c.isalnum() or c == "_")
        
        # Ensure unique ID
        base_id = new_id
        counter = 1
        while (self._user_profiles_dir / f"{new_id}.json").exists():
            new_id = f"{base_id}_{counter}"
            counter += 1
        
        # Create new profile
        new_data = source_data.copy()
        new_data["name"] = new_name
        new_data["description"] = f"Custom profile based on {source_data.get('name', source_id)}"
        
        new_path = self._user_profiles_dir / f"{new_id}.json"
        try:
            with open(new_path, 'w') as f:
                json.dump(new_data, f, indent=4)
            return new_id
        except IOError:
            return None

    def create_profile_as(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new profile from current settings with a custom name and description.
        
        Args:
            name: Display name for the new profile
            description: Optional description for the profile
            
        Returns:
            New profile ID if successful, None otherwise
        """
        # Start from current profile as template
        current_data = self.get_current_profile_data()
        if current_data is None:
            current_data = {}
        
        # Generate new ID from name
        new_id = name.lower().replace(" ", "_")
        new_id = "".join(c for c in new_id if c.isalnum() or c == "_")
        
        if not new_id:
            new_id = "custom_profile"
        
        # Ensure unique ID
        base_id = new_id
        counter = 1
        while (self._user_profiles_dir / f"{new_id}.json").exists():
            new_id = f"{base_id}_{counter}"
            counter += 1
        
        # Build new profile data with current settings
        new_data = {
            "name": name,
            "description": description if description else f"Custom profile created from {current_data.get('name', 'settings')}",
            "layout_type": current_data.get("layout_type", "flight_sim"),
            "axis_mapping": {},
            "buttons": current_data.get("buttons", {}),
            "joystick_settings": {
                "sensitivity": self.get("joystick_settings.sensitivity", 35.0),
                "deadzone": self.get("joystick_settings.deadzone", 0.0),
                "extremity_deadzone": self.get("joystick_settings.extremity_deadzone", 38.0),
            },
            "rudder_settings": {
                "sensitivity": self.get("rudder_settings.sensitivity", 50.0),
                "deadzone": self.get("rudder_settings.deadzone", 10.0),
                "extremity_deadzone": self.get("rudder_settings.extremity_deadzone", 5.0),
            }
        }
        
        # Copy axis mapping from config
        for axis in ["left_x", "left_y", "right_x", "right_y", "throttle", "rudder"]:
            value = self.get(f"axis_mapping.{axis}")
            if value:
                new_data["axis_mapping"][axis] = value
        
        # Update button toggle modes from current settings
        if "buttons" in new_data:
            for btn_key in new_data["buttons"]:
                if isinstance(new_data["buttons"][btn_key], dict):
                    toggle_mode = self.get(f"buttons.{btn_key}.toggle_mode", False)
                    new_data["buttons"][btn_key]["toggle_mode"] = toggle_mode
        
        new_path = self._user_profiles_dir / f"{new_id}.json"
        try:
            with open(new_path, 'w') as f:
                json.dump(new_data, f, indent=4)
            return new_id
        except IOError:
            return None

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a user-created profile.
        
        Cannot delete built-in profiles.
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            True if deleted, False if not allowed or failed
        """
        # Check if it's a built-in profile
        bundled_path = self._bundled_profiles_dir / f"{profile_id}.json"
        if bundled_path.exists():
            return False  # Can't delete built-in profiles
        
        user_path = self._user_profiles_dir / f"{profile_id}.json"
        if not user_path.exists():
            return False
        
        try:
            user_path.unlink()
            
            # If we deleted the current profile, switch to default
            if profile_id == self._current_profile:
                self.switch_profile("flight_simulator")
            
            return True
        except IOError:
            return False

    def is_builtin_profile(self, profile_id: str) -> bool:
        """Check if a profile is a built-in (bundled) profile."""
        bundled_path = self._bundled_profiles_dir / f"{profile_id}.json"
        return bundled_path.exists()

    def get_user_profiles_path(self) -> str:
        """Get the path to the user profiles directory."""
        return str(self._user_profiles_dir)
