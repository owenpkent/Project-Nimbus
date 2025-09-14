# Project Nimbus - Quick Start Guide

## 🚀 How to Run the Application

### Option 1: Double-click to run (Recommended)
- **Windows**: Double-click `run.bat`
- **Cross-platform**: Run `run.py`

### Option 2: Command line
```bash
python run.py
```

## 📁 Project Structure

```
Project-Nimbus/
├── 🎯 run.py          # Main launcher script (START HERE)
├── 🎯 run.bat         # Windows batch launcher (START HERE)
├── 📋 requirements.txt # Python dependencies
├── ⚙️ controller_config.json # Configuration file
├── 📖 README.md       # Detailed documentation
├── 🖼️ logo.png        # Project logo
├── 📂 src/            # Source code
│   ├── main.py        # Main application
│   ├── config.py      # Configuration management
│   ├── virtual_joystick.py # Joystick controls
│   ├── vjoy_interface.py   # VJoy driver interface
│   ├── axis_config_dialog.py # Axis configuration
│   └── joystick_settings_dialog.py # Settings dialog
└── 📂 tests/          # Test files
    ├── simple_vjoy_test.py
    ├── test_vjoy.py
    └── test_dialog.py
```

## 🎮 Features
- Dual virtual joysticks with lock/unlock functionality
- Throttle and rudder controls
- Resizable interface (50% - 200% scaling)
- Compact 16:9 aspect ratio layout
- VJoy integration for game compatibility

## 🔧 Requirements
- Python 3.8+
- VJoy driver installed and configured
- Dependencies auto-installed via run.py

---
**Quick Start**: Just run `run.py` or `run.bat` - everything else is handled automatically!
