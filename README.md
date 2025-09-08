# Project Nimbus

Project Nimbus is a Python project that bridges mouse and keyboard inputs (via Pygame) to vJoy, creating a software-defined virtual joystick.

It is designed with accessibility in mind, offering a practical solution for individuals with mobility limitations who may not be able to use traditional physical controllers. By providing a mouse-first input model, it enables users to interact with systems that expect joystick input.

At the same time, Project Nimbus is versatile enough for anyone interested in alternative control schemes. Whether for adaptive gaming or connecting to Mission Planner for UAV and rover control, Nimbus makes joystick input more flexible and inclusive.

## Features

### Core Functionality
- **Virtual joystick output** using the vJoy driver
- **Mouse-first interface** for generating joystick inputs with dual joystick layout
- **Real-time Control**: Low-latency input processing suitable for UAV and rover control
- **Safety Systems**: Built-in failsafe mechanisms and emergency stop functionality
- **Mission Planner Compatible**: Direct integration with MAVLink-compatible ground control software

### Advanced Configuration
- **Sensitivity Curves**: Linear, exponential, and logarithmic response curves
- **Dead Zone Control**: Configurable dead zones for each joystick
- **Axis Locking**: Individual X/Y axis lock functionality for precise control
- **Input Smoothing**: Optional smoothing for stability in critical applications
- **Rate Limiting**: Configurable update rates with safety limits

### User Interface
- **Accessibility-First Design**: Clean, high-contrast interface optimized for various input methods
- **Visual Feedback**: Real-time position indicators and comprehensive status display
- **Lock Indicators**: Clear visual feedback for locked axes
- **Debug Mode**: Comprehensive system information (F1 to toggle)

## Accessibility

The project was built with an accessibility-first philosophy. Instead of assuming users can handle conventional joysticks or gamepads, Nimbus allows mouse-driven or alternative inputs to control any software or hardware that supports vJoy.

This makes it especially valuable for:
- **Users with mobility impairments** who rely on mouse or adaptive devices
- **Developers creating assistive technology** solutions
- **Hobbyists and researchers** exploring human-computer interaction through unconventional inputs
- **Anyone seeking alternative control schemes** for specialized applications

## Applications

- **UAV and Rover Control**: Bridge mouse input to Mission Planner and other MAVLink-compatible ground control software with professional-grade stability features
- **Adaptive Gaming**: Play joystick-only games using a mouse-first input scheme with customizable sensitivity
- **Research and Prototyping**: Explore new input models for robotics, simulation, or accessibility tools with comprehensive configuration options
- **Assistive Technology**: Provide joystick functionality for users who cannot operate traditional controllers

## Installation

### Prerequisites
1. **Python 3.8+** - Required for the application
2. **VJoy Driver** - Download and install from [VJoy Official Site](http://vjoystick.sourceforge.net/)
3. **Git** (optional) - For cloning the repository

### Setup Instructions

1. **Clone or download the project**:
   ```bash
   git clone <repository-url>
   cd Project-Nimbus
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure VJoy**:
   - Install VJoy driver
   - Configure VJoy device #1 with at least 6 axes (X, Y, Z, RX, RY, RZ)
   - Ensure VJoy device is enabled and available

4. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Basic Controls
- **Mouse Drag**: Click and drag within joystick circles to control position
- **Lock Buttons**: Click "Lock X" or "Lock Y" to lock individual axes
- **Reset Buttons**: Click "RESET" to center individual joysticks
- **Center All**: Centers both joysticks simultaneously
- **Emergency Stop**: Immediately centers all axes and activates failsafe

### Keyboard Shortcuts
- **ESC**: Exit application
- **F1**: Toggle debug information display
- **SPACE**: Center both joysticks

### Status Indicators
- **VJoy Connection**: Shows VJoy driver connection status
- **Failsafe Status**: Indicates if failsafe mode is active
- **Real-time Values**: Current joystick positions and processed values
- **Lock Status**: Visual indicators for locked axes

## Configuration

The application uses a JSON-based configuration system stored in `controller_config.json`. The configuration is automatically created with sensible defaults on first run.

### Key Configuration Sections

#### Joystick Settings
```json
{
  "joysticks": {
    "left": {
      "dead_zone": 0.1,
      "sensitivity": 1.0,
      "curve_type": "linear",
      "curve_power": 2.0,
      "invert_x": false,
      "invert_y": false,
      "max_range": 1.0
    }
  }
}
```

#### Safety Settings
```json
{
  "safety": {
    "enable_failsafe": true,
    "failsafe_timeout": 5.0,
    "max_update_rate": 100,
    "enable_smoothing": true,
    "smoothing_factor": 0.1
  }
}
```

### Sensitivity Curves
- **Linear**: Direct 1:1 response
- **Exponential**: More precise control near center, faster at edges
- **Logarithmic**: Faster response near center, more precise at edges

## Architecture

### Project Structure
```
Project-Nimbus/
├── main.py              # Main application entry point
├── config.py            # Configuration management system
├── virtual_joystick.py  # Virtual joystick implementation
├── vjoy_interface.py    # VJoy driver interface wrapper
├── requirements.txt     # Python dependencies
└── README.md           # This documentation
```

### Key Classes

#### `VirtualControllerApp`
Main application class handling the GUI, event processing, and coordination between components.

#### `VirtualJoystick`
Handles individual joystick logic including:
- Mouse input processing
- Position calculations
- Visual rendering
- Lock/unlock functionality

#### `VJoyInterface`
Manages communication with the VJoy driver including:
- Device initialization and management
- Axis value updates
- Failsafe monitoring
- Error handling and recovery

#### `ControllerConfig`
Configuration management system providing:
- JSON-based configuration storage
- Sensitivity curve processing
- Dead zone calculations
- Configuration validation

## Safety Features

### Failsafe System
- **Automatic Activation**: Triggers if no commands received within timeout period
- **Emergency Stop**: Manual emergency stop button
- **Axis Centering**: Automatically centers all axes during failsafe
- **Visual Indicators**: Clear status display when failsafe is active

### Rate Limiting
- **Update Rate Control**: Prevents excessive update rates
- **Safety Limits**: Hard limits on maximum update frequency
- **Smooth Operation**: Ensures stable operation under all conditions

### Error Handling
- **VJoy Connection Monitoring**: Continuous monitoring of VJoy driver status
- **Graceful Degradation**: Continues operation even if VJoy is unavailable
- **Comprehensive Logging**: Detailed error reporting and status information

## Troubleshooting

### Common Issues

#### VJoy Not Detected
- Ensure VJoy driver is properly installed
- Check that VJoy device #1 is configured and enabled
- Verify VJoy device has sufficient axes configured
- Run application as administrator if needed

#### Poor Responsiveness
- Check `update_rate` setting in configuration
- Reduce `smoothing_factor` for more responsive control
- Verify system performance and close unnecessary applications

#### Joystick Drift
- Increase `dead_zone` values in configuration
- Check for hardware interference (other controllers)
- Verify mouse sensitivity settings

### Debug Mode
Press F1 to enable debug mode, which displays:
- Current configuration values
- Update rates and timing information
- Detailed joystick position data
- VJoy driver status

## Development

### Code Style
- **PEP 8 Compliance**: All code follows Python PEP 8 style guidelines
- **Type Hints**: Comprehensive type annotations for better code clarity
- **Documentation**: Detailed docstrings for all classes and methods
- **Error Handling**: Robust error handling throughout the application

### Testing
- **Configuration Validation**: Built-in configuration validation
- **Failsafe Testing**: Comprehensive failsafe system testing
- **Edge Case Handling**: Proper handling of edge cases and error conditions

### Extension Points
- **Custom Sensitivity Curves**: Easy to add new curve types
- **Additional Input Methods**: Framework supports multiple input types
- **Plugin Architecture**: Modular design allows for easy extensions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues, questions, or contributions, please refer to the project's issue tracker or documentation.

---

**Note**: This software is designed for educational and development purposes. When using for actual drone control, always follow proper safety protocols and local regulations.
