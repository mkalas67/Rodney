"""
Run this once to authenticate the workspace account (marta@martakalas.com)
for GA4 read access on the Apartment Budapest properties.

Usage:
    D:/tools/kpi-venv/Scripts/python.exe setup_workspace_auth.py
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Desktop app client from forest-of-apartment-pages project (workspace account)
CLIENT_SECRET = Path("D:/DD/client_secret_539646520795-85p36lp2s52nh9nskjs9qssb5cm9bq6g.apps.googleusercontent.com.json")
OUTPUT = Path(__file__).parent / "credentials" / "workspace_adc.json"


def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=8086, open_browser=True)

    data = {
        "account": "marta@martakalas.com",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
        "type": "authorized_user",
        "universe_domain": "googleapis.com",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2))
    print(f"Workspace credentials saved to {OUTPUT}")


if __name__ == "__main__":
    main()
