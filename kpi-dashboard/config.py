from pathlib import Path

CREDENTIALS_DIR = Path(__file__).parent / "credentials"

PERSONAL_ADC = CREDENTIALS_DIR / "personal_adc.json"
SHEETS_ADC = CREDENTIALS_DIR / "sheets_adc.json"
WORKSPACE_ADC = CREDENTIALS_DIR / "workspace_adc.json"

# GA4 property IDs — numeric, used by the Data API
PROPERTIES = [
    # Personal account (academyforpetloss@gmail.com)
    {
        "id": "537925237",
        "label": "Golders Green",
        "tab": "Golders Green",
        "account": "personal",
        "group": "standalone",
    },
    {
        "id": "538059252",
        "label": "Pet Academy",
        "tab": "Pet Academy",
        "account": "personal",
        "group": "standalone",
    },
    {
        "id": "538069718",
        "label": "Trace Memorial",
        "tab": "Trace Memorial",
        "account": "personal",
        "group": "standalone",
    },
    # Workspace account (marta@martakalas.com)
    {
        "id": "524816336",
        "label": "Bratislava",
        "tab": "AB - Bratislava",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmentbratislava.com",
    },
    {
        "id": "523606556",
        "label": "Budapest",
        "tab": "AB - Budapest",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmentbudapest.com",
    },
    {
        "id": "524758450",
        "label": "Cluj",
        "tab": "AB - Cluj",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmentcluj.com",
    },
    {
        "id": "524817061",
        "label": "Istanbul",
        "tab": "AB - Istanbul",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmentistanbul.com",
    },
    {
        "id": "524798409",
        "label": "Kyiv",
        "tab": "AB - Kyiv",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmentkyiv.com",
    },
    {
        "id": "524799177",
        "label": "Seville",
        "tab": "AB - Seville",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmentseville.com",
    },
    {
        "id": "524791437",
        "label": "Tallinn",
        "tab": "AB - Tallinn",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmenttallinn.com",
    },
    {
        "id": "524777603",
        "label": "Tirana",
        "tab": "AB - Tirana",
        "account": "workspace",
        "group": "apartment",
        "domain": "apartmenttirana.com",
    },
]

GA4_SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/cloud-platform",
]

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Combined — used when setting up fresh credentials
ALL_SCOPES = GA4_SCOPES + SHEETS_SCOPES

# Set this to the Google Sheet ID once created (or leave None to auto-create)
SHEET_ID = None
SHEET_NAME = "KPI Dashboard — All Projects"
