import streamlit as st

import pandas as pd

import os

from datetime import datetime



# --- CONFIG ---

ADMIN_PASSWORD = "abc123" 

TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]

MIN_STAFF_REQUIRED = 3

LEAVE_DB = "leave_data.csv"

SWAP_DB = "swap_requests.csv"



# --- DATA LOADERS (Self-Healing) ---

def load_data(file, cols):

    if os.path.exists(file):

        df = pd.read_csv(file)

        for col in cols:

            if col not in df.columns: df[col] = "Pending"

        return df[cols]

    return pd.DataFrame(columns=cols)



df_leave = load_data(LEAVE_DB, ["Name", "Date", "Status"])

df_swaps = load_data(SWAP_DB, ["Requester", "Date_To_Give", "Date_Wanted", "Status"])



# --- SIDEBAR AUTH ---

st.sidebar.title("🔐 Access Control")

access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])

authenticated = False

if access_mode == "Manager/Admin":

    pwd = st.sidebar.text_input("Enter Admin Password", type="password")

    if pwd == ADMIN_PASSWORD: authenticated = True



st.title("🛡️ QA & Publishing Team Leave Manager")



# --- NEW: LIVE AVAILABILITY COUNTER ---

st.header("📊 Real-Time Attendance Check")

check_date = st.date_input("Select a date to check availability:", datetime.now())

date_str = str(check_date)



# Count only "Approved" leaves for that day

absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()

present_count = len(TEAM_MEMBERS) - len(absent_list)



c1, c2 = st.columns(2)

with c1:

    st.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")

with c2:

    if present_count < MIN_STAFF_REQUIRED:

        st.error(f"⚠️ UNDERSTAFFED! Min required: {MIN_STAFF_REQUIRED}")

    else:

        st.success("✅ Sufficient Team Members Available.")



if absent_list:

    st.info(f"Confirmed Absent: {', '.join(absent_list)}")



st.divider()



# --- 1. MANAGER VIEW ---

if access_mode == "Manager/Admin" and authenticated:

    st.header("🔑 Manager Approval Queue")

    

    # Approve New Leaves

    pending_leaves = df_leave[df_leave["Status"] == "Pending Approval"]

    if not pending_leaves.empty:

        st.subheader("New Leave Requests")

        for idx, row in pending_leaves.iterrows():

            col1, col2, col3 = st.columns([3, 1, 1])

            col1.write(f"**{row['Name']}** requested **{row['Date']}**")

            if col2.button("Approve ✅", key=f"lp_{idx}"):

                df_leave.at[idx, "Status"] = "Approved"; df_leave.to_csv(LEAVE_DB, index=False); st.rerun()

            if col3.button("Deny ❌", key=f"ld_{idx}"):

                df_leave = df_leave.drop(idx); df_leave.to_csv(LEAVE_DB, index=False); st.rerun()

    

    # Approve Swaps

    pending_swaps = df_swaps[df_swaps["Status"] == "Awaiting Manager"]

    if not pending_swaps.empty:

        st.subheader("Peer Swap Approvals")

        for idx, row in pending_swaps.iterrows():

            st.write(f"**{row['Requester']}** wants to swap: Give up **{row['Date_To_Give']}** for **{row['Date_Wanted']}**")

            if st.button("Confirm Swap ✅", key=f"sw_{idx}"):

                # Update Leave Table: Remove old, add new

                df_leave = df_leave[~((df_leave['Name'] == row['Requester']) & (df_leave['Date'] == row['Date_To_Give']))]

                new_entry = pd.DataFrame([[row['Requester'], row['Date_Wanted'], "Approved"]], columns=["Name", "Date", "Status"])

                df_leave = pd.concat([df_leave, new_entry])

                df_swaps.at[idx, "Status"] = "Completed"

                df_leave.to_csv(LEAVE_DB, index=False); df_swaps.to_csv(SWAP_DB, index=False); st.rerun()



# --- 2. TEAM MEMBER VIEW ---

elif access_mode == "Team Member":

    t1, t2 = st.tabs(["Request Leave", "Swap Marketplace"])

    with t1:

        with st.form("leave_entry"):

            u_name = st.selectbox("Your Name", TEAM_MEMBERS)

            u_date = st.date_input("Date Requested")

            if st.form_submit_button("Submit Request"):

                new_row = pd.DataFrame([[u_name, str(u_date), "Pending Approval"]], columns=["Name", "Date", "Status"])

                df_leave = pd.concat([df_leave, new_row],
