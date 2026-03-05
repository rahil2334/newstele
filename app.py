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
st.set_page_config(page_title="Top News Feacher", page_icon="📰", layout="wide")

# Injecting Custom BBC Style CSS with user requested font
st.markdown("""
<style>
/* Reset padding to make header align perfectly */
.block-container {
    padding-top: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 1200px;
}

/* Custom Header styling */
.main-header {
    background-color: #B80000;
    color: white;
    padding: 15px 30px;
    font-family: "Times New Roman", Times, serif;
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 30px;
    width: 100%;
    display: flex;
    align-items: center;
}

/* App Background */
.stApp {
    background-color: #F6F6F6;
}

/* News Article Card */
.bbc-news-container {
    background-color: #FFFFFF;
    padding: 20px 30px;
    margin-bottom: 15px;
    border-left: 4px solid #B80000;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.bbc-news-title {
    color: #222222;
    font-size: 26px;
    font-weight: bold;
    text-decoration: none;
    font-family: "Times New Roman", Times, serif;
    margin-bottom: 8px;
    display: block;
    line-height: 1.2;
}

.bbc-news-title:hover {
    color: #B80000;
    text-decoration: underline;
}

.bbc-news-meta {
    color: #5A5A5A;
    font-size: 14px;
    font-family: Arial, sans-serif;
    margin-bottom: 12px;
    text-transform: uppercase;
}

.bbc-news-desc {
    color: #404040;
    font-size: 16px;
    font-family: Arial, sans-serif;
    line-height: 1.5;
}
</style>

<div class="main-header">
    Top News Feacher
</div>
""", unsafe_allow_html=True)

# Retrieve secrets
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL") or st.secrets.get("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON") or st.secrets.get("GOOGLE_CREDENTIALS_JSON")

@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent excessive API calls
def load_data():
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS_JSON:
        st.error("Missing Google Sheets Configuration. Please check your environment variables or Streamlit secrets.")
        return pd.DataFrame()
        
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        if isinstance(GOOGLE_CREDENTIALS_JSON, str):
            creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        else:
            # Streamlit secrets might return it as a dict directly
            creds_dict = dict(GOOGLE_CREDENTIALS_JSON)
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        records = sheet.get_all_records()
        
        if not records:
            return pd.DataFrame()
            
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        # Sort by latest date first
        df = df.sort_values(by="Date", ascending=False)
        return df
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {e}")
        return pd.DataFrame()

# Load Data
df = load_data()

if df.empty:
    st.info("No news data available yet. Ensure the fetch_news.py script has run successfully.")
else:
    # ---------------------------------------------------------
    # UI Filters
    # ---------------------------------------------------------
    st.sidebar.header("Filters")
    
    # 1. Date Filter
    unique_dates = df['Date'].dt.date.unique()
    selected_date = st.sidebar.selectbox("Select Date", ["All Dates"] + list(unique_dates))
    
    # 2. Source Filter
    unique_sources = df['Source'].unique()
    selected_source = st.sidebar.selectbox("Select Source", ["All Sources"] + list(unique_sources))
    
    # 3. Search Filter
    search_query = st.sidebar.text_input("Search News Title/Description")
    
    # Apply Filters
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

    st.subheader(f"Showing {len(filtered_df)} News Articles")

    # ---------------------------------------------------------
    # Display News Cards in BBC Format
    # ---------------------------------------------------------
    for index, row in filtered_df.iterrows():
        st.markdown(f"""
        <div class="bbc-news-container">
            <a href="{row['URL']}" target="_blank" class="bbc-news-title">{row['Title']}</a>
            <div class="bbc-news-meta"><strong>{row['Source']}</strong> &nbsp;|&nbsp; {row['Date'].strftime('%d %b %Y')}</div>
            <div class="bbc-news-desc">{row['Description']}</div>
        </div>
        """, unsafe_allow_html=True)
