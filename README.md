# NFC Sheets Logger

Automatic NFC card logging system that records card touches to Google Sheets with SONY RC-380 NFC card reader.

## Overview

This application monitors an NFC card reader (SONY RC-380) and automatically logs card touches to a Google Sheets spreadsheet. It supports both Stream Deck buttons and keyboard input for selecting additional information during logging.

### Use Case

This system is designed for logging phone inquiries about prescriptions at hospitals:
- When an NFC card is touched, the timestamp is automatically recorded
- User selects via Stream Deck or keyboard whether there was a change (1 key = change, 2 key = no change)
- Default action (5-second timeout) records as "change exists"

## System Requirements

- **Windows 10+** (for running the application)
- **Mac** (for development)
- **NFC Card Reader**: SONY RC-380
- **NFC Cards**: Standard NFC cards/tags
- **Google Account**: Personal account (gmail.com, etc.) - **Workspace NOT required**
  - Free tier: 1 million cells read/write per month
- **Optional**: Stream Deck (for button-based input)

## Installation

### 1. Development Setup (Mac)

```bash
# Clone repository
git clone https://github.com/yourusername/NFCrecord
cd NFCrecord

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Google Sheets API

```bash
# Run setup wizard
python setup/setup_credentials.py
```

This will:
1. Guide you through creating a Google Cloud service account
2. Download credentials JSON
3. Configure your Google Sheets spreadsheet ID
4. Generate configuration files

### 3. Windows Setup

Download the latest `NFCrecord.exe` from [GitHub Releases](https://github.com/yourusername/NFCrecord/releases)

Or build it yourself:
```bash
# On Windows
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --onefile --name NFCrecord src/main.py
```

### 4. SONY RC-380 Driver Installation

1. Download the SONY RC-380 driver for Windows
2. Install the driver
3. Connect RC-380 via USB

## Usage

### Starting the Application

**Mac (Development)**:
```bash
python src/main.py
```

**Windows**:
```bash
# Run the .exe file
NFCrecord.exe
```

### Recording a Log Entry

1. Touch NFC card to the reader
2. Within 5 seconds, press one of these:
   - **Key "1"** or **Stream Deck Button 1**: Record "変更あり" (Change exists)
   - **Key "2"** or **Stream Deck Button 2**: Record "変更なし" (No change)
   - **Wait 5 seconds**: Automatically records "変更あり" (default)
3. Entry is recorded to Google Sheets with timestamp

### Google Sheets Format

The spreadsheet logs include:

| 日時 | 問い合わせ内容 | 変更の有無 | 備考 |
|------|---|---|---|
| 2026-03-11 14:30 | 処方箋内容について確認 | 変更なし | |
| 2026-03-11 15:45 | 処方箋内容について確認 | 変更あり | |

## Configuration

Configuration file: `config/config.yaml`

```yaml
google_sheets:
  spreadsheet_id: "your-spreadsheet-id"
  sheet_name: "NFC Logs"
  columns:
    - 日時
    - 問い合わせ内容
    - 変更の有無
    - 備考

nfc:
  reader_name: "SONY RC-380"
  poll_interval: 0.5

input:
  key_mappings:
    "1": "変更あり"
    "2": "変更なし"
    "3": "タイムアウト"
  timeout_seconds: 5
  default_on_timeout: "変更あり"

gui:
  window_size: [600, 400]
  theme: "DarkBlue3"
  log_lines: 10
```

## Project Structure

```
NFCrecord/
├── src/
│   ├── main.py                 # Main UI entry point
│   ├── config.py               # Configuration management
│   ├── nfc_reader.py           # NFC reader interface
│   ├── sheets_api.py           # Google Sheets API
│   ├── input_handler.py        # Stream Deck + keyboard input
│   └── event_processor.py      # Event coordination
├── setup/
│   └── setup_credentials.py    # Setup wizard
├── config/
│   ├── credentials.json        # Google service account (NOT in git)
│   └── config.yaml             # Configuration
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
└── README.md                   # This file
```

## Troubleshooting

### NFC Reader Not Detected

```
⚠ No NFC readers found. Please connect SONY RC-380
```

- Check USB connection
- Verify driver installation
- Try different USB port

### Google Sheets API Error

```
✗ Failed to initialize Sheets API
```

- Verify `credentials.json` exists in `config/` directory
- Check spreadsheet ID is correct
- Ensure service account has access to the spreadsheet

### Stream Deck Not Detected

```
⚠ No Stream Deck device found
```

- Connect Stream Deck via USB
- Install Stream Deck software
- App will continue with keyboard input only

### Input Not Responding

- Ensure `config.yaml` contains valid key mappings
- For Windows: may need admin privileges for keyboard listener
- Try keyboard input (1, 2 keys) if Stream Deck is not available

## Development

### Running in Development Mode

```bash
source venv/bin/activate
python src/main.py
```

### Running Tests

```bash
python -m pytest tests/
```

### Building Windows EXE Locally

```bash
pip install pyinstaller
pyinstaller --onefile --name NFCrecord src/main.py
```

The EXE will be in `dist/NFCrecord.exe`

## Architecture

The application uses a multi-threaded architecture:

```
┌─────────────────────────────┐
│   Main UI Thread            │
│  (PySimpleGUI Window)       │
└──────────┬──────────────────┘
           │
      ┌────┴──────┬──────────┐
      ▼           ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│NFC       │ │Input     │ │Sheets    │
│Reader    │ │Handler   │ │API       │
│Thread    │ │Thread    │ │Thread    │
└─────┬────┘ └────┬─────┘ └──────────┘
      │           │
      └─────┬─────┘
            ▼
      ┌────────────────┐
      │Event Processor │
      │(Coordinator)   │
      └────────────────┘
```

## Security Considerations

- `credentials.json` is never committed to git (listed in .gitignore)
- Service account permissions are limited to specific Sheets
- Keyboard input requires no special permissions
- Stream Deck integration is optional

## License

MIT License

## Support

For issues or feature requests, please create an issue on [GitHub](https://github.com/yourusername/NFCrecord/issues)

## Author

Your Name <your.email@example.com>

## Changelog

### v0.1.0 (2026-03-11)
- Initial release
- NFC card reading support
- Google Sheets logging
- Stream Deck + keyboard input
- Windows executable via GitHub Actions
