import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

# 🚨 LINKS
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7iiQmtnEj3GVbT1IhajMd3bndS1S9_HTrCn1cwqF9ZefnUwnvSX3WyBRSEdSGwtUTpqy1TRpTe3n8/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz11sgcmRRm55GWQYxU26BTkORTgeegLguJeNEsBgWu9ZNLAc9DUlsqhFg0s9MTr1C2/exec"

st.set_page_config(page_title="QA & Publishing Leave Manager", layout="wide")

# --- DATA LOADER ---
@st.cache_data(ttl=2) # Very low TTL to prevent ghost data
def load_data():
    try:
        # Cache busting: Adds a unique number to the URL so Google sends fresh data
        sep = "&" if "?" in SHEET_CSV_URL else "?"
        fresh_url = f"{SHEET_CSV_URL}{sep}cache_buster={time.time()}"
        return pd.read_csv(fresh_url)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Status"])

# Load data at start
df_leave = load_data()
# Ensure Date is always a string for matching logic
if not df_leave.empty:
    df_leave['Date'] = df_leave['Date'].astype(str)

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- SIDEBAR ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = False
if access_mode == "Manager/Admin":
    if st.sidebar.text_input("Admin Password", type="password") == ADMIN_PASSWORD:
        authenticated = True

# --- 1. TEAM MEMBER VIEW ---
if access_mode == "Team Member":
    tab1, tab2 = st.tabs(["📝 Request Leave", "🔄 Swap Marketplace"])
    
    with tab1:
        st.header("Submit Leave Request")
        with st.form("request_form", clear_on_submit=True):
            u_name = st.selectbox("Your Name", TEAM_MEMBERS)
            u_date = st.date_input("Date Requested", datetime.now())
            if st.form_submit_button("Submit to Manager"):
                payload = {"name": u_name, "date": str(u_date), "action": "add"}
                requests.post(SCRIPT_URL, json=payload)
                st.success("Sent to Manager!")
                time.sleep(1.5) # Wait for Google to write
                st.cache_data.clear()
                st.rerun()

    with tab2:
        st.header("Swap Your Approved Leave")
        st.info("To swap, select an approved leave you ALREADY have.")
        my_name = st.selectbox("Who are you?", TEAM_MEMBERS, key="swap_name")
        my_approved = df_leave[(df_leave["Name"] == my_name) & (df_leave["Status"] == "Approved")]
        
        if not my_approved.empty:
            with st.form("swap_form"):
                old_date = st.selectbox("Select Leave to Give Up", my_approved["Date"].tolist())
                new_date = st.date_input("Select New Date You Want")
                if st.form_submit_button("Request Swap"):
                    payload = {
                        "name": my_name,
                        "old_date": str(old_date),
                        "new_date": str(new_date),
                        "action": "swap"
                    }
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("Swap processed!")
                    time.sleep(2) # Swaps take longer to process in script
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning("No approved leaves to swap.")

# --- 2. MANAGER APPROVAL VIEW ---
if authenticated:
    st.divider()
    st.header("🔑 Manager Approval Queue")
    pending_df = df_leave[df_leave["Status"] == "Pending Approval"]
    
    if not pending_df.empty:
        for index, row in pending_df.iterrows():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"👤 {row['Name']}")
            c2.write(f"📅 {row['Date']}")
            if c3.button("Approve ✅", key=f"app_{index}"):
                payload = {"name": row['Name'], "date": row['Date'], "action": "approve"}
                with st.spinner("Writing to Google Sheets..."):
                    requests.post(SCRIPT_URL, json=payload)
                    time.sleep(2) # CRITICAL: Give Google time to save before reload
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("No pending requests.")

# --- 3. ATTENDANCE CHECK & CALENDAR ---
st.divider()
st.header("📊 Real-Time Coverage")

check_date = st.date_input("Check staffing for:", datetime.now(), key="check_date")
date_str = str(check_date)

absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_list)

col1, col2 = st.columns(2)
col1.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")
if present_count < MIN_STAFF_REQUIRED:
    col2.error(f"⚠️ UNDERSTAFFED! (Min: {MIN_STAFF_REQUIRED})")
else:
    col2.success("✅ Staffing is sufficient.")

st.subheader("📅 Confirmed Approved Leaves")
approved_df = df_leave[df_leave["Status"] == "Approved"]
if not approved_df.empty:
    st.dataframe(approved_df.sort_values("Date"), use_container_width=True)
else:
    st.info("No approved leaves found.")
