"""
Run this once to authorise Google Sheets write access (personal account).
A browser will open — log in as academyforpetloss@gmail.com.

Usage:
    D:/tools/kpi-venv/Scripts/python.exe setup_sheets_auth.py
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

CLIENT_SECRET = Path("D:/DD/client_secret_371042218468-ot1db961f6vc8r63gt7u866a15fvu6c7.apps.googleusercontent.com.json")
OUTPUT = Path(__file__).parent / "credentials" / "sheets_adc.json"


def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=8087, open_browser=True)
    data = {
        "account": "academyforpetloss@gmail.com",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
        "type": "authorized_user",
        "universe_domain": "googleapis.com",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2))
    print(f"Sheets credentials saved to {OUTPUT}")


if __name__ == "__main__":
    main()
