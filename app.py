import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

# 🚨 PASTE YOUR PUBLISHED CSV LINK HERE
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7iiQmtnEj3GVbT1IhajMd3bndS1S9_HTrCn1cwqF9ZefnUwnvSX3WyBRSEdSGwtUTpqy1TRpTe3n8/pub?output=csv"

st.set_page_config(page_title="QA & Publishing Leave Manager", layout="wide")

# --- DATA LOADER ---
@st.cache_data(ttl=10) # Refreshes every 10 seconds
def load_data():
    try:
        # Pulls live data from the published Google Sheet
        return pd.read_csv(SHEET_CSV_URL)
    except Exception as e:
        st.error("Cannot connect to Google Sheets. Check if 'Publish to Web' is active.")
        return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_data()

# --- SIDEBAR ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = False
if access_mode == "Manager/Admin":
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        authenticated = True

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- ATTENDANCE CHECK ---
st.header("📊 Real-Time Attendance Check")
check_date = st.date_input("Check date:", datetime.now())
date_str = str(check_date)

# Filters
absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_list)

c1, c2 = st.columns(2)
with c1:
    st.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")
with c2:
    if present_count < MIN_STAFF_REQUIRED:
        st.error(f"⚠️ UNDERSTAFFED! Min: {MIN_STAFF_REQUIRED}")
    else:
        st.success("✅ Staffing OK.")

st.divider()

# --- TEAM MEMBER VIEW ---
if access_mode == "Team Member":
    st.subheader("📝 Submit New Request")
    st.info("Note: Requests are saved to the Google Sheet. Use the link below to add your entry.")
    
    # Since we aren't using a JSON key to write, we provide a direct link to the sheet
    sheet_edit_url = SHEET_CSV_URL.split("/pub")[0] # Trims to the main sheet link
    st.markdown(f"[👉 Click here to open the Google Sheet and add your request]({sheet_edit_url})")
    
    st.write("---")
    st.write("### Current Pending Requests")
    pending = df_leave[df_leave["Status"] == "Pending Approval"]
    if not pending.empty:
        st.table(pending)
    else:
        st.write("No pending requests.")

# --- MANAGER VIEW ---
elif authenticated:
    st.header("🔑 Manager Approval Dashboard")
    st.write("To approve or deny, please edit the 'Status' column directly in Google Sheets.")
    
    pending = df_leave[df_leave["Status"] == "Pending Approval"]
    if not pending.empty:
        st.dataframe(pending, use_container_width=True)
    else:
        st.success("All requests handled!")

# --- PUBLIC CALENDAR ---
st.divider()
st.subheader("📅 Approved Team Leave List")
approved = df_leave[df_leave["Status"] == "Approved"]
if not approved.empty:
    st.dataframe(approved.sort_values("Date"), use_container_width=True)
else:
    st.info("No approved leaves found.")
