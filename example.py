"""
Example script demonstrating how to use the WinHotkeys library.
"""
# Use relative import when running from within the package directory
try:
    from winhotkeys import HotkeyHandler
except ImportError:
    # If that fails, try a relative import
    from . import HotkeyHandler
import time

def on_hotkey1_pressed():
    """Callback function for the first hotkey."""
    print("\nHotkey 1 (Ctrl+Alt+1) was pressed!")

def on_hotkey2_pressed():
    """Callback function for the second hotkey."""
    print("\nHotkey 2 (Ctrl+Alt+2) was pressed!")

def main():
    """Main function to demonstrate the WinHotkeys library."""
    print("WinHotkeys Example")
    print("=================")
    
    # Create hotkey handlers
    print("Creating hotkey handlers...")
    hotkey1 = HotkeyHandler("control+alt+1", on_hotkey1_pressed, suppress=True)
    hotkey2 = HotkeyHandler("control+alt+2", on_hotkey2_pressed, suppress=True)
    
    # Start listening for hotkeys
    print("Starting to listen for hotkeys...")
    hotkey1.start()
    hotkey2.start()
    
    print("\nHotkeys registered and active:")
    print("- Press Ctrl+Alt+1 to trigger the first hotkey")
    print("- Press Ctrl+Alt+2 to trigger the second hotkey")
    print("- Press Ctrl+C to exit")
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        # Stop listening when the user presses Ctrl+C
        print("\nStopping hotkey handlers...")
        hotkey1.stop()
        hotkey2.stop()
        print("Exiting...")

if __name__ == "__main__":
    main()
