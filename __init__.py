"""
WinHotkeys - A Windows hotkey library for Python

This library provides a simple way to register global hotkeys in Windows applications.
It uses the Windows RegisterHotKey API to register hotkeys and handle key events.

Example usage:
    from winhotkeys import HotkeyHandler

    def on_hotkey_pressed():
        print("Hotkey was pressed!")

    # Create a hotkey handler
    hotkey_handler = HotkeyHandler(
        hotkey_combination="control+alt+h",  # Define your hotkey combination
        callback=on_hotkey_pressed,          # Function to call when hotkey is pressed
        suppress=True                        # Suppress the hotkey so it doesn't trigger in other apps
    )

    # Start listening for hotkeys
    hotkey_handler.start()

    # Your application code here...
    # Keep the main thread running (e.g., with a GUI event loop or a simple loop)

    # When you're done, stop listening
    hotkey_handler.stop()
"""

__version__ = '1.0.0'

from .hotkey import HotkeyManager, HotkeyHandler
