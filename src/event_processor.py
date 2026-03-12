"""Event processor coordinating NFC reads and input handling.

State machine:
  IDLE → (card placed) → WAITING_INPUT → (key 1/2 or timeout) → WAIT_REMOVAL → (card removed) → IDLE
                                        → (key 3: 疑義照会)   → WAITING_PATIENT_NUM → (number entered) → WAIT_REMOVAL → IDLE

One card touch = exactly one record. No duplicates.
"""

import sys
import os
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict
from enum import Enum

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

# Special value that triggers patient number input
GIGI_SHOUKAI = "疑義照会"


class State(Enum):
    IDLE = "idle"                                # Waiting for card
    WAITING_INPUT = "waiting_input"              # Card detected, waiting for key 1/2/3
    WAITING_PATIENT_NUM = "waiting_patient_num"  # Key 3 pressed, waiting for patient number
    WAIT_REMOVAL = "wait_removal"                # Record saved, waiting for card removal


class EventProcessor:
    """Coordinates NFC reads, input handling, and Sheets API.
    Ensures exactly one record per card placement."""

    def __init__(self, credentials_file: str, callback: Optional[Callable] = None,
                 status_callback: Optional[Callable] = None):
        self.credentials_file = credentials_file
        self.ui_callback = callback
        self.status_callback = status_callback
        self.timeout_seconds = config.get("input.timeout_seconds", 5)
        self.default_value = config.get("input.default_on_timeout", "変更あり")

        # State machine
        self._state = State.IDLE
        self._state_lock = threading.Lock()

        # Current session data (one card touch = one session)
        self._session_uid = None
        self._session_timestamp = None
        self._timeout_timer = None

        # Flag: UI should show patient number dialog
        self._needs_patient_number = False

        # Workers
        self.nfc_worker = None
        self.input_worker = None
        self.sheets_worker = None

        self._start_workers()

    def _start_workers(self):
        """Start background worker threads"""
        try:
            self.nfc_worker = NFCReaderWorker(
                on_card_placed=self._on_card_placed,
                on_card_removed=self._on_card_removed,
            )
            self.nfc_worker.start()

            self.input_worker = InputHandlerWorker(callback=self._on_input)
            self.input_worker.start()

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

    @property
    def needs_patient_number(self) -> bool:
        """Check if UI needs to show patient number input dialog."""
        return self._needs_patient_number

    def submit_patient_number(self, patient_number: str):
        """Called by UI after patient number is entered.
        patient_number can be empty string if user cancelled."""
        with self._state_lock:
            self._needs_patient_number = False

            if self._state != State.WAITING_PATIENT_NUM:
                return  # State changed (e.g. card removed), ignore

            if not patient_number:
                # User cancelled — record without patient number
                notes = ""
            else:
                notes = f"患者番号: {patient_number}"

            print(f"⌨ Patient number entered: {patient_number or '(空)'}")
            self._record_and_transition(GIGI_SHOUKAI, notes=notes)

    def _on_card_placed(self, uid: str):
        """Called when a card is placed on the reader (once per placement)."""
        with self._state_lock:
            if self._state != State.IDLE:
                return

            self._state = State.WAITING_INPUT
            self._session_uid = uid
            self._session_timestamp = datetime.now()

        print(f"📱 [Session start] Card placed (UID: {uid[:8]}...)")
        self._notify_status("nfc_detected", uid)

        self._timeout_timer = threading.Timer(
            self.timeout_seconds, self._on_timeout
        )
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

    def _on_card_removed(self):
        """Called when the card is removed from the reader."""
        with self._state_lock:
            if self._state in (State.WAIT_REMOVAL,):
                self._state = State.IDLE
                self._session_uid = None
                self._session_timestamp = None
                print("📱 [Session end] Card removed → ready for next")
                self._notify_status("waiting")
            elif self._state == State.WAITING_INPUT:
                # Card removed while waiting — let timeout handle it
                print("📱 Card removed while waiting for input")
            elif self._state == State.WAITING_PATIENT_NUM:
                # Card removed during patient number input — that's OK, still wait for input
                print("📱 Card removed during patient number input (still waiting)")

    def _on_input(self, value: str):
        """Called when keyboard input (1, 2, or 3) is received."""
        with self._state_lock:
            if self._state != State.WAITING_INPUT:
                return

            # Cancel timeout
            if self._timeout_timer:
                self._timeout_timer.cancel()

            if value == GIGI_SHOUKAI:
                # Key 3: need patient number → transition to WAITING_PATIENT_NUM
                self._state = State.WAITING_PATIENT_NUM
                self._needs_patient_number = True
                print(f"⌨ Input received: {value} → waiting for patient number")
                self._notify_status("waiting_patient_number")
            else:
                # Key 1 or 2: record immediately
                print(f"⌨ Input received: {value}")
                self._notify_status("input_received")
                self._record_and_transition(value)

    def _on_timeout(self):
        """Called when input timeout expires."""
        with self._state_lock:
            if self._state != State.WAITING_INPUT:
                return

            print(f"⏱ Input timeout → using default: {self.default_value}")
            self._notify_status("timeout")
            self._record_and_transition(self.default_value)

    def _record_and_transition(self, input_value: str, notes: str = ""):
        """Record event to Sheets and transition state.
        MUST be called while holding _state_lock."""
        uid = self._session_uid
        timestamp = self._session_timestamp

        if not uid or not timestamp:
            self._state = State.IDLE
            return

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        content = "処方箋内容について確認"

        # Check if card is still present
        if self.nfc_worker and self.nfc_worker.card_present:
            self._state = State.WAIT_REMOVAL
        else:
            self._state = State.IDLE
            self._session_uid = None
            self._session_timestamp = None

        # Queue the Sheets write
        if self.sheets_worker:
            self.sheets_worker.add_row(
                timestamp=timestamp_str,
                content=content,
                change=input_value,
                notes=notes,
            )

        # Notify UI
        if self.ui_callback:
            self.ui_callback({
                "nfc_uid": uid,
                "timestamp": timestamp_str,
                "content": content,
                "change": input_value,
                "notes": notes,
            })

        print(f"✓ [Recorded] {timestamp_str} | {input_value} | {notes} | UID: {uid[:8]}...")

        if self._state == State.WAIT_REMOVAL:
            self._notify_status("wait_removal")
        else:
            self._notify_status("waiting")

    def get_status(self) -> Dict[str, str]:
        """Get current status of all components"""
        status = {
            "nfc": self.nfc_worker.reader.get_status()
            if self.nfc_worker
            else "✗ Not initialized",
            "state": self._state.value,
        }

        if self.input_worker:
            status.update(self.input_worker.handler.get_status())

        return status

    def start(self):
        """Start the event processor (event-driven via callbacks)"""
        pass

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
