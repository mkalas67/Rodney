"""
Find email from rhoda@profskillsportal.com by scanning inbox metadata.
Workaround for Workspace metadata-only restriction on 'q' search.
"""
import json
import urllib.request
import urllib.parse
import urllib.error
import base64

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

def gmail_get(token, path, params=None):
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def get_header(headers_list, name):
    for h in headers_list:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""

def decode_body(payload):
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    elif mime == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            # Strip basic HTML tags for readability
            import re
            text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            return text.strip()
    elif mime.startswith("multipart/"):
        # Prefer plain text
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                result = decode_body(part)
                if result:
                    return result
        # Fall back to HTML
        for part in payload.get("parts", []):
            result = decode_body(part)
            if result:
                return result
    return ""

def main():
    creds = load_creds()
    token = get_token(creds)
    print("Got access token. Scanning inbox for rhoda@profskillsportal.com...\n")

    target = "rhoda@profskillsportal.com"
    page_token = None
    found_ids = []
    pages_checked = 0

    while pages_checked < 20:  # limit to ~1000 messages
        params = {"maxResults": 50, "labelIds": "INBOX"}
        if page_token:
            params["pageToken"] = page_token

        data, err = gmail_get(token, "messages", params)
        if err:
            print("Error listing messages:", err)
            break

        messages = data.get("messages", [])
        pages_checked += 1
        print(f"Page {pages_checked}: checking {len(messages)} messages...")

        for msg in messages:
            meta, err = gmail_get(token, f"messages/{msg['id']}", {"format": "metadata", "metadataHeaders": "From"})
            if err or not meta:
                continue
            headers = meta.get("payload", {}).get("headers", [])
            from_val = get_header(headers, "From")
            if target.lower() in from_val.lower():
                found_ids.append(msg["id"])
                print(f"  FOUND: id={msg['id']} from={from_val}")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    if not found_ids:
        # Also check ALL mail, not just inbox
        print("\nNot found in INBOX. Checking all mail (no label filter)...")
        params = {"maxResults": 50}
        data, err = gmail_get(token, "messages", params)
        if not err:
            for msg in data.get("messages", [])[:100]:
                meta, err = gmail_get(token, f"messages/{msg['id']}", {"format": "metadata", "metadataHeaders": "From"})
                if err or not meta:
                    continue
                headers = meta.get("payload", {}).get("headers", [])
                from_val = get_header(headers, "From")
                if target.lower() in from_val.lower():
                    found_ids.append(msg["id"])
                    print(f"  FOUND: id={msg['id']} from={from_val}")

    if not found_ids:
        print(f"\nNo emails found from {target}")
        return

    print(f"\nFetching full content of {len(found_ids)} email(s)...\n")

    for msg_id in found_ids:
        full, err = gmail_get(token, f"messages/{msg_id}", {"format": "full"})
        if err:
            print(f"Could not fetch full message {msg_id}: {err}")
            continue

        headers = full.get("payload", {}).get("headers", [])
        body = decode_body(full.get("payload", {}))
        thread_id = full.get("threadId")

        print("=" * 60)
        print(f"MESSAGE ID: {msg_id}")
        print(f"THREAD ID:  {thread_id}")
        print(f"FROM:    {get_header(headers, 'From')}")
        print(f"TO:      {get_header(headers, 'To')}")
        print(f"DATE:    {get_header(headers, 'Date')}")
        print(f"SUBJECT: {get_header(headers, 'Subject')}")
        print("=" * 60)
        print("\nBODY:\n")
        print(body[:3000])
        if len(body) > 3000:
            print(f"\n[...truncated, {len(body)} chars total]")

        # Check for drafts in the same thread
        print(f"\nChecking for drafts in thread {thread_id}...")
        drafts_data, err = gmail_get(token, "drafts", {"maxResults": 20})
        if not err:
            for d in drafts_data.get("drafts", []):
                d_detail, _ = gmail_get(token, f"drafts/{d['id']}")
                if d_detail and d_detail.get("message", {}).get("threadId") == thread_id:
                    d_msg_id = d_detail["message"]["id"]
                    d_full, _ = gmail_get(token, f"messages/{d_msg_id}", {"format": "full"})
                    if d_full:
                        d_body = decode_body(d_full.get("payload", {}))
                        d_headers = d_full.get("payload", {}).get("headers", [])
                        print(f"\nDRAFT FOUND (draft id: {d['id']})")
                        print(f"SUBJECT: {get_header(d_headers, 'Subject')}")
                        print("\nDRAFT BODY:\n")
                        print(d_body)

if __name__ == "__main__":
    main()
