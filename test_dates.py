import os
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv('c:\\Users\\HP\\OneDrive\\Desktop\\New folder\\news-automation\\.env')

GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
records = sheet.get_all_records()
df = pd.DataFrame(records)
print("Raw Dates:")
print(df["Date"].head(10).tolist())

print("Parsed Dates:")
df["Date"] = pd.to_datetime(df["Date"])
print(df["Date"].dt.date.head(10).tolist())
