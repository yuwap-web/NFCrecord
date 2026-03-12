"""NFC Reader support for SONY RC-380"""

import sys
import os
import threading
import time
from typing import Optional, Callable

# Fix module path for PyInstaller
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

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

    def is_card_present(self) -> Optional[str]:
        """Check if a card is on the reader.
        Returns UID string if card present, None if not.
        For FeliCa cards, UID may differ each read — that's OK,
        we only use this to detect presence/absence.
        """
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

                # APDU command to get UID
                apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                response, sw1, sw2 = connection.transmit(apdu)

                if sw1 == 0x90 and sw2 == 0x00:
                    uid = "".join([f"{byte:02x}" for byte in response])
                    return uid

                return None

        except Exception:
            # Any error means card is not (properly) present
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
    """Background worker thread for NFC reading.

    Uses state-based detection:
    - Detects card PRESENT (first successful read after absence)
    - Detects card REMOVED (first failed read after presence)
    - Only triggers callback ONCE per card placement
    """

    def __init__(self, on_card_placed: Optional[Callable] = None,
                 on_card_removed: Optional[Callable] = None):
        super().__init__(daemon=True)
        self.reader = NFCReader()
        self.on_card_placed = on_card_placed
        self.on_card_removed = on_card_removed
        self.running = True
        self.card_present = False
        self.poll_interval = config.get("nfc.poll_interval", 0.5)

    def run(self):
        """Main reader loop — state-based card detection"""
        print(f"NFC Reader worker started (poll interval: {self.poll_interval}s)")

        while self.running:
            try:
                uid = self.reader.is_card_present()

                if uid and not self.card_present:
                    # Card just placed on reader
                    self.card_present = True
                    print(f"📱 NFC card detected (UID: {uid[:8]}...)")
                    if self.on_card_placed:
                        self.on_card_placed(uid)

                elif not uid and self.card_present:
                    # Card just removed from reader
                    self.card_present = False
                    print("📱 NFC card removed")
                    if self.on_card_removed:
                        self.on_card_removed()

                time.sleep(self.poll_interval)

            except Exception as e:
                print(f"NFC Reader worker error: {e}")
                time.sleep(1)

    def stop(self):
        """Stop the reader thread"""
        self.running = False
        self.join(timeout=5)
