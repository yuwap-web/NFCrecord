"""Google Sheets API integration for NFC Sheets Logger"""

import threading
import queue
from typing import Optional, List
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient import discovery
import googleapiclient.errors

from config import config


class SheetsAPI:
    """Handles Google Sheets API operations"""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.service = None
        self.spreadsheet_id = config.get("google_sheets.spreadsheet_id")
        self.sheet_name = config.get("google_sheets.sheet_name")
        self._lock = threading.Lock()

        self._initialize_service()

    def _initialize_service(self) -> bool:
        """Initialize Google Sheets API service"""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=self.SCOPES
            )

            self.service = discovery.build(
                "sheets", "v4", credentials=credentials, cache_discovery=False
            )

            print(f"✓ Google Sheets API initialized")
            return True

        except Exception as e:
            print(f"✗ Failed to initialize Sheets API: {e}")
            return False

    def append_row(self, row_data: List[str]) -> bool:
        """Append a row to the spreadsheet"""
        if not self.service:
            print("Error: Sheets API not initialized")
            return False

        try:
            with self._lock:
                range_name = f"{self.sheet_name}!A:D"

                result = self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body={"values": [row_data]},
                ).execute()

            print(f"✓ Row appended: {row_data}")
            return True

        except googleapiclient.errors.HttpError as e:
            print(f"✗ Google Sheets API error: {e}")
            return False
        except Exception as e:
            print(f"✗ Error appending row: {e}")
            return False

    def create_headers(self) -> bool:
        """Create header row if it doesn't exist"""
        if not self.service:
            return False

        try:
            with self._lock:
                # Check if sheet exists
                sheet_metadata = self.service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()

                sheets = sheet_metadata.get("sheets", [])
                sheet_exists = any(
                    sheet["properties"]["title"] == self.sheet_name for sheet in sheets
                )

                if not sheet_exists:
                    # Create new sheet
                    requests = [
                        {
                            "addSheet": {
                                "properties": {
                                    "title": self.sheet_name,
                                }
                            }
                        }
                    ]

                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={"requests": requests},
                    ).execute()

                    print(f"✓ Created sheet: {self.sheet_name}")

                # Add headers
                headers = config.get("google_sheets.columns")
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1:D1",
                    valueInputOption="USER_ENTERED",
                    body={"values": [headers]},
                ).execute()

                print(f"✓ Headers created: {headers}")
                return True

        except Exception as e:
            print(f"✗ Error creating headers: {e}")
            return False


class SheetsAPIWorker(threading.Thread):
    """Background worker thread for Sheets API operations"""

    def __init__(self, credentials_file: str):
        super().__init__(daemon=True)
        self.credentials_file = credentials_file
        self.queue = queue.Queue()
        self.api = None
        self.running = True

    def run(self):
        """Main worker thread loop"""
        self.api = SheetsAPI(self.credentials_file)

        # Create headers on startup
        self.api.create_headers()

        while self.running:
            try:
                # Get row data from queue (blocking, timeout to allow shutdown)
                row_data = self.queue.get(timeout=1)

                if row_data is None:  # Shutdown signal
                    break

                # Append to sheets
                self.api.append_row(row_data)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")

    def add_row(self, timestamp: str, content: str, change: str, notes: str = ""):
        """Queue a row to be appended"""
        row_data = [timestamp, content, change, notes]
        self.queue.put(row_data)

    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.queue.put(None)  # Shutdown signal
        self.join(timeout=5)
