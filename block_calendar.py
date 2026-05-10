"""
List calendars and block 2pm-6pm BST on 2026-05-11 with title 'Travel'.
"""
import json
import urllib.request
import urllib.parse
import urllib.error

CREDS_FILE = r"C:\Users\marta\Rodney\gmail-credentials.json"
ACCOUNT = "gmail-opencpd"

def load_creds():
    with open(CREDS_FILE) as f:
        return json.load(f)

def get_token(creds):
    account = creds["accounts"][ACCOUNT]
    client = creds["gcp_oauth_client"]
    data = urllib.parse.urlencode({
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": account["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]

def cal_get(token, path, params=None):
    url = f"https://www.googleapis.com/calendar/v3/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def cal_post(token, path, body_dict):
    url = f"https://www.googleapis.com/calendar/v3/{path}"
    body = json.dumps(body_dict).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                  headers={"Authorization": f"Bearer {token}",
                                           "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def main():
    creds = load_creds()
    token = get_token(creds)
    print("Got token.\n")

    # List calendars
    data, err = cal_get(token, "users/me/calendarList")
    if err:
        print("Error listing calendars:", err)
        return

    print("Calendars found:")
    calendars = data.get("items", [])
    for cal in calendars:
        primary = " [PRIMARY]" if cal.get("primary") else ""
        print(f"  {cal['id']}{primary}")
        print(f"    Name: {cal.get('summary', 'N/A')}")

    # Use primary calendar (marta@open-cpd.com) — "Open CPD Demo" is for demos only
    target_cal = None
    for cal in calendars:
        if cal.get("primary"):
            target_cal = cal
            break
    if not target_cal:
        target_cal = calendars[0]

    print(f"\nUsing calendar: '{target_cal.get('summary')}' ({target_cal['id']})")

    # Create event: 2026-05-11 14:00-18:00 BST (Europe/London)
    event = {
        "summary": "Travel",
        "start": {
            "dateTime": "2026-05-11T14:00:00",
            "timeZone": "Europe/London"
        },
        "end": {
            "dateTime": "2026-05-11T18:00:00",
            "timeZone": "Europe/London"
        },
        "status": "confirmed",
        "transparency": "opaque"  # marks as busy/blocking
    }

    result, err = cal_post(token, f"calendars/{urllib.parse.quote(target_cal['id'])}/events", event)
    if err:
        print("Error creating event:", err)
    else:
        print(f"\nEvent created: {result.get('summary')}")
        print(f"Start: {result['start'].get('dateTime')}")
        print(f"End:   {result['end'].get('dateTime')}")
        print(f"Link:  {result.get('htmlLink')}")

if __name__ == "__main__":
    main()
