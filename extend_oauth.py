"""
Re-run OAuth for gmail-opencpd account with Gmail + Calendar scopes.
Opens browser, catches callback on localhost:8080, saves new refresh token.
"""
import json
import urllib.request
import urllib.parse
import webbrowser
import http.server
import threading

CREDS_FILE = r"C:\Users\marta\Rodney\gmail-credentials.json"
ACCOUNT = "gmail-opencpd"

SCOPES = " ".join([
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.metadata",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
])

auth_code = None

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorised. You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received.")

    def log_message(self, format, *args):
        pass  # suppress server logs

def main():
    with open(CREDS_FILE) as f:
        creds = json.load(f)

    client = creds["gcp_oauth_client"]
    client_id = client["client_id"]
    client_secret = client["client_secret"]
    redirect_uri = client["redirect_uri"]

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",  # forces new refresh token
            "login_hint": creds["accounts"][ACCOUNT]["email"],
        })
    )

    # Start local server to catch callback
    server = http.server.HTTPServer(("localhost", 8080), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    print("Opening browser for Google authorisation...")
    print(f"If it doesn't open automatically, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)

    thread.join(timeout=120)
    server.server_close()

    if not auth_code:
        print("ERROR: No authorisation code received within 2 minutes.")
        return

    print("Got authorisation code. Exchanging for tokens...")

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code": auth_code,
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())

    if "refresh_token" not in tokens:
        print("ERROR: No refresh token in response:", tokens)
        return

    new_refresh = tokens["refresh_token"]
    print(f"New refresh token received.")

    # Save to credentials file
    creds["accounts"][ACCOUNT]["refresh_token"] = new_refresh
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

    print(f"Saved to {CREDS_FILE}")
    print("\nDone. Calendar scope is now active for the gmail-opencpd account.")

if __name__ == "__main__":
    main()
