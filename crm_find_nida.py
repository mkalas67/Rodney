"""
Find Dr Nida in Zoho CRM and read recent activity/notes.
"""
import json
import urllib.request
import urllib.parse
import urllib.error

CREDS_FILE = r"C:\Users\marta\Rodney\credentials.json"

def load_creds():
    with open(CREDS_FILE) as f:
        return json.load(f)["env"]

def get_token(creds):
    data = urllib.parse.urlencode({
        "client_id": creds["ZOHO_CLIENT_ID"],
        "client_secret": creds["ZOHO_CLIENT_SECRET"],
        "refresh_token": creds["ZOHO_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://accounts.zoho.eu/oauth/v2/token",
        data=data, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        if "access_token" not in result:
            raise Exception(f"Token error: {result}")
        return result["access_token"]

def crm_get(token, path, params=None):
    url = f"https://www.zohoapis.eu/crm/v2/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Zoho-oauthtoken {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def search_records(token, module, criteria):
    return crm_get(token, f"{module}/search", {"criteria": criteria, "per_page": 5})

def main():
    creds = load_creds()
    token = get_token(creds)
    print("Got Zoho token.\n")

    # Search Leads first, then Contacts
    for module in ["Leads", "Contacts"]:
        print(f"Searching {module} for 'Nida'...")
        data, err = search_records(token, module, "(Last_Name:equals:Nida)")
        if not err and data and data.get("data"):
            for rec in data["data"]:
                print(f"  Found: {rec.get('Full_Name') or rec.get('First_Name','')+' '+rec.get('Last_Name','')} | Email: {rec.get('Email')} | ID: {rec.get('id')}")
            break
        # Try first name search
        data, err = search_records(token, module, "(First_Name:equals:Nida)")
        if not err and data and data.get("data"):
            for rec in data["data"]:
                print(f"  Found: {rec.get('Full_Name') or rec.get('First_Name','')+' '+rec.get('Last_Name','')} | Email: {rec.get('Email')} | ID: {rec.get('id')}")
            break
        # Try full name contains
        data, err = search_records(token, module, "(Full_Name:contains:Nida)")
        if not err and data and data.get("data"):
            for rec in data["data"]:
                print(f"  Found: {rec.get('Full_Name') or rec.get('First_Name','')+' '+rec.get('Last_Name','')} | Email: {rec.get('Email')} | ID: {rec.get('id')}")
            break
        data, err = search_records(token, module, "(Last_Name:contains:Nida)")
        if not err and data and data.get("data"):
            for rec in data["data"]:
                print(f"  Found: {rec.get('Full_Name') or rec.get('First_Name','')+' '+rec.get('Last_Name','')} | Email: {rec.get('Email')} | ID: {rec.get('id')}")
            break
        if err:
            print(f"  Error: {err[:200]}")
        else:
            print(f"  Not found in {module}.")

    # Also search word-search
    print("\nTrying word search across all modules...")
    data, err = crm_get(token, "search", {"word": "Nida", "per_page": 10})
    if not err and data:
        for item in data.get("data", []):
            print(f"  {item.get('type')}: {item.get('Full_Name') or item.get('name')} | {item.get('Email')}")
    elif err:
        print(f"  Error: {err[:200]}")

if __name__ == "__main__":
    main()
