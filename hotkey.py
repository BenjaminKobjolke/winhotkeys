"""
Hotkey registration and handling for Windows applications using the RegisterHotKey API
"""
from typing import Callable, Dict, List, Optional, Set, Tuple, Any
import threading
import time
import ctypes
import atexit
import win32con
import win32api
import win32gui

# Windows message constants
WM_HOTKEY = 0x0312

# Define constants that might not be in win32con
MOD_NOREPEAT = 0x4000  # Prevent auto-repeat when the hotkey is held down

class HotkeyManager:
    """
    Manages hotkey registration and handling using the Windows RegisterHotKey API.
    """
    # Class variables
    _next_id = 1  # Next hotkey ID
    _next_class_id = 1  # Next window class ID
    
    def __init__(self):
        """Initialize the hotkey manager."""
        self.registered_hotkeys = {}  # Stores hotkey IDs and their details
        self.running = False
        self.hwnd = None  # Window handle for receiving hotkey messages
        self._message_thread = None  # Thread for the Windows message loop
        
    def register_hotkey(self, hotkey_combination: str, callback: Callable, suppress: bool = False) -> None:
        """
        Register a hotkey with a callback function.

        Args:
            hotkey_combination: Hotkey combination string (e.g., 'control+shift+a')
            callback: Function to call when the hotkey is pressed
            suppress: Whether to suppress the hotkey (always True with RegisterHotKey)
        """
        # Parse the hotkey combination
        modifiers, vk_code = self._parse_hotkey_combination(hotkey_combination)
        if vk_code is None:
            print(f"Warning: Could not parse hotkey combination: {hotkey_combination}")
            return
            
        # Get a unique ID for this hotkey
        hotkey_id = HotkeyManager._next_id
        HotkeyManager._next_id += 1
        
        # Store the hotkey details
        self.registered_hotkeys[hotkey_id] = {
            'modifiers': modifiers,
            'vk_code': vk_code,
            'callback': callback,
            'combination': hotkey_combination  # Store the original combination for logging
        }
        
        print(f"Registered hotkey: {hotkey_combination} (ID={hotkey_id})")

    def _parse_hotkey_combination(self, hotkey_combination: str) -> Tuple[int, Optional[int]]:
        """
        Parse a hotkey combination string into modifiers and a virtual key code.
        
        Args:
            hotkey_combination: Hotkey combination string (e.g., 'control+shift+a')
            
        Returns:
            Tuple of (modifiers, vk_code) where modifiers is a bitmask of modifier keys
        """
        modifiers = 0
        vk_code = None
        keys = [k.strip() for k in hotkey_combination.lower().split('+')]
        
        # The last key is the main key, the rest are modifiers
        if not keys:
            return modifiers, None
            
        main_key = keys[-1]
        modifier_keys = keys[:-1]
        
        # Process modifiers
        for key in modifier_keys:
            if key == 'control' or key == 'ctrl':
                modifiers |= win32con.MOD_CONTROL
            elif key == 'alt':
                modifiers |= win32con.MOD_ALT
            elif key == 'shift':
                modifiers |= win32con.MOD_SHIFT
            elif key == 'win' or key == 'windows':
                modifiers |= win32con.MOD_WIN
            else:
                print(f"Warning: Unknown modifier key: {key}")
                return modifiers, None
                
        # If no modifiers are specified, use MOD_NOREPEAT to prevent auto-repeat
        if modifiers == 0:
            modifiers = MOD_NOREPEAT
        else:
            # Add MOD_NOREPEAT to prevent auto-repeat
            modifiers |= MOD_NOREPEAT
                
        # Process main key
        # Try to get from keycodes module first
        try:
            from .keycodes import vk_key_names
            if main_key in vk_key_names:
                vk_code = vk_key_names[main_key]
            else:
                # Try common mappings
                vk_code = self._get_vk_code(main_key)
        except ImportError:
            # Fall back to common mappings
            vk_code = self._get_vk_code(main_key)
            
        return modifiers, vk_code

    def _get_vk_code(self, key: str) -> Optional[int]:
        """
        Get the virtual key code for a key name.
        
        Args:
            key: Key name (e.g., 'a', 'enter', 'f1')
            
        Returns:
            Virtual key code or None if not found
        """
        # Common key mappings
        key_map = {
            'enter': win32con.VK_RETURN,
            'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB,
            'escape': win32con.VK_ESCAPE,
            'esc': win32con.VK_ESCAPE,
            'backspace': win32con.VK_BACK,
            'delete': win32con.VK_DELETE,
            'del': win32con.VK_DELETE,
            'insert': win32con.VK_INSERT,
            'ins': win32con.VK_INSERT,
            'home': win32con.VK_HOME,
            'end': win32con.VK_END,
            'pageup': win32con.VK_PRIOR,
            'pagedown': win32con.VK_NEXT,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'f1': win32con.VK_F1,
            'f2': win32con.VK_F2,
            'f3': win32con.VK_F3,
            'f4': win32con.VK_F4,
            'f5': win32con.VK_F5,
            'f6': win32con.VK_F6,
            'f7': win32con.VK_F7,
            'f8': win32con.VK_F8,
            'f9': win32con.VK_F9,
            'f10': win32con.VK_F10,
            'f11': win32con.VK_F11,
            'f12': win32con.VK_F12,
            '0': 0x30,
            '1': 0x31,
            '2': 0x32,
            '3': 0x33,
            '4': 0x34,
            '5': 0x35,
            '6': 0x36,
            '7': 0x37,
            '8': 0x38,
            '9': 0x39,
            'a': 0x41,
            'b': 0x42,
            'c': 0x43,
            'd': 0x44,
            'e': 0x45,
            'f': 0x46,
            'g': 0x47,
            'h': 0x48,
            'i': 0x49,
            'j': 0x4A,
            'k': 0x4B,
            'l': 0x4C,
            'm': 0x4D,
            'n': 0x4E,
            'o': 0x4F,
            'p': 0x50,
            'q': 0x51,
            'r': 0x52,
            's': 0x53,
            't': 0x54,
            'u': 0x55,
            'v': 0x56,
            'w': 0x57,
            'x': 0x58,
            'y': 0x59,
            'z': 0x5A,
        }
        
        return key_map.get(key.lower())

    def start_listening(self) -> None:
        """Start listening for registered hotkeys."""
        if self.running:
            return

        try:
            self.running = True
            
            # Create a hidden window to receive hotkey messages
            # Use a unique class name for each instance
            class_id = HotkeyManager._next_class_id
            HotkeyManager._next_class_id += 1
            class_name = f"HotkeyManagerWindow_{class_id}"
            
            wndclass = win32gui.WNDCLASS()
            wndclass.lpszClassName = class_name
            wndclass.lpfnWndProc = self._wndproc
            wndclass.hInstance = win32api.GetModuleHandle(None)
            
            # Register the window class
            try:
                win32gui.RegisterClass(wndclass)
            except Exception as e:
                print(f"Error registering window class: {e}")
                self.running = False
                return
            
            # Create the window
            try:
                self.hwnd = win32gui.CreateWindow(
                    class_name,  # Use the unique class name
                    f"Hotkey Manager Window {class_id}",
                    0,  # style
                    0, 0, 0, 0,  # dimensions
                    0,  # parent
                    0,  # menu
                    wndclass.hInstance,
                    None  # creation parameters
                )
                
                if not self.hwnd:
                    print("Failed to create window")
                    self.running = False
                    return
            except Exception as e:
                print(f"Error creating window: {e}")
                self.running = False
                return
            
            # Register the hotkeys
            for hotkey_id, details in self.registered_hotkeys.items():
                try:
                    # Print detailed information about the hotkey being registered
                    print(f"Registering hotkey ID {hotkey_id}: modifiers={details['modifiers']}, vk_code={details['vk_code']} ({details['combination']})")
                    
                    result = win32gui.RegisterHotKey(
                        self.hwnd,
                        hotkey_id,
                        details['modifiers'],
                        details['vk_code']
                    )
                    
                    if result:
                        print(f"Successfully registered hotkey ID {hotkey_id} ({details['combination']})")
                    else:
                        error_code = ctypes.get_last_error()
                        print(f"Failed to register hotkey ID {hotkey_id} ({details['combination']}), error code: {error_code}")
                        
                        # Try to get a more detailed error message
                        try:
                            error_message = ctypes.FormatError(error_code)
                            print(f"Error message: {error_message}")
                        except Exception as format_error:
                            print(f"Error getting error message: {format_error}")
                except Exception as reg_error:
                    print(f"Exception registering hotkey ID {hotkey_id}: {reg_error}")
                    import traceback
                    traceback.print_exc()
            
            # Register cleanup on exit
            atexit.register(self.stop_listening)
            
            # Start the message loop in a separate thread
            self._message_thread = threading.Thread(target=self._message_loop)
            self._message_thread.daemon = True
            self._message_thread.start()
            
            print("HotkeyManager: Started listening for hotkeys.")
        except Exception as e:
            print(f"Error in start_listening: {e}")
            import traceback
            traceback.print_exc()
            self.running = False

    def stop_listening(self) -> None:
        """Stop listening for hotkeys and clean up."""
        if not self.running:
            return

        try:
            self.running = False
            
            # Unregister the hotkeys
            if self.hwnd:
                for hotkey_id in self.registered_hotkeys.keys():
                    try:
                        win32gui.UnregisterHotKey(self.hwnd, hotkey_id)
                    except Exception as e:
                        print(f"Error unregistering hotkey ID {hotkey_id}: {e}")
                
                # Destroy the window
                win32gui.DestroyWindow(self.hwnd)
                self.hwnd = None
                
            # Wait for the message thread to exit
            if self._message_thread and self._message_thread.is_alive():
                self._message_thread.join(timeout=1.0)
                
            print("HotkeyManager: Stopped listening for hotkeys.")
        except Exception as e:
            print(f"Error in stop_listening: {e}")
            import traceback
            traceback.print_exc()

    def _wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """
        Window procedure for handling hotkey messages.
        
        Args:
            hwnd: Window handle
            msg: Message ID
            wparam: Message parameter (hotkey ID for WM_HOTKEY)
            lparam: Message parameter
            
        Returns:
            Result of message processing
        """
        try:
            if msg == WM_HOTKEY:
                # wparam contains the hotkey ID
                hotkey_id = wparam
                
                # Call the callback function for this hotkey
                if hotkey_id in self.registered_hotkeys:
                    self.registered_hotkeys[hotkey_id]['callback']()
                    return 0
                    
            # Pass the message to the default window procedure
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        except Exception as e:
            print(f"Error in window procedure: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def _message_loop(self) -> None:
        """Run the Windows message loop to process hotkey messages."""
        try:
            # Run the message loop
            while self.running:
                try:
                    # Process all waiting messages
                    win32gui.PumpWaitingMessages()
                    
                    # Sleep to reduce CPU usage
                    time.sleep(0.01)
                except Exception as pump_error:
                    print(f"Error in PumpWaitingMessages: {pump_error}")
                    
            print("HotkeyManager: Message loop exited.")
        except Exception as e:
            print(f"Error in message loop: {e}")
            import traceback
            traceback.print_exc()


class HotkeyHandler:
    """
    Handles hotkey functionality using HotkeyManager.
    Provides a simple interface for registering and handling hotkeys.
    """

    def __init__(self, hotkey_combination: str, callback: Callable, suppress: bool = False):
        """
        Initialize the hotkey handler.

        Args:
            hotkey_combination: Hotkey combination string (e.g., 'control+shift+f12')
            callback: Function to call when the hotkey is pressed
            suppress: Whether to suppress the hotkey so it doesn't trigger in other applications
        """
        self.hotkey_manager = HotkeyManager()
        self.hotkey_combination = hotkey_combination
        self.callback = callback
        self.suppress = suppress

    def start(self) -> None:
        """Start the hotkey handler."""
        self.hotkey_manager.register_hotkey(self.hotkey_combination, self.callback, self.suppress)
        self.hotkey_manager.start_listening()

    def stop(self) -> None:
        """Stop the hotkey handler."""
        self.hotkey_manager.stop_listening()
