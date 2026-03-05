import os
import json
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Streamlit Configuration & Initialization
# ---------------------------------------------------------
st.set_page_config(page_title="Top News Fetcher", page_icon="📰", layout="wide")

# ---------------------------------------------------------
# CSS Styling
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

.stApp {
    background-color: #F2F2F2;
    font-family: 'Inter', sans-serif;
}

/* === HEADER === */
.site-header {
    background-color: #BB1919;
    color: #FFFFFF;
    padding: 28px 48px 20px 48px;
    text-align: center;
    border-bottom: 4px solid #880000;
    margin-bottom: 0;
}

.site-header .logo {
    font-family: "Times New Roman", Times, serif;
    font-size: 48px;
    font-weight: bold;
    letter-spacing: 2px;
    line-height: 1.1;
    display: block;
    margin: 0 auto;
}

.site-header .tagline {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: rgba(255,255,255,0.75);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 6px;
}

/* === CONTENT AREA === */
.content-wrapper {
    max-width: 960px;
    margin: 28px auto 0 auto;
    padding: 0 24px 48px 24px;
}

/* === NEWS CARDS === */
.news-card {
    background-color: #FFFFFF;
    border-top: 3px solid #BB1919;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.news-card-category {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #BB1919;
    margin-bottom: 8px;
}

.news-card-title a {
    font-family: "Times New Roman", Times, serif;
    font-size: 24px;
    font-weight: bold;
    color: #1A1A1A;
    text-decoration: none;
    line-height: 1.3;
    display: block;
    margin-bottom: 10px;
}

.news-card-title a:hover { color: #BB1919; }

.news-card-meta {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #888888;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
    border-bottom: 1px solid #EEEEEE;
    padding-bottom: 12px;
}

.news-card-desc {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    color: #4A4A4A;
    line-height: 1.65;
}

/* === CATEGORY BUTTONS === */
div[data-testid="stHorizontalBlock"] > div > div.stButton > button {
    background-color: #222222;
    color: #DDDDDD;
    border: none;
    border-radius: 0px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 8px 18px;
    width: 100%;
    cursor: pointer;
}

div[data-testid="stHorizontalBlock"] > div > div.stButton > button:hover,
div[data-testid="stHorizontalBlock"] > div > div.stButton > button:focus {
    background-color: #BB1919;
    color: #FFFFFF;
    border-color: #BB1919;
}

/* === FOOTER === */
.site-footer {
    background-color: #222222;
    color: #AAAAAA;
    text-align: center;
    padding: 18px;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    margin-top: 48px;
}
</style>

<div class="site-header">
    <span class="logo">Top News Fetcher</span>
    <div class="tagline">Daily News &bull; Automatically Curated</div>
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
# Load Data from Google Sheets
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
        return pd.DataFrame()
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        if isinstance(GOOGLE_CREDENTIALS_JSON, str):
            creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        else:
            creds_dict = dict(GOOGLE_CREDENTIALS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by="Date", ascending=False)
        return df
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {e}")
        return pd.DataFrame()

df = load_data()

# ---------------------------------------------------------
# Session State for Category Selection
# ---------------------------------------------------------
if "active_category" not in st.session_state:
    st.session_state.active_category = "All"

# ---------------------------------------------------------
# Functional Category Nav Bar
# ---------------------------------------------------------
categories = ["All", "World/Current Affairs", "Sports", "Entertainment/Movies", "Technology", "Business"]
cat_labels  = ["All",  "World",              "Sports",  "Entertainment",         "Technology",  "Business"]

# Render as columns of buttons
cols = st.columns(len(categories))
for i, (cat, label) in enumerate(zip(categories, cat_labels)):
    if cols[i].button(label, key=f"cat_{cat}"):
        st.session_state.active_category = cat

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.markdown("## 🔍 Filter News")
search_query = st.sidebar.text_input("🔎 Search Title or Description")

if not df.empty:
    unique_dates = df['Date'].dt.date.unique()
    selected_date = st.sidebar.selectbox("📅 Select Date", ["All Dates"] + list(unique_dates))
else:
    selected_date = "All Dates"

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

    # Apply category filter
    if st.session_state.active_category != "All":
        filtered_df = filtered_df[filtered_df['Source'].str.contains(st.session_state.active_category, case=False, na=False)]

    # Apply date filter
    if selected_date != "All Dates":
        filtered_df = filtered_df[filtered_df['Date'].dt.date == selected_date]

    # Apply search filter
    if search_query:
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(search_query, case=False, na=False) |
            filtered_df['Description'].str.contains(search_query, case=False, na=False)
        ]

    active = st.session_state.active_category if st.session_state.active_category != "All" else "All Categories"
    st.markdown(f"<p style='font-family:Inter,sans-serif; color:#888; font-size:13px; padding: 12px 0;'>Showing <strong>{len(filtered_df)}</strong> articles in <strong>{active}</strong></p>", unsafe_allow_html=True)

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
