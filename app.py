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

# Injecting fully polished CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

/* === GLOBAL RESET === */
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
    padding: 18px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0;
    border-bottom: 4px solid #880000;
}

.site-header .logo {
    font-family: "Times New Roman", Times, serif;
    font-size: 40px;
    font-weight: bold;
    letter-spacing: 1px;
    line-height: 1;
}

.site-header .tagline {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: rgba(255,255,255,0.8);
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* === NAV BAR === */
.category-nav {
    background-color: #222222;
    padding: 10px 48px;
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.category-nav span {
    color: #DDDDDD;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
}

.category-nav span:hover {
    color: #FFFFFF;
    text-decoration: underline;
}

/* === MAIN CONTENT AREA === */
.content-wrapper {
    max-width: 960px;
    margin: 0 auto;
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

.news-card-title a:hover {
    color: #BB1919;
}

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
    <div class="logo">Top News Fetcher</div>
    <div class="tagline">Daily news &bull; Automatically curated</div>
</div>

<div class="category-nav">
    <span>World</span>
    <span>Sports</span>
    <span>Entertainment</span>
    <span>Technology</span>
    <span>Business</span>
</div>

<div class="content-wrapper">
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Retrieve secrets - prefer environment variables loaded by dotenv
# ---------------------------------------------------------
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Fallback to Streamlit secrets if running on Streamlit Cloud
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

@st.cache_data(ttl=3600)
def load_data():
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
        st.error("Missing Google Sheets Configuration. Please check your environment variables or Streamlit secrets.")
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

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.markdown("## 🔍 Filter News")

df = load_data()

if not df.empty:
    unique_dates = df['Date'].dt.date.unique()
    selected_date = st.sidebar.selectbox("📅 Select Date", ["All Dates"] + list(unique_dates))
    
    unique_sources = df['Source'].unique()
    selected_source = st.sidebar.selectbox("📰 Select Source / Category", ["All Sources"] + list(unique_sources))
    
    search_query = st.sidebar.text_input("🔎 Search Title or Description")
    
    filtered_df = df.copy()
    
    if selected_date != "All Dates":
        filtered_df = filtered_df[filtered_df['Date'].dt.date == selected_date]
    if selected_source != "All Sources":
        filtered_df = filtered_df[filtered_df['Source'] == selected_source]
    if search_query:
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(search_query, case=False, na=False) |
            filtered_df['Description'].str.contains(search_query, case=False, na=False)
        ]

    st.markdown(f"<p style='font-family:Inter,sans-serif; color:#888; font-size:13px; padding: 0 0 12px 0;'>Showing <strong>{len(filtered_df)}</strong> articles</p>", unsafe_allow_html=True)

    for _, row in filtered_df.iterrows():
        # Extract category from source like "BBC Sport (Sports)"
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
else:
    st.info("No news data available yet. Please run `fetch_news.py` to populate the Google Sheet.")

st.markdown("""
</div>
<div class="site-footer">
    &copy; 2025 Top News Fetcher &mdash; Automated BBC News Aggregator &bull; Powered by Streamlit
</div>
""", unsafe_allow_html=True)
