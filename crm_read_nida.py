"""
Find Dr Nida in Zoho CRM and read recent notes/activities/emails.
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
        "refresh_token": creds["ZOHO_CRM_REFRESH_TOKEN"],
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
            content = resp.read()
            return (json.loads(content) if content.strip() else {}), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def print_record(rec, label="Record"):
    print(f"\n{label}:")
    interesting = ["id", "Full_Name", "First_Name", "Last_Name", "Email", "Phone",
                   "Lead_Source", "Lead_Status", "Contact_Lifecycle_v2",
                   "Company", "Title", "Description", "Created_Time", "Modified_Time"]
    for k in interesting:
        if rec.get(k):
            print(f"  {k}: {rec[k]}")

def main():
    creds = load_creds()
    token = get_token(creds)
    print("Got Zoho CRM token.\n")

    found_records = []

    for module in ["Leads", "Contacts"]:
        for field, val in [("Last_Name", "Nida"), ("First_Name", "Nida"), ("Full_Name", "Nida")]:
            for op in ["equals", "contains"]:
                data, err = crm_get(token, f"{module}/search",
                    {"criteria": f"({field}:{op}:{val})", "per_page": 5})
                if not err and data and data.get("data"):
                    for rec in data["data"]:
                        if not any(r["id"] == rec["id"] for r in found_records):
                            rec["_module"] = module
                            found_records.append(rec)

    if not found_records:
        print("Not found by name. Trying word search...")
        data, err = crm_get(token, "unified_search",
            {"word": "Nida", "per_page": 10})
        if not err and data:
            for item in data.get("data", []):
                item["_module"] = item.get("type", "Unknown")
                found_records.append(item)

    if not found_records:
        print("No record found for Nida.")
        return

    for rec in found_records:
        print_record(rec, label=f"{rec.get('_module','?')} record")
        rec_id = rec["id"]
        module = rec.get("_module", "Leads")

        # Get notes
        print(f"\n  --- Notes for {rec_id} ---")
        notes, err = crm_get(token, f"{module}/{rec_id}/Notes",
            {"per_page": 10, "sort_by": "Created_Time", "sort_order": "desc"})
        if not err and notes and notes.get("data"):
            for note in notes["data"]:
                print(f"  [{note.get('Created_Time','')}] {note.get('Note_Title','(no title)')}")
                print(f"    {note.get('Note_Content','')[:300]}")
        else:
            print("  No notes found.")

        # Get activities (calls, meetings)
        print(f"\n  --- Activities for {rec_id} ---")
        acts, err = crm_get(token, f"{module}/{rec_id}/Activities",
            {"per_page": 10})
        if not err and acts and acts.get("data"):
            for act in acts["data"]:
                print(f"  [{act.get('Created_Time','')}] {act.get('Activity_Type','')} - {act.get('Subject','')}")
                print(f"    {act.get('Description','')[:200]}")
        else:
            print("  No activities found.")

        # Get emails sent/received
        print(f"\n  --- Emails for {rec_id} ---")
        emails, err = crm_get(token, f"{module}/{rec_id}/Emails",
            {"per_page": 10})
        if not err and emails and emails.get("data"):
            for em in emails["data"]:
                print(f"  [{em.get('date_time','')}] From: {em.get('from',{}).get('user_name','')} | Subject: {em.get('subject','')}")
                content = em.get("content", "") or em.get("summary", "")
                print(f"    {str(content)[:300]}")
        else:
            print("  No emails found (or not accessible).")

if __name__ == "__main__":
    main()
