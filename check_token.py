"""Check what scopes the current Gmail token has."""
import json
import urllib.request
import urllib.parse

CREDS_FILE = r"C:\Users\marta\Rodney\gmail-credentials.json"
ACCOUNT = "gmail-opencpd"

def load_creds():
    with open(CREDS_FILE) as f:
        return json.load(f)

def refresh_access_token(creds):
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
        result = json.loads(resp.read())
        print("Token response keys:", list(result.keys()))
        if "scope" in result:
            print("Scopes:", result["scope"])
        return result["access_token"]

def check_tokeninfo(access_token):
    url = f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        info = json.loads(resp.read())
        print("\nToken info:")
        for k, v in info.items():
            print(f"  {k}: {v}")

creds = load_creds()
token = refresh_access_token(creds)
check_tokeninfo(token)
