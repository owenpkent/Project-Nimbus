import sys
import traceback

try:
    import pyvjoy
    print("PyVjoy imported successfully")
    print("Available attributes:", [attr for attr in dir(pyvjoy) if not attr.startswith('_')])
    
    # Check for different possible function names
    if hasattr(pyvjoy, 'vJoyEnabled'):
        print("vJoyEnabled function found")
        try:
            enabled = pyvjoy.vJoyEnabled()
            print(f"VJoy enabled: {enabled}")
        except Exception as e:
            print(f"Error calling vJoyEnabled: {e}")
    else:
        print("vJoyEnabled function NOT found")
    
    # Try to create a device directly
    if hasattr(pyvjoy, 'VJoyDevice'):
        print("VJoyDevice class found")
        try:
            device = pyvjoy.VJoyDevice(1)
            print("VJoyDevice created successfully")
            
            # Try to set an axis
            if hasattr(pyvjoy, 'HID_USAGE_X'):
                device.set_axis(pyvjoy.HID_USAGE_X, 16384)
                print("Successfully set X axis")
            else:
                print("HID_USAGE_X not found")
                
        except Exception as e:
            print(f"Error with VJoyDevice: {e}")
            traceback.print_exc()
    else:
        print("VJoyDevice class NOT found")
        
except ImportError as e:
    print(f"Failed to import pyvjoy: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    traceback.print_exc()
