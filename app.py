import os
import json
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------------------------------------
# Streamlit Configuration & Initialization
# ---------------------------------------------------------
st.set_page_config(page_title="Top News Dashboard", page_icon="📰", layout="wide")

st.title("📰 Daily Top News Dashboard")
st.markdown("Displays the latest top news automatically fetched every day and stored in Google Sheets.")

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
    # Display News Cards
    # ---------------------------------------------------------
    for index, row in filtered_df.iterrows():
        with st.container():
            st.markdown(f"### [{row['Title']}]({row['URL']})")
            st.caption(f"**Source:** {row['Source']} | **Date:** {row['Date'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
            st.write(row['Description'])
            st.markdown("---")
