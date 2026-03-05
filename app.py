import os
import json
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
params = st.query_params
active_cat = params.get("category", "All")

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
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* Push content below the fixed header (header ~130px + nav ~44px) */
.block-container {{
    padding-top: 182px !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
}}

.stApp {{
    background-color: #F0F0F0;
    font-family: 'Inter', sans-serif;
}}

/* === STICKY WRAPPER === */
.sticky-header {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 99999;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}}

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
    gap: 0;
    height: 44px;
    border-bottom: 2px solid #333;
}}

.nav-item {{
    color: #CCCCCC;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    text-decoration: none;
    padding: 12px 22px;
    height: 100%;
    display: flex;
    align-items: center;
    transition: background 0.2s, color 0.2s;
    border-bottom: 3px solid transparent;
}}

.nav-item:hover {{
    background-color: #2A2A2A;
    color: #FFFFFF;
    border-bottom: 3px solid #BB1919;
}}

.nav-item.active {{
    color: #FFFFFF;
    background-color: #BB1919;
    border-bottom: 3px solid #FF4444;
}}

/* === CONTENT === */
.content-wrapper {{
    max-width: 960px;
    margin: 24px auto 0 auto;
    padding: 0 24px 64px 24px;
}}

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
    font-family: 'Inter', sans-serif;
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

/* Hide Streamlit top header bar chrome */
header[data-testid="stHeader"] {{
    background: transparent;
    height: 0;
}}
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
# Retrieve Secrets
# ---------------------------------------------------------
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

if not GOOGLE_SHEET_URL:
    try:
        GOOGLE_SHEET_URL = st.secrets.get("GOOGLE_SHEET_URL")
    except Exception:
        GOOGLE_SHEET_URL = None

if not GOOGLE_CREDENTIALS_JSON:
    try:
        GOOGLE_CREDENTIALS_JSON = st.secrets.get("GOOGLE_CREDENTIALS_JSON")
    except Exception:
        GOOGLE_CREDENTIALS_JSON = None

# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
        return pd.DataFrame()
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON) if isinstance(GOOGLE_CREDENTIALS_JSON, str) else dict(GOOGLE_CREDENTIALS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values(by="Date", ascending=False)
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {e}")
        return pd.DataFrame()

df = load_data()

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.markdown("## 🔍 Filter News")
search_query = st.sidebar.text_input("🔎 Search Title or Description")
selected_date = "All Dates"
if not df.empty:
    unique_dates = df['Date'].dt.date.unique()
    selected_date = st.sidebar.selectbox("📅 Select Date", ["All Dates"] + list(unique_dates))

# ---------------------------------------------------------
# Main Content
# ---------------------------------------------------------
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
    st.error("Missing Google Sheets Configuration. Please check your environment variables or Streamlit secrets.")
elif df.empty:
    st.info("No news data available yet. Please run `fetch_news.py` to populate the Google Sheet.")
else:
    filtered_df = df.copy()

    # Apply category filter from URL params
    if active_cat != "All":
        filtered_df = filtered_df[filtered_df['Source'].str.contains(active_cat, case=False, na=False)]

    if selected_date != "All Dates":
        filtered_df = filtered_df[filtered_df['Date'].dt.date == selected_date]

    if search_query:
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(search_query, case=False, na=False) |
            filtered_df['Description'].str.contains(search_query, case=False, na=False)
        ]

    display_cat = active_cat if active_cat != "All" else "All Categories"
    st.markdown(
        f"<p style='font-family:Inter,sans-serif;color:#888;font-size:13px;padding:0 0 14px 0;'>"
        f"Showing <strong>{len(filtered_df)}</strong> articles in <strong>{display_cat}</strong></p>",
        unsafe_allow_html=True
    )

    for _, row in filtered_df.iterrows():
        source_label = row['Source']
        category_tag = source_label.split("(")[-1].rstrip(")") if "(" in source_label else source_label

        st.markdown(f"""
        <div class="news-card">
            <div class="news-card-category">{category_tag}</div>
            <div class="news-card-title">
                <a href="{row['URL']}" target="_blank">{row['Title']}</a>
            </div>
            <div class="news-card-meta">{source_label} &nbsp;|&nbsp; {row['Date'].strftime('%d %B %Y')}</div>
            <div class="news-card-desc">{row['Description']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""
<div class="site-footer">
    &copy; 2025 Top News Fetcher &mdash; Automated BBC News Aggregator &bull; Powered by Streamlit
</div>
""", unsafe_allow_html=True)
