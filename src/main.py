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

# Write debug log file next to the EXE
_debug_log_path = os.path.join(app_dir, "debug.log")
try:
    with open(_debug_log_path, "w", encoding="utf-8") as _f:
        _f.write(f"=== NFC Sheets Logger Debug Log ===\n")
        _f.write(f"Time: {datetime.now()}\n")
        _f.write(f"sys.frozen: {getattr(sys, 'frozen', False)}\n")
        _f.write(f"sys.executable: {sys.executable}\n")
        _f.write(f"app_dir: {app_dir}\n")
        _f.write(f"os.getcwd(): {os.getcwd()}\n")
        _config_path = os.path.join(app_dir, "config", "config.yaml")
        _cred_path = os.path.join(app_dir, "config", "credentials.json")
        _f.write(f"Expected config.yaml: {_config_path}\n")
        _f.write(f"  exists: {os.path.exists(_config_path)}\n")
        _f.write(f"Expected credentials.json: {_cred_path}\n")
        _f.write(f"  exists: {os.path.exists(_cred_path)}\n")
        # List files in app_dir
        _f.write(f"\nFiles in app_dir ({app_dir}):\n")
        for _item in os.listdir(app_dir):
            _full = os.path.join(app_dir, _item)
            _f.write(f"  {'[DIR]' if os.path.isdir(_full) else '[FILE]'} {_item}\n")
        _config_dir = os.path.join(app_dir, "config")
        if os.path.isdir(_config_dir):
            _f.write(f"\nFiles in config/ ({_config_dir}):\n")
            for _item in os.listdir(_config_dir):
                _f.write(f"  [FILE] {_item}\n")
        else:
            _f.write(f"\nconfig/ directory NOT FOUND at {_config_dir}\n")
except Exception:
    pass

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
        self._status_message = "起動中..."
        self._pending_uid = None
        self._show_patient_dialog = False

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
                status_callback=self._on_status_change,
            )

            # Start processing
            self.processor.start()

            return True

        except Exception as e:
            print(f"Error initializing: {e}")
            return False

    def create_layout(self):
        """Create the GUI layout"""
        layout = [
            [sg.Text(WINDOW_TITLE, font=("Arial", 16, "bold"))],
            [sg.HorizontalSeparator()],
            # Status area - large and prominent
            [
                sg.Text("状態:", font=("Arial", 12)),
                sg.Text("カード待機中...", key="-STATUS-", font=("Arial", 14, "bold"),
                         text_color="lime green", size=(30, 1)),
            ],
            [sg.HorizontalSeparator()],
            # Last entry
            [sg.Text("最後の記録:", font=("Arial", 11, "bold"))],
            [
                sg.Text("日時:", size=(8, 1)),
                sg.Text("---", key="-LAST-TIMESTAMP-", size=(25, 1)),
            ],
            [
                sg.Text("変更:", size=(8, 1)),
                sg.Text("---", key="-LAST-CHANGE-", font=("Arial", 12, "bold"),
                         size=(25, 1)),
            ],
            [sg.HorizontalSeparator()],
            # Log area
            [sg.Text("ログ:", font=("Arial", 11, "bold"))],
            [
                sg.Multiline(
                    size=(65, LOG_LINES),
                    key="-LOG-",
                    disabled=True,
                    autoscroll=True,
                    font=("Consolas", 9),
                )
            ],
            # Buttons
            [sg.Button("終了", key="-EXIT-", size=(10, 1))],
        ]

        return layout

    def _on_event(self, event_data):
        """Callback from event processor when NFC + input is processed"""
        timestamp = event_data.get("timestamp")
        content = event_data.get("content")
        change = event_data.get("change")
        nfc_uid = event_data.get("nfc_uid")
        notes = event_data.get("notes", "")

        # Add to log
        if notes:
            log_entry = f"[{timestamp}] {change} / {notes}"
        else:
            log_entry = f"[{timestamp}] {change}"
        self.log_entries.insert(0, log_entry)
        self.log_entries = self.log_entries[:LOG_LINES]

        print(f"Event recorded: {log_entry}")

    def _on_status_change(self, status: str, uid: str = None):
        """Callback for status changes from event processor"""
        if status == "nfc_detected":
            self._status_message = "📱 カード検出 → 入力待ち (1:変更あり / 2:変更なし / 3:疑義照会)"
        elif status == "waiting":
            self._status_message = "カード待機中..."
        elif status == "timeout":
            self._status_message = "⏱ タイムアウト → 変更ありで記録中..."
        elif status == "input_received":
            self._status_message = "⌨ 入力受付 → 記録中..."
        elif status == "wait_removal":
            self._status_message = "✓ 記録完了！ カードを取り外してください"
        elif status == "waiting_patient_number":
            self._status_message = "📝 疑義照会 → 患者番号を入力してください"
            self._show_patient_dialog = True

    def update_display(self):
        """Update all GUI elements"""
        if not self.window:
            return

        try:
            # Update status
            self.window["-STATUS-"].update(self._status_message)

            # Update status color
            if "待機中" in self._status_message:
                self.window["-STATUS-"].update(text_color="lime green")
            elif "入力待ち" in self._status_message:
                self.window["-STATUS-"].update(text_color="yellow")
            elif "取り外して" in self._status_message:
                self.window["-STATUS-"].update(text_color="cyan")
            elif "患者番号" in self._status_message:
                self.window["-STATUS-"].update(text_color="yellow")
            elif "タイムアウト" in self._status_message:
                self.window["-STATUS-"].update(text_color="orange")
            elif "記録中" in self._status_message:
                self.window["-STATUS-"].update(text_color="orange")

            # Update log
            log_text = "\n".join(self.log_entries)
            self.window["-LOG-"].update(log_text)

            # Update last entry
            if self.log_entries:
                first_log = self.log_entries[0]
                parts = first_log.split("] ", 1)
                if len(parts) == 2:
                    timestamp = parts[0].strip("[")
                    rest = parts[1]
                    change = rest.split("(")[0].strip()
                    self.window["-LAST-TIMESTAMP-"].update(timestamp)
                    self.window["-LAST-CHANGE-"].update(change)

        except Exception as e:
            print(f"Error updating display: {e}")

    def run(self):
        """Main UI event loop"""
        if not self.initialize():
            msg = (
                f"初期化に失敗しました。\n\n"
                f"EXE場所: {os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else '(スクリプト実行)'}\n"
                f"設定ファイル: {config.config_file}\n"
                f"設定ファイル存在: {config.config_file.exists()}\n"
                f"認証ファイル: {config.credentials_file}\n"
                f"認証ファイル存在: {config.credentials_file.exists()}\n"
                f"spreadsheet_id: {config.get('google_sheets.spreadsheet_id', '(未設定)')}\n\n"
                f"configフォルダをEXEと同じフォルダに配置してください。"
            )
            sg.popup_error(msg, title="設定エラー")
            return

        self.window = sg.Window(
            WINDOW_TITLE,
            self.create_layout(),
            size=(WINDOW_WIDTH, WINDOW_HEIGHT),
            finalize=True,
        )

        self._status_message = "カード待機中..."

        # Main event loop
        while True:
            event, values = self.window.read(timeout=300)

            if event == sg.WINDOW_CLOSED or event == "-EXIT-":
                break

            # Check if we need to show patient number dialog
            if self._show_patient_dialog:
                self._show_patient_dialog = False
                patient_number = sg.popup_get_text(
                    "患者番号を入力してください:",
                    title="疑義照会 — 患者番号入力",
                    default_text="",
                    font=("Arial", 12),
                )
                # patient_number is None if cancelled, "" if empty, or the entered text
                self.processor.submit_patient_number(patient_number or "")

            # Update display every 300ms
            self.update_display()

        # Cleanup
        self.processor.stop()
        self.window.close()


def main():
    """Main entry point"""
    app = NFCLoggerUI()
    app.run()


if __name__ == "__main__":
    main()
