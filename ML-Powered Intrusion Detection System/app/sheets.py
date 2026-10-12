"""Optional Google Sheets logging of normal flows via a service account."""
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from app.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_NAME

SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]


def log_normal_flow(flow: dict) -> None:
    if not GOOGLE_SHEET_NAME:
        return
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, SCOPE)
        sheet = gspread.authorize(creds).open(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row([str(v) for v in flow.values()])
    except Exception:
        pass  # logging is optional and must not affect the verdict
