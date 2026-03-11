"""Main UI for NFC Sheets Logger using FreeSimpleGUI"""

import sys
import os
import threading
from pathlib import Path
from datetime import datetime

# Fix module path for PyInstaller
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    app_dir = os.path.dirname(sys.executable)
else:
    # Running as script
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

import FreeSimpleGUI as sg

from config import config
from event_processor import EventProcessor

# Configure theme
sg.theme(config.get("gui.theme", "DarkBlue3"))

# Constants
WINDOW_TITLE = "NFC Sheets Logger"
WINDOW_WIDTH, WINDOW_HEIGHT = config.get("gui.window_size", (600, 400))
LOG_LINES = config.get("gui.log_lines", 10)


class NFCLoggerUI:
    """Main UI for NFC Sheets Logger"""

    def __init__(self):
        self.processor = None
        self.log_entries = []
        self.window = None

    def initialize(self) -> bool:
        """Initialize the UI and event processor"""
        try:
            # Validate configuration
            if not config.validate():
                print("Configuration validation failed. Please run setup_credentials.py first.")
                return False

            # Create event processor
            credentials_file = str(config.credentials_file)
            self.processor = EventProcessor(
                credentials_file=credentials_file,
                callback=self._on_event,
            )

            # Start processing
            self.processor.start()

            return True

        except Exception as e:
            print(f"Error initializing: {e}")
            return False

    def create_layout(self):
        """Create the GUI layout"""
        status_layout = [
            [
                sg.Text("Status:"),
                sg.Text("Initializing...", key="-STATUS-", text_color="yellow"),
            ],
            [sg.Multiline(size=(60, 5), key="-STATUS-DETAIL-", disabled=True)],
        ]

        log_layout = [
            [sg.Text("Recent Logs:")],
            [
                sg.Multiline(
                    size=(60, LOG_LINES),
                    key="-LOG-",
                    disabled=True,
                    text_color="white",
                )
            ],
        ]

        last_entry_layout = [
            [sg.Text("Last Entry:")],
            [
                sg.Text("Timestamp:", font=("Arial", 10, "bold")),
                sg.Text("--:--:--", key="-LAST-TIMESTAMP-"),
            ],
            [
                sg.Text("Content:", font=("Arial", 10, "bold")),
                sg.Text("---", key="-LAST-CONTENT-"),
            ],
            [
                sg.Text("Change:", font=("Arial", 10, "bold")),
                sg.Text("---", key="-LAST-CHANGE-"),
            ],
        ]

        button_layout = [
            [sg.Button("Refresh", key="-REFRESH-"), sg.Button("Exit", key="-EXIT-")]
        ]

        layout = [
            [sg.Text(WINDOW_TITLE, font=("Arial", 16, "bold"))],
            [sg.Column(status_layout)],
            [sg.Column(log_layout)],
            [sg.Column(last_entry_layout)],
            [sg.Column(button_layout)],
        ]

        return layout

    def _on_event(self, event_data):
        """Callback from event processor when NFC + input is processed"""
        timestamp = event_data.get("timestamp")
        content = event_data.get("content")
        change = event_data.get("change")
        nfc_uid = event_data.get("nfc_uid")

        # Add to log
        log_entry = f"[{timestamp}] {content} → {change} (UID: {nfc_uid[:8]}...)"
        self.log_entries.insert(0, log_entry)
        self.log_entries = self.log_entries[:LOG_LINES]

        print(f"Event recorded: {log_entry}")

    def update_status(self):
        """Update status information"""
        if not self.processor:
            return

        try:
            status = self.processor.get_status()

            # Format status text
            status_text = ""
            for component, state in status.items():
                status_text += f"{component}: {state}\n"

            # Update window
            if self.window:
                self.window["-STATUS-DETAIL-"].update(status_text)

        except Exception as e:
            print(f"Error updating status: {e}")

    def update_logs(self):
        """Update log display"""
        if self.window:
            log_text = "\n".join(self.log_entries)
            self.window["-LOG-"].update(log_text)

    def update_last_entry(self, timestamp, content, change):
        """Update last entry display"""
        if self.window:
            self.window["-LAST-TIMESTAMP-"].update(timestamp)
            self.window["-LAST-CONTENT-"].update(content)
            self.window["-LAST-CHANGE-"].update(change)

    def run(self):
        """Main UI event loop"""
        if not self.initialize():
            sg.popup_error("Failed to initialize. Check configuration.")
            return

        self.window = sg.Window(
            WINDOW_TITLE,
            self.create_layout(),
            size=(WINDOW_WIDTH, WINDOW_HEIGHT),
            finalize=True,
        )

        # Initial status update
        self.update_status()

        # Main event loop
        while True:
            event, values = self.window.read(timeout=500)

            if event == sg.WINDOW_CLOSED or event == "-EXIT-":
                break

            if event == "-REFRESH-":
                self.update_status()

            # Periodic updates
            self.update_logs()

            # Update last entry if we have logs
            if self.log_entries:
                first_log = self.log_entries[0]
                # Parse log entry
                parts = first_log.split("] ", 1)
                if len(parts) == 2:
                    timestamp = parts[0].strip("[")
                    rest = parts[1]
                    # Extract components
                    if "→" in rest:
                        content_part, change_part = rest.split("→", 1)
                        content = content_part.strip()
                        change = change_part.split("(")[0].strip()
                        self.update_last_entry(timestamp, content, change)

        # Cleanup
        self.processor.stop()
        self.window.close()


def main():
    """Main entry point"""
    app = NFCLoggerUI()
    app.run()


if __name__ == "__main__":
    main()
