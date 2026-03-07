import os
import json
import html as html_module
from datetime import date, datetime, timezone
import requests
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Streamlit Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="Top News Fetcher", page_icon="📰", layout="wide")

# ---------------------------------------------------------
# Read active category from URL query params
# ---------------------------------------------------------
try:
    active_cat = st.query_params.get("category", "All")
except Exception:
    active_cat = "All"

# ---------------------------------------------------------
# CSS + Sticky Header HTML
# ---------------------------------------------------------
categories = {
    "All":           "All",
    "World":         "World/Current Affairs",
    "Sports":        "Sports",
    "Entertainment": "Entertainment/Movies",
    "Technology":    "Technology",
    "Business":      "Business",
}

nav_items_html = ""
for label, value in categories.items():
    is_active = "active" if active_cat == value or (active_cat == "All" and label == "All") else ""
    nav_items_html += f'<a class="nav-item {is_active}" href="?category={value}">{label}</a>'

st.markdown(f"""
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap");
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
.block-container {{ padding-top: 186px !important; padding-left: 0 !important; padding-right: 0 !important; max-width: 100% !important; }}
.stApp {{ background-color: #F0F0F0; font-family: "Inter", sans-serif; }}

/* === STICKY HEADER === */
.sticky-header {{ position: fixed; top: 0; left: 0; width: 100%; z-index: 99999; box-shadow: 0 2px 8px rgba(0,0,0,0.25); }}

/* === RED TITLE BAR === */
.site-header {{
    background-color: #BB1919;
    color: #FFFFFF;
    padding: 20px 48px 16px 48px;
    text-align: center;
    border-bottom: 4px solid #880000;
    min-height: 90px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: visible;
}}
.site-header .logo {{
    font-family: "Times New Roman", Times, serif;
    font-size: 48px;
    font-weight: bold;
    letter-spacing: 2px;
    line-height: 1.2;
    white-space: nowrap;
    overflow: visible;
}}
.site-header .tagline {{
    font-size: 11px;
    color: rgba(255,255,255,0.85);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
}}

/* === DARK NAV BAR === */
.nav-bar {{
    background-color: #1A1A1A;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 44px;
    border-bottom: 2px solid #333;
}}
.nav-item {{
    color: #CCCCCC;
    font-family: "Inter", sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    text-decoration: none;
    padding: 12px 22px;
    height: 100%;
    display: flex;
    align-items: center;
    border-bottom: 3px solid transparent;
    transition: background 0.15s, color 0.15s;
}}
.nav-item:hover {{ background-color: #2A2A2A; color: #FFFFFF; border-bottom: 3px solid #BB1919; }}
.nav-item.active {{ color: #FFFFFF; background-color: #BB1919; border-bottom: 3px solid #FF4444; }}

/* === CONTENT === */
.content-wrapper {{ max-width: 960px; margin: 24px auto 0 auto; padding: 0 24px 64px 24px; }}

/* === NEWS CARDS === */
.news-card {{
    background-color: #FFFFFF;
    border-top: 3px solid #BB1919;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}
.news-card-category {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #BB1919;
    margin-bottom: 8px;
}}
.news-card-title a {{
    font-family: "Times New Roman", Times, serif;
    font-size: 24px;
    font-weight: bold;
    color: #1A1A1A;
    text-decoration: none;
    line-height: 1.3;
    display: block;
    margin-bottom: 10px;
}}
.news-card-title a:hover {{ color: #BB1919; }}
.news-card-meta {{
    font-size: 12px;
    color: #888888;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
    border-bottom: 1px solid #EEEEEE;
    padding-bottom: 12px;
}}
.news-card-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    color: #4A4A4A;
    line-height: 1.65;
}}

/* === FOOTER === */
.site-footer {{
    background-color: #1A1A1A;
    color: #AAAAAA;
    text-align: center;
    padding: 20px;
    font-size: 12px;
    margin-top: 48px;
    letter-spacing: 1px;
}}

/* Hide Streamlit chrome */
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
section[data-testid="stSidebar"] {{ display: none !important; }}
</style>

<div class="sticky-header">
    <div class="site-header">
        <span class="logo">Top News Fetcher</span>
        <span class="tagline">Daily News &bull; Automatically Curated</span>
    </div>
    <div class="nav-bar">
        {nav_items_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Login / Sign Up
# ---------------------------------------------------------
USERS_FILE = "users.json"

def _load_users() -> dict:
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"admin": "password"}

def _save_user(username: str, password: str) -> bool:
    users = _load_users()
    if username in users:
        return False
    users[username] = password
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
    return True

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;color:#BB1919;'>Login to Top News</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login_form"):
                uname = st.text_input("Username")
                passwd = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Log In", use_container_width=True)
            if login_btn:
                users = _load_users()
                if uname in users and str(users[uname]) == str(passwd):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("New Username")
                new_pass = st.text_input("New Password", type="password")
                confirm  = st.text_input("Confirm Password", type="password")
                signup_btn = st.form_submit_button("Sign Up", use_container_width=True)
            if signup_btn:
                if not new_user or not new_pass:
                    st.error("Username and password are required.")
                elif new_pass != confirm:
                    st.error("Passwords do not match.")
                elif len(new_pass) < 4:
                    st.error("Password must be at least 4 characters.")
                elif _save_user(new_user, new_pass):
                    st.success("Signup successful! You can now log in.")
                else:
                    st.error("Username already exists.")

    st.stop()

# ---------------------------------------------------------
# Secrets — read from env first, then Streamlit secrets
# ---------------------------------------------------------
def _get_secret(key: str, default=None):
    val = os.getenv(key)
    if val:
        return val
    try:
        val = st.secrets.get(key)
        return val if val is not None else default
    except Exception:
        return default

GOOGLE_SHEET_URL        = _get_secret("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_JSON = _get_secret("GOOGLE_CREDENTIALS_JSON")
TELEGRAM_BOT_TOKEN      = _get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID        = _get_secret("TELEGRAM_CHAT_ID")
GUARDIAN_API_KEY        = _get_secret("GUARDIAN_API_KEY", "test")

# ---------------------------------------------------------
# Helper: parse Google credentials (handles str & dict/AttrDict)
# ---------------------------------------------------------
def _parse_google_creds() -> dict:
    raw = GOOGLE_CREDENTIALS_JSON
    if raw is None:
        raise ValueError("GOOGLE_CREDENTIALS_JSON is not configured.")
    if isinstance(raw, str):
        # TOML triple-quoted strings sometimes double-escape the newlines,
        # or have raw newlines. `strict=False` allows control characters.
        cleaned = raw.replace('\\n', '\n')
        return json.loads(cleaned, strict=False)
    # Streamlit already parsed the TOML table into a dict-like object
    return dict(raw)

# ---------------------------------------------------------
# Guardian section map
# ---------------------------------------------------------
GUARDIAN_SECTION_MAP = {
    "World/Current Affairs": "world",
    "Sports":                "sport",
    "Entertainment/Movies":  "culture",
    "Technology":            "technology",
    "Business":              "business",
}

# ---------------------------------------------------------
# Fetch live news from The Guardian API
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_guardian_news(query_date: date, category: str = "All"):
    date_str = query_date.strftime("%Y-%m-%d")
    base_url = "https://content.guardianapis.com/search"
    results = []

    sections = list(GUARDIAN_SECTION_MAP.values()) if category == "All" else [
        GUARDIAN_SECTION_MAP.get(category, "news")
    ]
    section_labels = {v: k for k, v in GUARDIAN_SECTION_MAP.items()}

    for section in sections:
        params = {
            "from-date":    date_str,
            "to-date":      date_str,
            "section":      section,
            "page-size":    4 if category == "All" else 10,
            "show-fields":  "trailText,shortUrl",
            "api-key":      GUARDIAN_API_KEY,
            "order-by":     "relevance",
        }
        try:
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("response", {}).get("results", []):
                cat_label = section_labels.get(section, section.title())
                results.append({
                    "Title":       item.get("webTitle", "No Title"),
                    "URL":         item.get("webUrl", ""),
                    "Source":      f"The Guardian ({cat_label})",
                    "Description": item.get("fields", {}).get("trailText", ""),
                    "Date":        pd.Timestamp(date_str),
                })
        except Exception:
            pass

    return pd.DataFrame(results) if results else pd.DataFrame()

# ---------------------------------------------------------
# Append fetched articles to Google Sheet
# ---------------------------------------------------------
def append_to_gsheet(news_df: pd.DataFrame):
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON or news_df.empty:
        return
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(_parse_google_creds(), scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1

        # Build set of existing URLs to avoid duplicates
        try:
            existing_urls = {r.get("URL", "") for r in sheet.get_all_records()}
        except Exception:
            existing_urls = set()

        added = 0
        for _, row in news_df.iterrows():
            if str(row["URL"]) not in existing_urls:
                date_str = pd.Timestamp(row["Date"]).strftime("%Y-%m-%d %H:%M:%S UTC")
                sheet.append_row([date_str, str(row["Title"]), str(row["Source"]),
                                   str(row["Description"]), str(row["URL"])])
                existing_urls.add(str(row["URL"]))
                added += 1
    except Exception as e:
        st.error(f"Google Sheets error: {e}")

# ---------------------------------------------------------
# Send top-5 articles to Telegram
# ---------------------------------------------------------
def send_to_telegram(news_df: pd.DataFrame, date_obj):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or news_df.empty:
        return
    date_str = date_obj.strftime("%d %b %Y") if date_obj else "Unknown Date"
    message = f"📰 <b>Top News – {date_str}</b>\n\n"

    for i, row in enumerate(news_df.head(5).itertuples(), 1):
        safe_title  = html_module.escape(str(row.Title))
        safe_source = html_module.escape(str(row.Source))
        safe_url    = html_module.escape(str(row.URL))
        message += f"<b>{i}. {safe_title}</b>\n"
        message += f"Source: {safe_source}\n"
        message += f"Read more: <a href='{safe_url}'>Link</a>\n\n"

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10,
        )
    except Exception as e:
        st.error(f"Telegram error: {e}")

# ---------------------------------------------------------
# Load data from Google Sheet
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
        return pd.DataFrame()
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(_parse_google_creds(), scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        try:
            df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            df["Date"] = pd.to_datetime(df["Date"], format="mixed")
        return df.sort_values(by="Date", ascending=False)
    except Exception as e:
        st.error(f"Error loading news data: {e}")
        return pd.DataFrame()

df = load_data()

# ---------------------------------------------------------
# Main Content
# ---------------------------------------------------------
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
    st.error("Missing Google Sheets configuration. Please check your environment variables or Streamlit secrets.")
elif df.empty:
    st.info("No news data available yet. Please run `fetch_news.py` to populate the Google Sheet.")
else:
    col_cal, col_clear = st.columns([3, 1])
    with col_cal:
        available_dates = sorted(df["Date"].dt.date.unique(), reverse=True)
        min_date    = date(1999, 1, 1)
        max_date    = date.today()
        default_date = available_dates[0] if available_dates else max_date
        default_date = max(min_date, min(default_date, max_date))
        selected_date = st.date_input(
            "📅 Select a date to view news",
            value=default_date,
            min_value=min_date,
            max_value=max_date,
            help="Click any date to see news from that day",
        )
    with col_clear:
        st.write("")
        if st.button("🔄 Show All Dates"):
            selected_date = None

    filtered_df = df.copy()
    if active_cat != "All":
        filtered_df = filtered_df[filtered_df["Source"].str.contains(active_cat, case=False, na=False)]

    date_filtered = filtered_df.copy()
    if selected_date is not None:
        date_filtered = filtered_df[filtered_df["Date"].dt.date == selected_date]

    using_guardian = False
    if selected_date is not None and date_filtered.empty:
        # Fallback: fetch live from The Guardian for the selected date
        guardian_df = fetch_guardian_news(selected_date, active_cat)
        if not guardian_df.empty:
            date_filtered  = guardian_df
            using_guardian = True
            # Save to Google Sheet + notify Telegram
            append_to_gsheet(guardian_df)
            send_to_telegram(guardian_df, selected_date)
            load_data.clear()   # invalidate cache so next load picks up new rows
        else:
            st.warning(f"No news found for **{selected_date.strftime('%d %B %Y')}** in any source.")

    filtered_df = date_filtered.head(5)

    date_label   = selected_date.strftime("%d %B %Y") if selected_date else "All Dates"
    display_cat  = active_cat if active_cat != "All" else "All Categories"
    source_label_text = " · Via The Guardian (live)" if using_guardian else ""
    st.markdown(
        f"<p style='font-family:Inter,sans-serif;color:#888;font-size:13px;padding:0 0 14px 0;'>"
        f"Showing <strong>{len(filtered_df)}</strong> articles (Top 5 Max) &bull; "
        f"<strong>{display_cat}</strong> &bull; {date_label}{source_label_text}</p>",
        unsafe_allow_html=True,
    )

    for _, row in filtered_df.iterrows():
        s_label  = row["Source"]
        cat_tag  = s_label.split("(")[-1].rstrip(")") if "(" in s_label else s_label
        st.markdown(f"""
        <div class="news-card">
            <div class="news-card-category">{cat_tag}</div>
            <div class="news-card-title"><a href="{row['URL']}" target="_blank">{row['Title']}</a></div>
            <div class="news-card-meta">{s_label} &nbsp;|&nbsp; {row['Date'].strftime('%d %B %Y')}</div>
            <div class="news-card-desc">{row['Description']}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown(
    '<div class="site-footer">&copy; 2026 Top News Fetcher &mdash; Automated News Aggregator &bull; Powered by Streamlit</div>',
    unsafe_allow_html=True,
)
