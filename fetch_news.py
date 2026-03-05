import os
import json
import logging
import requests
from datetime import datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import feedparser

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_top_news():
    """Fetches the top 5 news articles from BBC News RSS Feed (No API Key Required)."""
    logging.info("Fetching news from BBC RSS Feed...")

    url = "http://feeds.bbci.co.uk/news/rss.xml"
    try:
        feed = feedparser.parse(url)
        articles = feed.entries[:5] # Get the top 5 articles
        
        news_data = []
        fetch_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        for article in articles:
            news_data.append({
                "Date": fetch_date,
                "Title": article.get("title", ""),
                "Source": "BBC News",
                "Description": article.get("description", ""),
                "URL": article.get("link", "")
            })
            
        logging.info(f"Successfully fetched {len(news_data)} news articles.")
        return news_data
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

def get_google_sheet():
    """Authenticates and returns the Google Sheet."""
    if not GOOGLE_SHEET_URL:
        logging.error("GOOGLE_SHEET_URL is not set.")
        return None

    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # In GitHub Actions, Google credentials should be stored in a secret
        # For local usage, they can be read from a file or environment variable
        creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_json_str:
            logging.error("GOOGLE_CREDENTIALS_JSON is not set.")
            return None
            
        creds_dict = json.loads(creds_json_str)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Open by URL
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        return sheet
    except Exception as e:
        logging.error(f"Error authenticating to Google Sheets: {e}")
        return None

def write_to_sheets(sheet, news_list):
    """Appends news data to the Google Sheet if it doesn't already exist."""
    if not sheet or not news_list:
        return

    logging.info("Writing data to Google Sheets...")
    try:
        # Check existing URLs to avoid duplicates for the current day
        existing_urls = []
        try:
            records = sheet.get_all_records()
            existing_urls = [r.get("URL") for r in records if r.get("URL")]
        except Exception as sheet_err:
            logging.warning(f"Could not read existing sheet data (might be empty): {sheet_err}")
            # If sheet is empty, let's initialize headers
            sheet.append_row(["Date", "Title", "Source", "Description", "URL"])
            
        rows_added = 0
        for news in news_list:
            if news["URL"] not in existing_urls:
                sheet.append_row([
                    news["Date"],
                    news["Title"],
                    news["Source"],
                    news["Description"],
                    news["URL"]
                ])
                rows_added += 1
                existing_urls.append(news["URL"]) # Prevent duplicates in same batch

        logging.info(f"Successfully appended {rows_added} new rows to Google Sheets.")
    except Exception as e:
        logging.error(f"Error writing to Google Sheets: {e}")

def send_to_telegram(news_list):
    """Sends the formatted news summary to a Telegram Channel."""
    if not news_list:
        return
        
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Telegram credentials not set.")
        return

    logging.info("Sending news to Telegram...")
    today_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    message = f"📰 <b>Top News – {today_str}</b>\n\n"
    
    for i, news in enumerate(news_list, 1):
        message += f"<b>{i}. {news['Title']}</b>\n"
        message += f"Source: {news['Source']}\n"
        message += f"Read more: <a href='{news['URL']}'>{news['URL']}</a>\n\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info("Successfully sent message to Telegram.")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {e}")

def main():
    logging.info("Starting Daily News Automation...")
    # 1. Fetch News
    news = fetch_top_news()
    if not news:
        logging.warning("No news fetched. Exiting.")
        return
        
    # 2. Write to Sheets
    sheet = get_google_sheet()
    if sheet:
        write_to_sheets(sheet, news)
    else:
        logging.warning("Skipping Google Sheets writing due to authentication error.")
        
    # 3. Send to Telegram
    send_to_telegram(news)
    
    logging.info("Automation completed.")

if __name__ == "__main__":
    main()
