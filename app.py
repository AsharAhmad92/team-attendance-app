import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

# 🚨 PASTE YOUR LINKS HERE
# 1. The "Publish to Web" CSV link (for READING)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7iiQmtnEj3GVbT1IhajMd3bndS1S9_HTrCn1cwqF9ZefnUwnvSX3WyBRSEdSGwtUTpqy1TRpTe3n8/pub?output=csv"
# 2. The Apps Script Web App URL (for WRITING)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzQJeisM-PeZmeJqyArPMiVj8fjqX39DtlIpBCd6jtXHZePgXcCezPCn6bArVoRC2Q/exec"

st.set_page_config(page_title="QA & Publishing Leave Manager", layout="wide")

# --- DATA LOADER ---
@st.cache_data(ttl=5) # Refresh every 5 seconds for "live" feel
def load_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_data()

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- SIDEBAR ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = False
if access_mode == "Manager/Admin":
    if st.sidebar.text_input("Admin Password", type="password") == ADMIN_PASSWORD:
        authenticated = True

# --- 1. TEAM MEMBER VIEW (The Request Form) ---
if access_mode == "Team Member":
    st.header("📝 Submit Leave Request")
    with st.form("request_form", clear_on_submit=True):
        u_name = st.selectbox("Your Name", TEAM_MEMBERS)
        u_date = st.date_input("Date Requested", datetime.now())
        
        if st.form_submit_button("Submit to Sheet"):
            # This is the "Magic" part that sends data to Google Sheets
            payload = {
                "name": u_name,
                "date": str(u_date),
                "status": "Pending Approval"
            }
            try:
                response = requests.post(SCRIPT_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"✅ Success! Request for {u_name} on {u_date} has been logged.")
                    st.balloons()
                else:
                    st.error("Submission failed. Check your Script URL.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 2. ATTENDANCE CHECK & CALENDAR (Manager & Team) ---
st.divider()
st.header("📊 Real-Time Coverage")

# Date picker for checking specific days
check_date = st.date_input("Check staffing for:", datetime.now())
date_str = str(check_date)

absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_list)

col1, col2 = st.columns(2)
col1.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")
if present_count < MIN_STAFF_REQUIRED:
    col2.error(f"⚠️ UNDERSTAFFED! (Min: {MIN_STAFF_REQUIRED})")
else:
    col2.success("✅ Staffing is sufficient.")

# Show the confirmed leave list
st.subheader("📅 Confirmed Approved Leaves")
approved_df = df_leave[df_leave["Status"] == "Approved"]
if not approved_df.empty:
    st.dataframe(approved_df.sort_values("Date"), use_container_width=True)
else:
    st.info("No approved leaves found.")

# Manager-only raw data view
if authenticated:
    st.divider()
    st.subheader("🔑 Manager Audit (All Data)")
    st.write("Edit the Google Sheet directly to Approve/Deny requests.")
    st.dataframe(df_leave)
