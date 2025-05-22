# WinHotkeys

A Python library for registering global hotkeys in Windows applications with suppression capability.

## Features

-   Register global hotkeys that work system-wide
-   Suppress hotkeys so they don't trigger in other applications
-   Simple API for easy integration
-   Support for modifier keys (Ctrl, Alt, Shift, Win)
-   Proper error handling and cleanup

## Installation

```bash
# From the directory containing setup.py
pip install .

# Or directly from GitHub (once published)
# pip install git+https://github.com/yourusername/winhotkeys.git
```

## Requirements

-   Windows operating system
-   Python 3.6+
-   pywin32 package

## Usage

### Basic Example

```python
from winhotkeys import HotkeyHandler
import time

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

try:
    # Keep the main thread running
    print("Press Ctrl+Alt+H to trigger the hotkey...")
    print("Press Ctrl+C to exit.")
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    # Stop listening when the user presses Ctrl+C
    hotkey_handler.stop()
    print("Exiting...")
```

### Multiple Hotkeys

```python
from winhotkeys import HotkeyHandler
import time

def on_hotkey1_pressed():
    print("Hotkey 1 was pressed!")

def on_hotkey2_pressed():
    print("Hotkey 2 was pressed!")

# Create hotkey handlers
hotkey1 = HotkeyHandler("control+alt+1", on_hotkey1_pressed, suppress=True)
hotkey2 = HotkeyHandler("control+alt+2", on_hotkey2_pressed, suppress=True)

# Start listening for hotkeys
hotkey1.start()
hotkey2.start()

try:
    # Keep the main thread running
    print("Press Ctrl+Alt+1 or Ctrl+Alt+2 to trigger the hotkeys...")
    print("Press Ctrl+C to exit.")
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    # Stop listening when the user presses Ctrl+C
    hotkey1.stop()
    hotkey2.stop()
    print("Exiting...")
```

### Using with GUI Applications

```python
from winhotkeys import HotkeyHandler
import tkinter as tk

def on_hotkey_pressed():
    label.config(text="Hotkey was pressed!")

# Create the main window
root = tk.Tk()
root.title("WinHotkeys Example")
root.geometry("300x200")

# Create a label
label = tk.Label(root, text="Press Ctrl+Alt+H to trigger the hotkey")
label.pack(pady=50)

# Create a hotkey handler
hotkey_handler = HotkeyHandler("control+alt+h", on_hotkey_pressed, suppress=True)

# Start listening for hotkeys
hotkey_handler.start()

# Register cleanup on exit
def on_closing():
    hotkey_handler.stop()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main loop
root.mainloop()
```

## Supported Key Names

The library supports a wide range of key names, including:

-   Letters: 'a' through 'z'
-   Numbers: '0' through '9'
-   Function keys: 'f1' through 'f24'
-   Special keys: 'enter', 'space', 'tab', 'escape', etc.
-   Modifiers: 'control', 'alt', 'shift', 'win'

## Notes

-   This library only works on Windows systems since it uses the Windows API.
-   The hotkey combinations are specified as strings with key names separated by '+' (e.g., 'control+alt+h').
-   The main key should be the last one in the combination.
-   When using the `suppress=True` parameter, the hotkey won't be passed to other applications.

## License

MIT License
