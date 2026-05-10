"""
Update the known draft r6863118584587526132 (Rhoda reply) with completed text.
"""
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import email.mime.text

CREDS_FILE = r"C:\Users\marta\Rodney\gmail-credentials.json"
ACCOUNT = "gmail-opencpd"
DRAFT_ID = "r6863118584587526132"

NEW_BODY = """Dear Rhoda,

Apologies for not following up sooner - I was on the road for a few days and didn't plan well enough to stay on top of things. I'm back now.

Here are answers to your questions. And yes, let's have a call - as early as tomorrow morning if that works. Just pick a slot here:
https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ2pDMHI0jP1jNUkEK4VO4Cc2Iz8DFCcJdlGQktDOif6ArEiAgjM0vVXHarKf_IhSot13FhHk35

Retroactive accreditation - yes, we can cover courses already in progress and even retrospectively, for up to six months. Your May 1 launches are well within that window.

Documentation - you don't need to submit materials to us. What you do need is clearly defined Learning Aims, Skills and Outcomes for each programme. You may already have these as part of your ILO WiDB curriculum documentation - if so, it's simply a matter of adding them to your course profile on the Open CPD app. If not, we have a free AI tool (CPD Genie) that can pull them from existing materials. Either way, we provide full support and it typically takes about an hour per course.

Pricing - unlike most accreditation providers, we charge by usage, not by course - no submission fees, no annual licence. Our Pay-as-you-go option is a good starting point, at £2 per certificate with no commitment. Once you have a rough sense of likely participant numbers across your four programmes, I'm happy to work out the most cost-effective option for your volume. Worth having that conversation on the call.

SimpliTrain - there's no direct integration between Open CPD and SimpliTrain, but you don't need one - particularly at this stage. The way it works: participants complete their course on SimpliTrain, and you issue Open CPD certificates separately, either one at a time or via a quick bulk CSV upload. The upload takes minutes and gives you a chance to check everything before issuing - which is actually more flexible than a live API connection. We can walk through this on the call.

Participant certificates - once issued, each participant automatically receives a unique, tamper-proof digital certificate and an Open Badge 2.0 digital badge, both delivered by email. They also get a persistent public achievement page at achievements.open-cpd.com that they can share - including directly to LinkedIn.

I thought this might be a useful read before our call - it covers how to get set up with CPD accreditation quickly and without unnecessary cost:
How to Set Up CPD Accreditation in Just One Day - Without Breaking the Bank
https://open-cpd.com/wp-content/uploads/2025/12/How-to-Set-Up-CPD-Accreditation-in-Just-One-Day%E2%80%94Without-Breaking-the-Bank.pdf

On your ITC-ILO and QCTO accreditation - Open CPD sits alongside those frameworks rather than competing with them. We handle the digital certificate issuance and verification side; those bodies provide recognition within their respective systems. The two are complementary.

Looking forward to speaking.

Best,
Marta"""

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

def gmail_request(token, method, path, body_dict=None):
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    body = json.dumps(body_dict).encode("utf-8") if body_dict else None
    headers = {"Authorization": f"Bearer {token}"}
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")

def main():
    creds = load_creds()
    token = get_token(creds)
    print("Got token.")

    # Get the existing draft to retrieve threadId and message details
    print(f"Fetching draft {DRAFT_ID}...")
    draft, err = gmail_request(token, "GET", f"drafts/{DRAFT_ID}")
    if err:
        print("Error fetching draft:", err)
        return

    msg = draft.get("message", {})
    thread_id = msg.get("threadId")
    msg_id = msg.get("id")
    print(f"Thread ID: {thread_id}")
    print(f"Message ID: {msg_id}")

    # Try to get In-Reply-To from the existing draft message
    full_msg, _ = gmail_request(token, "GET", f"messages/{msg_id}?format=metadata&metadataHeaders=In-Reply-To&metadataHeaders=References&metadataHeaders=Subject&metadataHeaders=To")
    in_reply_to = ""
    references = ""
    subject = "Re: Following Up - OpenCPD Accreditation for ILO WiDB Training Programmes"

    if full_msg:
        headers = full_msg.get("payload", {}).get("headers", [])
        for h in headers:
            n = h["name"].lower()
            if n == "in-reply-to":
                in_reply_to = h["value"]
            elif n == "references":
                references = h["value"]
            elif n == "subject":
                subject = h["value"]
        print(f"Subject: {subject}")
        print(f"In-Reply-To: {in_reply_to}")

    # Build MIME message
    mime_msg = email.mime.text.MIMEText(NEW_BODY, "plain", "utf-8")
    mime_msg["To"] = "Rhoda Fenon <rhoda@profskillsportal.com>"
    mime_msg["From"] = "Marta Kalas <marta@open-cpd.com>"
    mime_msg["Subject"] = subject
    if in_reply_to:
        mime_msg["In-Reply-To"] = in_reply_to
    if references:
        mime_msg["References"] = references

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

    update_body = {
        "message": {
            "raw": raw,
            "threadId": thread_id
        }
    }

    print("\nUpdating draft...")
    result, err = gmail_request(token, "PUT", f"drafts/{DRAFT_ID}", update_body)
    if err:
        print("ERROR updating draft:", err)
    else:
        print("Draft updated successfully!")
        print(f"Draft ID: {result.get('id')}")

if __name__ == "__main__":
    main()
