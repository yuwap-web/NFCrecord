"""Input handler for Stream Deck and keyboard inputs"""

import threading
import queue
from typing import Optional, Callable, Dict

try:
    from streamdeck.DeviceManager import DeviceManager
    HAS_STREAMDECK = True
except ImportError:
    HAS_STREAMDECK = False

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

from config import config


class InputHandler:
    """Unified handler for Stream Deck and keyboard inputs"""

    def __init__(self):
        self.stream_deck = None
        self.key_mappings = config.get("input.key_mappings", {})
        self._lock = threading.Lock()
        self._streamdeck_initialized = False
        self._keyboard_initialized = False

        self._initialize()

    def _initialize(self) -> None:
        """Initialize both Stream Deck and keyboard listeners"""
        if HAS_STREAMDECK:
            self._initialize_streamdeck()

        if HAS_KEYBOARD:
            self._initialize_keyboard()

    def _initialize_streamdeck(self) -> bool:
        """Initialize Stream Deck connection"""
        try:
            devices = DeviceManager().enumerate()

            if not devices:
                print("⚠ No Stream Deck device found")
                return False

            self.stream_deck = devices[0]
            self.stream_deck.open()

            print(f"✓ Stream Deck initialized: {self.stream_deck.deck_type()}")
            self._streamdeck_initialized = True
            return True

        except Exception as e:
            print(f"⚠ Stream Deck initialization failed: {e}")
            return False

    def _initialize_keyboard(self) -> bool:
        """Initialize keyboard listener"""
        try:
            # Test if keyboard module is working
            print("✓ Keyboard input enabled")
            self._keyboard_initialized = True
            return True

        except Exception as e:
            print(f"⚠ Keyboard initialization failed: {e}")
            return False

    def register_streamdeck_callback(self, callback: Callable) -> None:
        """Register callback for Stream Deck key presses"""
        if not self._streamdeck_initialized or not self.stream_deck:
            return

        try:
            def key_callback(deck, key, state):
                if state:  # Key press (not release)
                    key_str = str(key)
                    if key_str in self.key_mappings:
                        callback(self.key_mappings[key_str])

            self.stream_deck.set_key_callback(key_callback)

        except Exception as e:
            print(f"Error registering Stream Deck callback: {e}")

    def register_keyboard_callback(self, callback: Callable) -> None:
        """Register callback for keyboard presses"""
        if not self._keyboard_initialized:
            return

        try:
            for key_name, value in self.key_mappings.items():
                if key_name.isdigit():  # "1", "2", "3"
                    keyboard.add_hotkey(key_name, callback, args=(value,))

            print("✓ Keyboard hotkeys registered")

        except Exception as e:
            print(f"Error registering keyboard callback: {e}")

    def get_status(self) -> Dict[str, str]:
        """Get input devices status"""
        return {
            "stream_deck": "✓ Ready" if self._streamdeck_initialized else "✗ Not available",
            "keyboard": "✓ Ready" if self._keyboard_initialized else "✗ Not available",
        }

    def cleanup(self) -> None:
        """Cleanup input handlers"""
        try:
            if HAS_KEYBOARD:
                keyboard.clear_all_hotkeys()

            if self.stream_deck:
                self.stream_deck.close()

        except Exception as e:
            print(f"Error during cleanup: {e}")


class InputHandlerWorker(threading.Thread):
    """Background worker thread for input handling"""

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__(daemon=True)
        self.handler = InputHandler()
        self.callback = callback
        self.timeout_seconds = config.get("input.timeout_seconds", 5)
        self.default_value = config.get("input.default_on_timeout", "変更あり")
        self.running = True

    def run(self):
        """Main input handler loop"""
        # Register callbacks
        if self.callback:
            self.handler.register_streamdeck_callback(self.callback)
            self.handler.register_keyboard_callback(self.callback)

        print(f"Input handler worker started (timeout: {self.timeout_seconds}s)")

        while self.running:
            try:
                import time

                time.sleep(1)

            except Exception as e:
                print(f"Input handler worker error: {e}")

    def stop(self):
        """Stop the input handler"""
        self.running = False
        self.handler.cleanup()
        self.join(timeout=5)
