"""
KPI Dashboard — nightly refresh script.

Pulls 7-day rolling GA4 traffic for all projects and writes to Google Sheet.
Run nightly via Windows Task Scheduler.
"""

import sys
from datetime import date
from pathlib import Path

# Ensure local modules resolve correctly when run from any directory
sys.path.insert(0, str(Path(__file__).parent))

from config import PROPERTIES, PERSONAL_ADC, SHEETS_ADC, WORKSPACE_ADC, GA4_SCOPES, SHEETS_SCOPES, SHEET_ID, SHEET_NAME
from auth import load_credentials
from ga4 import make_client, fetch_weekly_metrics
from sheets import get_or_create_sheet, write_property_tab, write_summary_tab, write_ab_summary_tab


def run():
    today = date.today()
    print(f"KPI refresh starting — {today.strftime('%d %b %Y')}")

    # Load credentials
    print("Loading credentials...")
    personal_creds = load_credentials(PERSONAL_ADC, GA4_SCOPES)

    try:
        personal_sheets_creds = load_credentials(SHEETS_ADC, SHEETS_SCOPES)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run setup_sheets_auth.py first, then retry.")
        sys.exit(1)

    try:
        workspace_creds = load_credentials(WORKSPACE_ADC, GA4_SCOPES)
    except FileNotFoundError as e:
        print(f"WARNING: {e}")
        print("Workspace (AB) properties will be skipped until credentials are set up.")
        workspace_creds = None

    personal_client = make_client(personal_creds)
    workspace_client = make_client(workspace_creds) if workspace_creds else None

    # Fetch GA4 data for all properties
    all_results = []
    ab_results = []

    for prop in PROPERTIES:
        account = prop["account"]
        client = personal_client if account == "personal" else workspace_client

        if client is None:
            print(f"  SKIP {prop['label']} (no workspace credentials)")
            continue

        print(f"  Fetching {prop['label']} (property {prop['id']})...")
        try:
            data = fetch_weekly_metrics(client, prop["id"])
            entry = {"label": prop["label"], "tab": prop["tab"], "data": data, "group": prop["group"]}
            all_results.append(entry)
            if prop["group"] == "apartment":
                ab_results.append(entry)
        except Exception as exc:
            print(f"  ERROR {prop['label']}: {exc}")

    if not all_results:
        print("No data fetched. Exiting.")
        sys.exit(1)

    # Write to Google Sheet — use personal credentials for sheet access
    print("Writing to Google Sheet...")
    spreadsheet = get_or_create_sheet(personal_sheets_creds, SHEET_ID, SHEET_NAME)

    # Summary tab first
    write_summary_tab(spreadsheet, all_results, today)
    print("  Written: Summary")

    # AB summary if we have AB data
    if ab_results:
        write_ab_summary_tab(spreadsheet, ab_results, today)
        print("  Written: AB Summary")

    # Individual property tabs
    for entry in all_results:
        write_property_tab(spreadsheet, entry["tab"], entry["label"], entry["data"], today)
        print(f"  Written: {entry['tab']}")

    print(f"\nDone. Sheet: {spreadsheet.url}")
    if not SHEET_ID:
        print(f"\nFirst run — sheet created. Add this to config.py:")
        print(f'  SHEET_ID = "{spreadsheet.id}"')


if __name__ == "__main__":
    run()
