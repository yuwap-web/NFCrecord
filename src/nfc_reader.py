"""NFC Reader support for SONY RC-380"""

import threading
import queue
from typing import Optional, Callable

try:
    from smartcard.System import readers
    from smartcard.Exceptions import SmartcardException
    HAS_SMARTCARD = True
except ImportError:
    HAS_SMARTCARD = False

from config import config


class NFCReader:
    """SONY RC-380 NFC Reader interface"""

    def __init__(self):
        self.reader_index = 0
        self.last_uid = None
        self._lock = threading.Lock()
        self._initialized = False

        if HAS_SMARTCARD:
            self._initialize()

    def _initialize(self) -> bool:
        """Initialize NFC reader connection"""
        try:
            reader_list = readers()

            if not reader_list:
                print("✗ No NFC readers found. Please connect SONY RC-380")
                return False

            print(f"✓ Found {len(reader_list)} NFC reader(s)")

            for i, reader in enumerate(reader_list):
                print(f"  [{i}] {reader}")

            self._initialized = True
            return True

        except Exception as e:
            print(f"✗ Error initializing NFC reader: {e}")
            return False

    def read_card(self) -> Optional[str]:
        """Read NFC card UID (non-blocking)"""
        if not HAS_SMARTCARD or not self._initialized:
            return None

        try:
            with self._lock:
                reader_list = readers()

                if not reader_list or len(reader_list) <= self.reader_index:
                    return None

                reader = reader_list[self.reader_index]
                connection = reader.createConnection()
                connection.connect()

                # SELECT command to get UID
                # This is a simplified example - actual implementation depends on card type
                apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                response, sw1, sw2 = connection.transmit(apdu)

                if sw1 == 0x90 and sw2 == 0x00:
                    uid = "".join([f"{byte:02x}" for byte in response])
                    return uid

                return None

        except Exception as e:
            # No card detected is normal, only log on other errors
            if "Card not present" not in str(e):
                print(f"NFC read error: {e}")
            return None

    def get_status(self) -> str:
        """Get reader connection status"""
        if not HAS_SMARTCARD:
            return "⚠ smartcard module not installed"

        if not self._initialized:
            return "✗ Not initialized"

        try:
            reader_list = readers()
            if not reader_list:
                return "✗ No readers found"

            return f"✓ Ready ({len(reader_list)} reader(s))"

        except Exception:
            return "✗ Error"


class NFCReaderWorker(threading.Thread):
    """Background worker thread for NFC reading"""

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__(daemon=True)
        self.reader = NFCReader()
        self.callback = callback
        self.running = True
        self.last_uid = None
        self.poll_interval = config.get("nfc.poll_interval", 0.5)

    def run(self):
        """Main reader loop"""
        import time

        print(f"NFC Reader worker started (poll interval: {self.poll_interval}s)")

        while self.running:
            try:
                uid = self.reader.read_card()

                # Only trigger callback on new card detection
                if uid and uid != self.last_uid:
                    self.last_uid = uid
                    if self.callback:
                        self.callback(uid)

                time.sleep(self.poll_interval)

            except Exception as e:
                print(f"NFC Reader worker error: {e}")
                import time

                time.sleep(1)

    def stop(self):
        """Stop the reader thread"""
        self.running = False
        self.join(timeout=5)
