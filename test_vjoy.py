#!/usr/bin/env python3
"""
VJoy Test Script - Diagnose VJoy installation and configuration issues.
"""

import sys

def test_pyvjoy_import():
    """Test if pyvjoy can be imported and what functions are available."""
    print("Testing PyVjoy import...")
    try:
        import pyvjoy
        print("✓ PyVjoy imported successfully")
        
        # Check available attributes
        required_attrs = ['vJoyEnabled', 'VJoyDevice', 'GetvJoyVersion', 'GetVJDStatus']
        available_attrs = []
        missing_attrs = []
        
        for attr in required_attrs:
            if hasattr(pyvjoy, attr):
                available_attrs.append(attr)
            else:
                missing_attrs.append(attr)
        
        print(f"✓ Available functions: {', '.join(available_attrs)}")
        if missing_attrs:
            print(f"✗ Missing functions: {', '.join(missing_attrs)}")
            return False, pyvjoy
        
        return True, pyvjoy
        
    except ImportError as e:
        print(f"✗ Failed to import pyvjoy: {e}")
        return False, None

def test_vjoy_driver(pyvjoy):
    """Test VJoy driver availability."""
    print("\nTesting VJoy driver...")
    
    try:
        if pyvjoy.vJoyEnabled():
            print("✓ VJoy driver is enabled")
        else:
            print("✗ VJoy driver is not enabled")
            return False
    except Exception as e:
        print(f"✗ Error checking VJoy driver: {e}")
        return False
    
    # Try to get version info
    try:
        dll_ver, driver_ver = pyvjoy.GetvJoyVersion()
        print(f"✓ VJoy Driver Version: {driver_ver}, DLL Version: {dll_ver}")
    except Exception as e:
        print(f"⚠ Could not get VJoy version: {e}")
    
    return True

def test_vjoy_device(pyvjoy, device_id=1):
    """Test specific VJoy device."""
    print(f"\nTesting VJoy device #{device_id}...")
    
    try:
        status = pyvjoy.GetVJDStatus(device_id)
        
        if status == pyvjoy.VJD_STAT_OWN:
            print(f"✓ Device {device_id} is owned by this application")
        elif status == pyvjoy.VJD_STAT_FREE:
            print(f"✓ Device {device_id} is free and available")
        elif status == pyvjoy.VJD_STAT_BUSY:
            print(f"✗ Device {device_id} is busy (used by another application)")
            return False
        elif status == pyvjoy.VJD_STAT_MISS:
            print(f"✗ Device {device_id} is not configured")
            print("  → Open VJoy configuration tool and enable device #1")
            return False
        else:
            print(f"✗ Device {device_id} has unknown status: {status}")
            return False
            
    except Exception as e:
        print(f"✗ Error checking device status: {e}")
        return False
    
    # Try to create device instance
    try:
        device = pyvjoy.VJoyDevice(device_id)
        print(f"✓ Successfully created VJoyDevice({device_id})")
        
        # Test setting an axis
        try:
            device.set_axis(pyvjoy.HID_USAGE_X, 16384)  # Center position
            print("✓ Successfully set X axis")
            
            # Test setting other axes
            device.set_axis(pyvjoy.HID_USAGE_Y, 16384)
            device.set_axis(pyvjoy.HID_USAGE_Z, 16384)
            device.set_axis(pyvjoy.HID_USAGE_RX, 16384)
            device.set_axis(pyvjoy.HID_USAGE_RY, 16384)
            device.set_axis(pyvjoy.HID_USAGE_RZ, 16384)
            print("✓ Successfully set all 6 axes")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to set axes: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to create VJoyDevice: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("Project Nimbus - VJoy Diagnostic Test")
    print("=" * 60)
    
    # Test 1: PyVjoy import
    success, pyvjoy = test_pyvjoy_import()
    if not success:
        print("\n" + "=" * 60)
        print("DIAGNOSIS: PyVjoy library issue")
        print("SOLUTION: Reinstall pyvjoy with: pip install pyvjoy==1.0.1")
        return 1
    
    # Test 2: VJoy driver
    if not test_vjoy_driver(pyvjoy):
        print("\n" + "=" * 60)
        print("DIAGNOSIS: VJoy driver not installed or enabled")
        print("SOLUTION:")
        print("1. Download VJoy from: http://vjoystick.sourceforge.net/")
        print("2. Install the driver")
        print("3. Restart your computer")
        return 1
    
    # Test 3: VJoy device
    if not test_vjoy_device(pyvjoy):
        print("\n" + "=" * 60)
        print("DIAGNOSIS: VJoy device #1 not configured properly")
        print("SOLUTION:")
        print("1. Run 'Configure vJoy' from Start Menu")
        print("2. Enable Device #1")
        print("3. Configure it with at least 6 axes (X, Y, Z, RX, RY, RZ)")
        print("4. Click 'Apply' and close the configuration tool")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("VJoy is properly configured and ready to use.")
    print("You can now run Project Nimbus successfully.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
