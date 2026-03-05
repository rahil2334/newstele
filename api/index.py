import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

def get_google_sheet():
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
        print("Missing Google Sheets Configuration in environment.")
        return None

    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON) if isinstance(GOOGLE_CREDENTIALS_JSON, str) else dict(GOOGLE_CREDENTIALS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        return sheet
    except Exception as e:
        print(f"Error authenticating to Google Sheets: {e}")
        return None

@app.get("/api/news")
def get_news():
    sheet = get_google_sheet()
    if not sheet:
        raise HTTPException(status_code=500, detail="Database configuration missing or invalid.")
    
    try:
        records = sheet.get_all_records()
        
        # Sort by date descending (assuming format: 'YYYY-MM-DD HH:MM:SS UTC')
        # gspread returns strings, so we can sort them alphabetically since the format is sortable
        records_sorted = sorted(records, key=lambda x: str(x.get('Date', '')), reverse=True)
        return {"status": "success", "data": records_sorted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
