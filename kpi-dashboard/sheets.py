"""Google Sheets writer for the KPI dashboard."""

from datetime import date

import gspread
from google.oauth2.credentials import Credentials


HEADER_ROW = [
    "Metric", "This Week", "Prev Week", "Change"
]

METRIC_LABELS = {
    "sessions": "Sessions",
    "activeUsers": "Active Users",
    "screenPageViews": "Pageviews",
    "newUsers": "New Users",
    "averageSessionDuration": "Avg Session Duration",
    "bounceRate": "Bounce Rate",
}


def get_or_create_sheet(creds: Credentials, sheet_id: str | None, sheet_name: str) -> gspread.Spreadsheet:
    gc = gspread.authorize(creds)
    if sheet_id:
        return gc.open_by_key(sheet_id)
    spreadsheet = gc.create(sheet_name)
    spreadsheet.share(None, perm_type="anyone", role="reader")
    print(f"Created sheet: {spreadsheet.url}")
    return spreadsheet


def get_or_create_tab(spreadsheet: gspread.Spreadsheet, tab_name: str) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=tab_name, rows=50, cols=10)


def write_property_tab(
    spreadsheet: gspread.Spreadsheet,
    tab_name: str,
    label: str,
    data: dict,
    updated: date,
):
    from ga4 import pct_change, format_duration

    ws = get_or_create_tab(spreadsheet, tab_name)
    ws.clear()

    rows = [
        [f"{label} — Weekly Traffic", "", "", ""],
        [f"Updated: {updated.strftime('%d %b %Y')}", "", "", ""],
        [],
        HEADER_ROW,
    ]

    this = data.get("this_week", {})
    prev = data.get("prev_week", {})

    for key, label_text in METRIC_LABELS.items():
        cur_raw = float(this.get(key, 0))
        prv_raw = float(prev.get(key, 0))

        if key == "averageSessionDuration":
            cur = format_duration(cur_raw)
            prv = format_duration(prv_raw)
        elif key == "bounceRate":
            cur = f"{cur_raw * 100:.1f}%"
            prv = f"{prv_raw * 100:.1f}%"
        else:
            cur = str(int(cur_raw))
            prv = str(int(prv_raw))

        change = pct_change(cur_raw, prv_raw)
        rows.append([label_text, cur, prv, change])

    ws.update("A1", rows)
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 13}})
    ws.format("A4:D4", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})


def write_summary_tab(
    spreadsheet: gspread.Spreadsheet,
    all_results: list[dict],
    updated: date,
):
    from ga4 import pct_change

    ws = get_or_create_tab(spreadsheet, "Summary")
    ws.clear()

    rows = [
        ["KPI Dashboard — All Projects", "", "", "", "", ""],
        [f"Updated: {updated.strftime('%d %b %Y')} (7-day rolling, vs prior 7 days)", "", "", "", "", ""],
        [],
        ["Project", "Sessions", "vs Prior Week", "Users", "Pageviews", "Bounce Rate"],
    ]

    for entry in all_results:
        this = entry["data"].get("this_week", {})
        prev = entry["data"].get("prev_week", {})
        sessions = int(float(this.get("sessions", 0)))
        sessions_prev = int(float(prev.get("sessions", 0)))
        users = int(float(this.get("activeUsers", 0)))
        pageviews = int(float(this.get("screenPageViews", 0)))
        bounce = float(this.get("bounceRate", 0))
        rows.append([
            entry["label"],
            sessions,
            pct_change(sessions, sessions_prev),
            users,
            pageviews,
            f"{bounce * 100:.1f}%",
        ])

    ws.update("A1", rows)
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
    ws.format("A4:F4", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.85, "green": 0.9, "blue": 0.95}})


def write_ab_summary_tab(
    spreadsheet: gspread.Spreadsheet,
    ab_results: list[dict],
    updated: date,
):
    from ga4 import pct_change

    ws = get_or_create_tab(spreadsheet, "AB Summary")
    ws.clear()

    rows = [
        ["Apartment Budapest — All Cities", "", "", "", "", ""],
        [f"Updated: {updated.strftime('%d %b %Y')} (7-day rolling, vs prior 7 days)", "", "", "", "", ""],
        [],
        ["City / Site", "Sessions", "vs Prior Week", "Users", "Pageviews", "Bounce Rate"],
    ]

    total_sessions = total_sessions_prev = total_users = total_pageviews = 0

    for entry in ab_results:
        this = entry["data"].get("this_week", {})
        prev = entry["data"].get("prev_week", {})
        sessions = int(float(this.get("sessions", 0)))
        sessions_prev = int(float(prev.get("sessions", 0)))
        users = int(float(this.get("activeUsers", 0)))
        pageviews = int(float(this.get("screenPageViews", 0)))
        bounce = float(this.get("bounceRate", 0))
        total_sessions += sessions
        total_sessions_prev += sessions_prev
        total_users += users
        total_pageviews += pageviews
        rows.append([
            entry["label"],
            sessions,
            pct_change(sessions, sessions_prev),
            users,
            pageviews,
            f"{bounce * 100:.1f}%",
        ])

    rows.append([])
    rows.append([
        "TOTAL",
        total_sessions,
        pct_change(total_sessions, total_sessions_prev),
        total_users,
        total_pageviews,
        "",
    ])

    ws.update("A1", rows)
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 13}})
    ws.format("A4:F4", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.95, "green": 0.9, "blue": 0.85}})
