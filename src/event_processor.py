"""Event processor coordinating NFC reads and input handling"""

import sys
import os
import threading
import queue
import time
from datetime import datetime
from typing import Optional, Callable, Dict

# Fix module path for PyInstaller
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from config import config
from nfc_reader import NFCReaderWorker
from input_handler import InputHandlerWorker
from sheets_api import SheetsAPIWorker


class EventProcessor:
    """Coordinates NFC reads, input handling, and Sheets API"""

    def __init__(self, credentials_file: str, callback: Optional[Callable] = None,
                 status_callback: Optional[Callable] = None):
        self.credentials_file = credentials_file
        self.ui_callback = callback
        self.status_callback = status_callback
        self.timeout_seconds = config.get("input.timeout_seconds", 5)
        self.default_value = config.get("input.default_on_timeout", "変更あり")

        # State management
        self.pending_nfc = None
        self.pending_timestamp = None
        self.input_value = None
        self.input_ready = threading.Event()
        self._lock = threading.Lock()
        self._timeout_timer = None

        # Workers
        self.nfc_worker = None
        self.input_worker = None
        self.sheets_worker = None

        # Start workers
        self._start_workers()

    def _start_workers(self):
        """Start background worker threads"""
        try:
            # Start NFC reader
            self.nfc_worker = NFCReaderWorker(callback=self._on_nfc_read)
            self.nfc_worker.start()

            # Start input handler
            self.input_worker = InputHandlerWorker(callback=self._on_input)
            self.input_worker.start()

            # Start Sheets API worker
            self.sheets_worker = SheetsAPIWorker(self.credentials_file)
            self.sheets_worker.start()

            print("✓ All workers started")

        except Exception as e:
            print(f"✗ Error starting workers: {e}")

    def _notify_status(self, status: str, uid: str = None):
        """Notify UI of status change"""
        if self.status_callback:
            try:
                self.status_callback(status, uid)
            except Exception:
                pass

    def _on_nfc_read(self, uid: str):
        """Callback when NFC card is read"""
        with self._lock:
            # Cancel any existing timer
            if self._timeout_timer:
                self._timeout_timer.cancel()

            self.pending_nfc = uid
            self.pending_timestamp = datetime.now()
            self.input_value = None
            self.input_ready.clear()

        print(f"📱 NFC card detected: {uid}")
        self._notify_status("nfc_detected", uid)

        # Start timeout timer
        self._timeout_timer = threading.Timer(
            self.timeout_seconds, self._on_input_timeout
        )
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

    def _on_input(self, value: str):
        """Callback when input (Stream Deck or keyboard) is received"""
        with self._lock:
            if self.pending_nfc is None:
                return  # No pending NFC read

            # Cancel timeout timer
            if self._timeout_timer:
                self._timeout_timer.cancel()

            self.input_value = value
            self.input_ready.set()

        print(f"⌨ Input received: {value}")
        self._notify_status("input_received")

    def _on_input_timeout(self):
        """Handle input timeout - use default value"""
        with self._lock:
            if self.pending_nfc is None:
                return  # Already processed

            if not self.input_ready.is_set():
                self.input_value = self.default_value
                print(f"⏱ Input timeout - using default: {self.default_value}")
                self._notify_status("timeout")

            self.input_ready.set()

    def _process_nfc(self):
        """Main processing loop for NFC events"""
        while True:
            with self._lock:
                if self.pending_nfc is None or not self.input_ready.is_set():
                    pass  # Nothing to process yet
                else:
                    # Process the pending NFC + input
                    nfc_uid = self.pending_nfc
                    timestamp = self.pending_timestamp
                    input_value = self.input_value or self.default_value

                    # Reset pending state
                    self.pending_nfc = None
                    self.pending_timestamp = None
                    self.input_value = None
                    self.input_ready.clear()

                    # Do the actual work outside the lock
                    self._record_event(nfc_uid, timestamp, input_value)

            time.sleep(0.1)

    def _record_event(self, nfc_uid: str, timestamp, input_value: str):
        """Record a completed event to Sheets and notify UI"""
        # Format timestamp
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        content = "処方箋内容について確認"

        # Add to Sheets queue
        if self.sheets_worker:
            self.sheets_worker.add_row(
                timestamp=timestamp_str,
                content=content,
                change=input_value,
                notes="",
            )

        # Notify UI callback
        if self.ui_callback:
            self.ui_callback(
                {
                    "nfc_uid": nfc_uid,
                    "timestamp": timestamp_str,
                    "content": content,
                    "change": input_value,
                }
            )

    def get_status(self) -> Dict[str, str]:
        """Get current status of all components"""
        status = {
            "nfc": self.nfc_worker.reader.get_status()
            if self.nfc_worker
            else "✗ Not initialized",
        }

        if self.input_worker:
            status.update(self.input_worker.handler.get_status())

        return status

    def start(self):
        """Start the main processing loop"""
        processing_thread = threading.Thread(target=self._process_nfc, daemon=True)
        processing_thread.start()

    def stop(self):
        """Stop all workers"""
        if self._timeout_timer:
            self._timeout_timer.cancel()

        if self.nfc_worker:
            self.nfc_worker.stop()

        if self.input_worker:
            self.input_worker.stop()

        if self.sheets_worker:
            self.sheets_worker.stop()

        print("✓ Event processor stopped")
