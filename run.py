#!/usr/bin/env python3
"""
Quick launcher script for Project Nimbus Virtual Controller.
Handles virtual environment setup, dependency checking and provides user-friendly error messages.
"""

import sys
import subprocess
import os
import venv
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def setup_virtual_environment():
    """Create and setup virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            venv.create(venv_path, with_pip=True)
            print("Virtual environment created successfully!")
        except Exception as e:
            print(f"ERROR: Failed to create virtual environment: {e}")
            return False
    
    return True

def get_venv_python():
    """Get the path to Python executable in virtual environment."""
    if sys.platform == "win32":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def check_dependencies():
    """Check if required packages are installed in virtual environment."""
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("ERROR: Virtual environment Python not found")
        return False
    
    required_packages = ['pygame', 'pyvjoy', 'numpy']
    
    # Check if packages are installed
    try:
        result = subprocess.run([
            str(venv_python), '-c', 
            '; '.join([f'import {pkg}' for pkg in required_packages])
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Installing dependencies in virtual environment...")
            # Upgrade pip first
            subprocess.check_call([str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'])
            # Install requirements
            subprocess.check_call([str(venv_python), '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("Dependencies installed successfully!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        print("Please check your internet connection and try again")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during dependency check: {e}")
        return False

def run_in_venv():
    """Run the application in the virtual environment."""
    venv_python = get_venv_python()
    
    try:
        # Run main.py using the virtual environment Python
        result = subprocess.run([str(venv_python), "main.py"], cwd=Path.cwd())
        return result.returncode
    except Exception as e:
        print(f"ERROR: Failed to run application: {e}")
        return 1

def main():
    """Main launcher function."""
    print("=" * 50)
    print("Project Nimbus - Virtual Controller Interface")
    print("=" * 50)
    print()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return 1
    
    # Setup virtual environment
    if not setup_virtual_environment():
        input("Press Enter to exit...")
        return 1
    
    # Check dependencies in virtual environment
    if not check_dependencies():
        input("Press Enter to exit...")
        return 1
    
    print("Starting application in virtual environment...")
    print("Controls:")
    print("  - ESC: Exit application")
    print("  - F1: Toggle debug info")
    print("  - SPACE: Center both joysticks")
    print()
    
    try:
        return run_in_venv()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nIf this is a VJoy error, make sure:")
        print("1. VJoy driver is installed")
        print("2. VJoy device #1 is configured with 6+ axes")
        print("3. VJoy device is enabled")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
