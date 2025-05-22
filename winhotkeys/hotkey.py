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
import sys

# Import key mappings from keycodes module
try:
    from .keycodes import vk_key_names
except ImportError:
    # For direct imports or testing
    try:
        from keycodes import vk_key_names
    except ImportError:
        # Define a minimal set of key mappings if keycodes.py is not available
        vk_key_names = {}

# Windows message constants
WM_HOTKEY = 0x0312
WM_CLOSE = 0x0010  # Standard Windows close message
WM_DESTROY = 0x0002  # Standard Windows destroy message
WM_QUIT = 0x0012  # Standard Windows quit message
WM_USER = 0x0400  # Base for user-defined messages
WM_USER_CLEANUP = WM_USER + 1  # Custom message for cleanup

# Define constants that might not be in win32con
MOD_NOREPEAT = 0x4000  # Prevent auto-repeat when the hotkey is held down

# Global dictionary to store hotkey managers by window handle
_hotkey_managers = {}

# Global dictionary to store window procedures by window handle
_window_procedures = {}

# Global window procedure function
def _global_wndproc(hwnd, msg, wparam, lparam):
    """Global window procedure function for all hotkey manager windows."""
    try:
        # Debug logging for all messages
        print(f"DEBUG: Window procedure received message: {msg} (0x{msg:04x}), wparam: {wparam}, lparam: {lparam}")
        
        # Specifically check for WM_HOTKEY (0x0312)
        if msg == WM_HOTKEY:
            print(f"DEBUG: WM_HOTKEY message received! ID: {wparam}")
            
            # wparam contains the hotkey ID
            hotkey_id = wparam
            print(f"DEBUG: Received WM_HOTKEY message for hotkey ID: {hotkey_id}")
            
            # Get the hotkey manager for this window
            if hwnd in _hotkey_managers:
                hotkey_manager = _hotkey_managers[hwnd]
                
                # Call the callback function for this hotkey
                if hotkey_id in hotkey_manager.registered_hotkeys:
                    print(f"DEBUG: Found registered hotkey ID {hotkey_id}, calling callback function...")
                    # Get the hotkey combination for better logging
                    hotkey_combo = hotkey_manager.registered_hotkeys[hotkey_id]['combination']
                    print(f"DEBUG: Executing callback for hotkey: {hotkey_combo}")
                    
                    # Call the callback
                    hotkey_manager.registered_hotkeys[hotkey_id]['callback']()
                    
                    # Force flush the output to ensure it's displayed immediately
                    sys.stdout.flush()
                    
                    print(f"DEBUG: Callback for hotkey ID {hotkey_id} executed successfully")
                    return 0
                else:
                    print(f"DEBUG: Received hotkey ID {hotkey_id} but it's not in registered_hotkeys")
            else:
                print(f"DEBUG: Received hotkey message for window {hwnd} but it's not in _hotkey_managers")
        
        # Handle custom cleanup message
        elif msg == WM_USER_CLEANUP:
            print(f"DEBUG: Received WM_USER_CLEANUP message")
            
            # Get the hotkey manager for this window
            if hwnd in _hotkey_managers:
                hotkey_manager = _hotkey_managers[hwnd]
                
                # Unregister all hotkeys
                for hotkey_id in list(hotkey_manager.registered_hotkeys.keys()):
                    try:
                        win32gui.UnregisterHotKey(hwnd, hotkey_id)
                        print(f"Unregistered hotkey ID {hotkey_id}")
                    except Exception as e:
                        print(f"Error unregistering hotkey ID {hotkey_id}: {e}")
                
                # Remove this hotkey manager from the global dictionary
                del _hotkey_managers[hwnd]
                
                # Post a quit message to exit the message loop
                win32gui.PostQuitMessage(0)
                return 0
                
        # Pass the message to the default window procedure
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    except Exception as e:
        print(f"Error in window procedure: {e}")
        import traceback
        traceback.print_exc()
        return 0

# Create a window procedure function that can be used with win32gui
def create_window_proc():
    """Create a window procedure function that can be used with win32gui."""
    # This is a hack to create a window procedure function that can be used with win32gui
    # The function is stored in a dictionary to prevent it from being garbage collected
    def window_proc(hwnd, msg, wparam, lparam):
        return _global_wndproc(hwnd, msg, wparam, lparam)
    
    # Store the function in the dictionary to prevent it from being garbage collected
    _window_procedures[window_proc] = window_proc
    
    return window_proc

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
        # First check if it's a single character that we can get the VK code for at runtime
        if len(main_key) == 1:
            try:
                # Get the VK code for the character in the current keyboard layout
                vk_code = ctypes.windll.user32.VkKeyScanW(ord(main_key)) & 0xFF
                print(f"DEBUG: Got VK code for '{main_key}' at runtime: {vk_code} (0x{vk_code:x})")
            except Exception as e:
                print(f"Error getting VK code for '{main_key}' at runtime: {e}")
                # Fall back to the dictionary
                vk_code = vk_key_names.get(main_key)
        else:
            # Use the imported vk_key_names dictionary for named keys
            vk_code = vk_key_names.get(main_key)
        
        # Debug output to verify the parsed values
        print(f"DEBUG: Parsed hotkey combination: '{hotkey_combination}'")
        print(f"DEBUG: Main key: '{main_key}', Modifiers: {modifier_keys}")
        if vk_code is not None:
            print(f"DEBUG: VK code: {vk_code} (0x{vk_code:x}), Modifiers: {modifiers} (0x{modifiers:x})")
        else:
            print(f"DEBUG: VK code: None (0x0), Modifiers: {modifiers} (0x{modifiers:x})")
            
        return modifiers, vk_code

    def _get_vk_code(self, key: str) -> Optional[int]:
        """
        Get the virtual key code for a key name.
        
        Args:
            key: Key name (e.g., 'a', 'enter', 'f1')
            
        Returns:
            Virtual key code or None if not found
        """
        # Use the imported vk_key_names dictionary
        return vk_key_names.get(key.lower())

    def start_listening(self) -> None:
        """Start listening for registered hotkeys."""
        if self.running:
            return

        self.running = True
        
        def _thread_proc():
            """Thread procedure that creates the window, registers hotkeys, and pumps messages."""
            try:
                # 1) Register window class + create window
                class_name = f"HotkeyMgr{HotkeyManager._next_class_id}"
                HotkeyManager._next_class_id += 1
                
                # Create a window procedure function
                window_proc = create_window_proc()
                
                wndclass = win32gui.WNDCLASS()
                wndclass.lpszClassName = class_name
                wndclass.lpfnWndProc = window_proc
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
                    # Create a normal window (not a message-only window)
                    self.hwnd = win32gui.CreateWindowEx(
                        0,  # extended style
                        class_name,  # class name
                        f"Hotkey Manager Window {HotkeyManager._next_class_id}",  # window name
                        0,  # style
                        0, 0, 0, 0,  # dimensions
                        0,  # parent - use 0 for a top-level window
                        0,  # menu
                        wndclass.hInstance,  # instance
                        None  # creation parameters
                    )
                    
                    if not self.hwnd:
                        print("Failed to create window")
                        self.running = False
                        return
                    
                    # Register this hotkey manager in the global dictionary
                    _hotkey_managers[self.hwnd] = self
                except Exception as e:
                    print(f"Error creating window: {e}")
                    self.running = False
                    return
                
                # 2) Register all hotkeys on THIS thread
                for hotkey_id, details in self.registered_hotkeys.items():
                    try:
                        # Print detailed information about the hotkey being registered
                        print(f"Registering hotkey ID {hotkey_id}: modifiers={details['modifiers']}, vk_code={details['vk_code']} ({details['combination']})")
                        
                        # Skip the unregistration step for the first registration
                        # This avoids the "Hot key is not registered" error
                        print(f"Registering hotkey ID {hotkey_id} ({details['combination']}) for the first time.")
                        
                        # Now register the hotkey with improved error handling
                        try:
                            success = win32gui.RegisterHotKey(
                                self.hwnd,
                                hotkey_id,
                                details['modifiers'],
                                details['vk_code']
                            )
                            
                            # Print the return value and last error for debugging
                            last_error = ctypes.GetLastError()
                            print(f"RegisterHotKey→ {success}, GetLastError→ {last_error}")
                            
                            # In pywin32, RegisterHotKey might return None even on success
                            # So we check the last error code instead
                            if last_error == 0:
                                print(f"Successfully registered hotkey ID {hotkey_id} ({details['combination']})")
                            else:
                                error_message = f"RegisterHotKey failed (0x{last_error:08X}): {ctypes.FormatError(last_error)}"
                                print(f"Failed to register hotkey ID {hotkey_id} ({details['combination']}): {error_message}")
                                # Don't raise an exception, just log the error and continue
                                print(f"Will attempt to use the hotkey anyway.")
                        except win32gui.error as win_error:
                            # Check if the error is "Hot key is already registered" (error code 1409)
                            if win_error.winerror == 1409:
                                print(f"Hotkey ID {hotkey_id} ({details['combination']}) is already registered. This is normal if the application was not closed properly previously.")
                                # Try to unregister and register again with improved error handling
                                try:
                                    win32gui.UnregisterHotKey(self.hwnd, hotkey_id)
                                    success = win32gui.RegisterHotKey(
                                        self.hwnd,
                                        hotkey_id,
                                        details['modifiers'],
                                        details['vk_code']
                                    )
                                    if success:
                                        print(f"Successfully re-registered hotkey ID {hotkey_id} ({details['combination']})")
                                    else:
                                        err = ctypes.GetLastError()
                                        if err != 0:  # Only report as an error if the error code is not 0
                                            error_message = f"Re-RegisterHotKey failed (0x{err:08X}): {ctypes.FormatError(err)}"
                                            print(f"Failed to re-register hotkey ID {hotkey_id} ({details['combination']}): {error_message}")
                                            raise OSError(error_message)
                                        else:
                                            # Error code 0 means success, so this is not actually an error
                                            print(f"Successfully re-registered hotkey ID {hotkey_id} ({details['combination']})")
                                except Exception as e:
                                    print(f"Error re-registering hotkey ID {hotkey_id}: {e}")
                                    print(f"Will attempt to use the hotkey anyway.")
                            else:
                                # Re-raise other errors
                                raise
                    except Exception as reg_error:
                        print(f"Exception registering hotkey ID {hotkey_id}: {reg_error}")
                        import traceback
                        traceback.print_exc()
                
                # 3) Pump messages here
                print("DEBUG: Message loop started")
                print("HotkeyManager: entering PumpMessages")
                
                # This will block and process all messages, including WM_HOTKEY,
                # until win32gui.PostQuitMessage() is called
                win32gui.PumpMessages()
                
                print("HotkeyManager: Message loop exited.")
            except Exception as e:
                print(f"Error in thread procedure: {e}")
                import traceback
                traceback.print_exc()
                self.running = False
        
        # Start the thread
        self._message_thread = threading.Thread(target=_thread_proc, daemon=True)
        self._message_thread.start()
        
        # Register cleanup on exit
        atexit.register(self.stop_listening)
        
        print("HotkeyManager: Started listening for hotkeys in background thread.")

    def stop_listening(self) -> None:
        """Stop listening for hotkeys and clean up."""
        if not self.running:
            return

        try:
            self.running = False
            
            # Send a custom cleanup message to the window thread
            if self.hwnd:
                # Post our custom cleanup message to the window
                # This will be handled by the window procedure in the window thread
                win32gui.PostMessage(self.hwnd, WM_USER_CLEANUP, 0, 0)
                print("HotkeyManager: Posted cleanup message to window thread")
                
                # Give the thread a little time to process the cleanup message
                # This helps prevent issues with daemon threads during interpreter shutdown
                time.sleep(0.1)
                
            # Don't wait for the message thread to exit, as it will exit on its own
            # when it receives the WM_USER_CLEANUP message
                
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
            # Debug logging for all messages
            print(f"DEBUG: Window procedure received message: {msg}")
            
            if msg == WM_HOTKEY:
                # wparam contains the hotkey ID
                hotkey_id = wparam
                print(f"DEBUG: Received WM_HOTKEY message for hotkey ID: {hotkey_id}")
                
                # Call the callback function for this hotkey
                if hotkey_id in self.registered_hotkeys:
                    print(f"DEBUG: Found registered hotkey ID {hotkey_id}, calling callback function...")
                    # Get the hotkey combination for better logging
                    hotkey_combo = self.registered_hotkeys[hotkey_id]['combination']
                    print(f"DEBUG: Executing callback for hotkey: {hotkey_combo}")
                    
                    # Call the callback
                    self.registered_hotkeys[hotkey_id]['callback']()
                    
                    print(f"DEBUG: Callback for hotkey ID {hotkey_id} executed successfully")
                    return 0
                else:
                    print(f"DEBUG: Received hotkey ID {hotkey_id} but it's not in registered_hotkeys")
                    
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
            print("DEBUG: Message loop started")
            print("HotkeyManager: entering PumpMessages")
            
            # This will block and process all messages, including WM_HOTKEY,
            # until win32gui.PostQuitMessage() is called
            win32gui.PumpMessages()
            
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
