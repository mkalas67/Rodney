"""Credential helpers for personal and workspace Google accounts."""

import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def load_credentials(adc_path: Path, scopes: list[str]) -> Credentials:
    """Load and refresh OAuth2 credentials from an ADC JSON file."""
    if not adc_path.exists():
        raise FileNotFoundError(
            f"Credentials not found: {adc_path}\n"
            "Run setup_auth.py to authenticate this account."
        )

    data = json.loads(adc_path.read_text())
    creds = Credentials(
        token=None,
        refresh_token=data["refresh_token"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes,
    )
    creds.refresh(Request())
    return creds
