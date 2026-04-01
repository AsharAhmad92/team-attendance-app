import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
ADMIN_PASSWORD = "abc123"
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

# REPLACE THESE WITH YOUR ACTUAL LINKS
# To get the CSV_URL: Take your sheet link and replace everything after /edit... with /export?format=csv&gid=0
CSV_URL = "https://docs.google.com/spreadsheets/d/1Yk_QWEfgdGhQFQI3CKjTUHljRWj4ZScvBlBBVakOok8/edit/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzj1IO4lhK58iiKCRDkAEUa3ByzRJV2TO8oPNnhy_ubec793qAJDTXFryVoBnUnJteb/exec"

st.set_page_config(page_title="Team Leave Manager", layout="wide")

# --- DATA LOADER ---
def load_public_data():
    try:
        return pd.read_csv(CSV_URL)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_public_data()

# --- SIDEBAR ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = (access_mode == "Manager/Admin" and st.sidebar.text_input("Password", type="password") == ADMIN_PASSWORD)

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- ATTENDANCE CHECK ---
st.header("📊 Real-Time Attendance Check")
check_date = st.date_input("Select Date", datetime.now())
date_str = str(check_date)

absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_list)

c1, c2 = st.columns(2)
with c1:
    st.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")
with c2:
    if present_count < MIN_STAFF_REQUIRED:
        st.error(f"⚠️ UNDERSTAFFED!")
    else:
        st.success("✅ Sufficient Staff.")

st.divider()

# --- LOGIC: TEAM MEMBER REQUEST ---
if access_mode == "Team Member":
    with st.form("leave_entry"):
        u_name = st.selectbox("Your Name", TEAM_MEMBERS)
        u_date = st.date_input("Date Requested")
        if st.form_submit_button("Submit Request"):
            # Send data to the Google Apps Script
            payload = [u_name, str(u_date), "Pending Approval"]
            requests.post(f"{SCRIPT_URL}?sheet=Leaves", json=payload)
            st.success("Sent to Google Sheets!")
            st.rerun()

# --- LOGIC: MANAGER APPROVAL ---
elif authenticated:
    st.header("🔑 Manager Approval Queue")
    pending = df_leave[df_leave["Status"] == "Pending Approval"]
    
    if not pending.empty:
        for idx, row in pending.iterrows():
            if st.button(f"Approve {row['Name']} for {row['Date']}"):
                # Note: For 'Approving' via Public URL, it is easiest to 
                # manually change the status to "Approved" in the Google Sheet itself.
                st.info("Please open the Google Sheet and change 'Pending' to 'Approved' for this row.")
    else:
        st.info("No pending requests.")

# --- VIEW CALENDAR ---
st.divider()
st.subheader("📅 Approved Team Leave List")
st.dataframe(df_leave[df_leave["Status"] == "Approved"])
