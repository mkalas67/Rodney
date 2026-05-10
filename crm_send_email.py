"""
Send email to Dr Nida via Zoho CRM, logged against his Contact record.
"""
import json
import urllib.request
import urllib.parse
import urllib.error

CREDS_FILE = r"C:\Users\marta\Rodney\credentials.json"
CONTACT_ID = "413057000029751001"

SUBJECT = "CPD Certificate Process - Global Institute of Psychology"

BODY = """Dear Dr Nida,

Thanks for your questions - happy to go through the certificate process properly.

How the certificate is issued
Once a participant completes a course, you log into the Open CPD platform and issue their certificate - individually or in bulk via CSV upload. The platform delivers everything instantly by email: a digital certificate, a digital badge (Open Badge 2.0 standard), and a link to their personal achievement page. No manual approval on our side - you issue when you're ready.

Your logo and branding
Your academy logo, name and social media details are uploaded to your organisation profile during setup and incorporated into every certificate you issue. The certificates carry your identity - Open CPD appears in the background as the credentialing platform.

Verification - how it works
Open CPD certificates are primarily electronic documents rather than printed ones. Each certificate comes with a unique, permanent achievement page at achievements.open-cpd.com - a public URL specific to that student and that course. Anyone can verify a certificate by visiting that page: it shows the course details, the provider's profile, and the learner's record. The certificate is tamper-proof and cannot be altered after issue.

The CPD Charter - worth knowing about
As part of the setup process, you'll be invited to sign the Open CPD Charter - a public declaration of your commitment to CPD standards. This isn't a formality: it gives the Global Institute of Psychology its own CPD Membership Certificate and establishes you as a verified, bona fide CPD provider on the platform. For your participants and clients, this is the underpinning that makes your certificates meaningful - your organisation is publicly listed and accountable, not just issuing documents.

Automated or approved?
Entirely self-service. No submission, no waiting, no external sign-off on individual certificates. You are in control of what gets issued and when.

Using your academy name
No restrictions. You issue as the Global Institute of Psychology. The only language convention is that certificates reference Open CPD as the credentialing platform rather than implying we have independently assessed the training content - but that's a simple wording point we can help with.

I've put together a short guide that covers the full setup - most providers are up and running within a day:
How to Set Up CPD Accreditation in Just One Day - Without Breaking the Bank
https://open-cpd.com/wp-content/uploads/2025/12/How-to-Set-Up-CPD-Accreditation-in-Just-One-Day%E2%80%94Without-Breaking-the-Bank.pdf

If it would help to walk through this on a quick call, just pick a time here:
https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ2pDMHI0jP1jNUkEK4VO4Cc2Iz8DFCcJdlGQktDOif6ArEiAgjM0vVXHarKf_IhSot13FhHk35

Looking forward to hearing from you.

Best,
Marta
Open CPD"""

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

def crm_post(token, path, body_dict):
    url = f"https://www.zohoapis.eu/crm/v2/{path}"
    body = json.dumps(body_dict).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"Authorization": f"Zoho-oauthtoken {token}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return (json.loads(content) if content.strip() else {}), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def main():
    creds = load_creds()
    token = get_token(creds)
    print("Got token.")

    # First get the from address (CRM user email)
    payload = {
        "data": [{
            "from": {
                "user_name": "Marta Kalas",
                "email": "marta@open-cpd.com"
            },
            "to": [{
                "user_name": "Dr Nida",
                "email": "globalinstituteofpsychology@gmail.com"
            }],
            "subject": SUBJECT,
            "content": BODY,
            "mail_format": "text",
            "schedule_time": "",
            "attachments": []
        }]
    }

    print(f"Sending email to Dr Nida via CRM (Contact {CONTACT_ID})...")
    result, err = crm_post(token, f"Contacts/{CONTACT_ID}/actions/send_mail", payload)

    if err:
        print(f"CRM send failed: {err[:300]}")
        print("\nFalling back to Gmail...")
        send_via_gmail(creds)
    else:
        print("Result:", json.dumps(result, indent=2))
        data = result.get("data", [{}])
        status = data[0].get("status") if data else None
        if status == "success" or result.get("message") == "success":
            print("\nEmail sent successfully via CRM and logged against the contact record.")
        else:
            print("\nUnexpected response - trying Gmail fallback...")
            send_via_gmail(creds)

def send_via_gmail(creds):
    import base64, email.mime.text
    gmail_creds_file = r"C:\Users\marta\Rodney\gmail-credentials.json"
    with open(gmail_creds_file) as f:
        gmail_creds = json.load(f)

    account = gmail_creds["accounts"]["gmail-opencpd"]
    client = gmail_creds["gcp_oauth_client"]
    data = urllib.parse.urlencode({
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": account["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        g_token = json.loads(resp.read())["access_token"]

    msg = email.mime.text.MIMEText(BODY, "plain", "utf-8")
    msg["To"] = "Dr Nida <globalinstituteofpsychology@gmail.com>"
    msg["From"] = "Marta Kalas <marta@open-cpd.com>"
    msg["Subject"] = SUBJECT
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    send_body = json.dumps({"raw": raw}).encode("utf-8")
    req2 = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=send_body, method="POST",
        headers={"Authorization": f"Bearer {g_token}",
                 "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req2) as resp:
            result = json.loads(resp.read())
            print(f"Sent via Gmail. Message ID: {result.get('id')}")
    except urllib.error.HTTPError as e:
        print(f"Gmail also failed: {e.read().decode()[:300]}")

if __name__ == "__main__":
    main()
