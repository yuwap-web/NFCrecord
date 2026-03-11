"""Setup script for Google Sheets API credentials"""

import os
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
EXAMPLE_CREDENTIALS = CONFIG_DIR / "credentials.json"
EXAMPLE_CONFIG = CONFIG_DIR / "example_config.yaml"


def setup_credentials():
    """Interactive setup for Google Sheets API credentials"""

    print("=" * 60)
    print("NFC Sheets Logger - Setup Wizard")
    print("=" * 60)
    print()

    # Create config directory
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Credentials file
    print("Step 1: Google Sheets API Credentials")
    print("-" * 60)
    print(
        "You need to create a service account on Google Cloud Console."
    )
    print("Follow these steps:")
    print("  1. Go to https://console.cloud.google.com/")
    print("  2. Create a new project")
    print("  3. Enable the Sheets API")
    print("  4. Create a Service Account")
    print("  5. Create a JSON key for the service account")
    print("  6. Download the JSON key file")
    print()

    credentials_path = None
    while not credentials_path:
        input_path = input("Enter the path to your credentials.json file: ").strip()

        if not input_path:
            print("Error: Path cannot be empty")
            continue

        input_path = Path(input_path).expanduser()

        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            continue

        # Validate JSON
        try:
            with open(input_path, "r") as f:
                creds = json.load(f)

            if "type" not in creds or creds["type"] != "service_account":
                print("Error: Invalid service account credentials file")
                continue

            credentials_path = input_path
            print(f"✓ Credentials file loaded successfully")

        except json.JSONDecodeError:
            print("Error: Invalid JSON file")
            continue

    # Copy credentials to config directory
    dest_path = CONFIG_DIR / "credentials.json"
    shutil.copy(credentials_path, dest_path)
    print(f"✓ Credentials saved to {dest_path}")
    print()

    # Step 2: Spreadsheet ID
    print("Step 2: Google Sheets Spreadsheet ID")
    print("-" * 60)
    print(
        "Enter the ID of your Google Sheets document."
    )
    print(
        "You can find it in the URL: "
        "https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/..."
    )
    print()

    spreadsheet_id = None
    while not spreadsheet_id:
        spreadsheet_id = input("Enter the Spreadsheet ID: ").strip()

        if not spreadsheet_id:
            print("Error: ID cannot be empty")
            spreadsheet_id = None
            continue

    print(f"✓ Spreadsheet ID: {spreadsheet_id}")
    print()

    # Step 3: Create config file
    print("Step 3: Creating Configuration")
    print("-" * 60)

    config_data = {
        "google_sheets": {
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": "NFC Logs",
            "columns": ["日時", "問い合わせ内容", "変更の有無", "備考"],
        },
        "nfc": {
            "reader_name": "SONY RC-380",
            "poll_interval": 0.5,
        },
        "input": {
            "key_mappings": {
                "1": "変更あり",
                "2": "変更なし",
                "3": "タイムアウト",
            },
            "timeout_seconds": 5,
            "default_on_timeout": "変更あり",
        },
        "gui": {
            "window_size": [600, 400],
            "theme": "DarkBlue3",
            "log_lines": 10,
        },
    }

    config_path = CONFIG_DIR / "config.yaml"

    try:
        import yaml

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

        print(f"✓ Configuration saved to {config_path}")

    except ImportError:
        print("⚠ PyYAML not installed. Saving as JSON instead.")
        config_path = CONFIG_DIR / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Configuration saved to {config_path}")

    print()

    # Step 4: Share spreadsheet with service account
    print("Step 4: Share Spreadsheet with Service Account")
    print("-" * 60)
    print(
        "You must share your Google Sheets with the service account email."
    )
    print()

    try:
        with open(CONFIG_DIR / "credentials.json", "r") as f:
            creds = json.load(f)
            service_account_email = creds.get("client_email", "")
            print(f"Service Account Email: {service_account_email}")
            print()
            print("Steps:")
            print("  1. Open your Google Sheets document")
            print("  2. Click 'Share' button")
            print(f"  3. Enter this email: {service_account_email}")
            print("  4. Grant 'Editor' permission")
            print("  5. Click 'Share'")

    except Exception as e:
        print(f"Error reading credentials: {e}")

    print()

    # Summary
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Share the Google Sheets with the service account (see above)")
    print("2. Run the application: python src/main.py")
    print()


if __name__ == "__main__":
    try:
        setup_credentials()
    except KeyboardInterrupt:
        print("\n⚠ Setup cancelled by user")
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
