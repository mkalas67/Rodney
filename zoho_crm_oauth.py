"""
OAuth flow for Zoho CRM — saves refresh token to credentials.json as ZOHO_CRM_REFRESH_TOKEN.
"""
import json
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
import http.server
import threading

CREDS_FILE = r"C:\Users\marta\Rodney\credentials.json"

SCOPES = ",".join([
    "ZohoCRM.modules.ALL",
    "ZohoCRM.settings.ALL",
    "ZohoCRM.bulk.ALL",
    "ZohoMail.messages.CREATE",
    "ZohoMail.accounts.READ",
])

REDIRECT_URI = "http://localhost:8080/callback"
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
        pass

def main():
    with open(CREDS_FILE) as f:
        creds_data = json.load(f)
    creds = creds_data["env"]

    client_id = creds["ZOHO_CLIENT_ID"]
    client_secret = creds["ZOHO_CLIENT_SECRET"]

    auth_url = (
        "https://accounts.zoho.eu/oauth/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    server = http.server.HTTPServer(("localhost", 8080), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    print("Opening browser for Zoho CRM authorisation...")
    print(f"If it doesn't open, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)

    thread.join(timeout=120)
    server.server_close()

    if not auth_code:
        print("ERROR: No authorisation code received.")
        return

    print("Got code. Exchanging for tokens...")

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": auth_code,
    }).encode()

    req = urllib.request.Request(
        "https://accounts.zoho.eu/oauth/v2/token",
        data=data, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())

    print("Response:", {k: v for k, v in tokens.items() if k != "access_token"})

    if "refresh_token" not in tokens:
        print("ERROR: No refresh token returned. Full response:", tokens)
        return

    creds_data["env"]["ZOHO_CRM_REFRESH_TOKEN"] = tokens["refresh_token"]
    with open(CREDS_FILE, "w") as f:
        json.dump(creds_data, f, indent=2)

    print("Saved ZOHO_CRM_REFRESH_TOKEN to credentials.json")
    print("Done — Zoho CRM API access is ready.")

if __name__ == "__main__":
    main()
