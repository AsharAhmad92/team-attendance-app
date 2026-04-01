import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

st.set_page_config(page_title="QA & Publishing Team Leave Manager", layout="wide")

# --- GOOGLE SHEETS CONNECTION ---
# Connects using the [connections.gsheets] section in your Streamlit Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_all_data():
    try:
        # ttl=0 ensures we bypass the cache to see live updates from the team
        df_l = conn.read(worksheet="Leaves", ttl=0)
        df_s = conn.read(worksheet="Swaps", ttl=0)
        return df_l, df_s
    except Exception as e:
        st.error("Connection Error: Check if your Google Sheet has tabs named 'Leaves' and 'Swaps'.")
        return pd.DataFrame(columns=["Name", "Date", "Status"]), pd.DataFrame(columns=["Requester", "Date_To_Give", "Date_Wanted", "Status"])

df_leave, df_swaps = get_all_data()

# --- SIDEBAR AUTH ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = False
if access_mode == "Manager/Admin":
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    if pwd == ADMIN_PASSWORD: 
        authenticated = True
    elif pwd != "":
        st.sidebar.warning("Incorrect Password")

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- LIVE AVAILABILITY COUNTER ---
st.header("📊 Real-Time Attendance Check")
check_date = st.date_input("Select a date to check availability:", datetime.now())
date_str = str(check_date)

# Count only "Approved" leaves for that specific day
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
    
    # Section: Approve New Leaves
    pending_leaves = df_leave[df_leave["Status"] == "Pending Approval"]
    if not pending_leaves.empty:
        st.subheader("New Leave Requests")
        for idx, row in pending_leaves.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{row['Name']}** requested **{row['Date']}**")
            if col2.button("Approve ✅", key=f"lp_{idx}"):
                df_leave.at[idx, "Status"] = "Approved"
                conn.update(worksheet="Leaves", data=df_leave)
                st.rerun()
            if col3.button("Deny ❌", key=f"ld_{idx}"):
                df_leave = df_leave.drop(idx)
                conn.update(worksheet="Leaves", data=df_leave)
                st.rerun()
    
    # Section: Approve Peer Swaps
    pending_swaps = df_swaps[df_swaps["Status"] == "Awaiting Manager"]
    if not pending_swaps.empty:
        st.subheader("Peer Swap Approvals")
        for idx, row in pending_swaps.iterrows():
            st.write(f"**{row['Requester']}** wants to swap: Give up **{row['Date_To_Give']}** for **{row['Date_Wanted']}**")
            if st.button("Confirm Swap ✅", key=f"sw_{idx}"):
                # Logic: Remove the original leave date and add the new one as Approved
                df_leave = df_leave[~((df_leave['Name'] == row['Requester']) & (df_leave['Date'] == row['Date_To_Give']))]
                new_entry = pd.DataFrame([[row['Requester'], row['Date_Wanted'], "Approved"]], columns=["Name", "Date", "Status"])
                df_leave = pd.concat([df_leave, new_entry], ignore_index=True)
                
                # Update swap status to Completed
                df_swaps.at[idx, "Status"] = "Completed"
                
                # Sync both sheets
                conn.update(worksheet="Leaves", data=df_leave)
                conn.update(worksheet="Swaps", data=df_swaps)
                st.rerun()
    else:
        st.info("No pending approvals at the moment.")

# --- 2. TEAM MEMBER VIEW ---
elif access_mode == "Team Member":
    t1, t2 = st.tabs(["Request Leave", "Swap Marketplace"])
    
    with t1:
        with st.form("leave_entry"):
            u_name = st.selectbox("Your Name", TEAM_MEMBERS)
            u_date = st.date_input("Date Requested")
            if st.form_submit_button("Submit Request"):
                new_row = pd.DataFrame([[u_name, str(u_date), "Pending Approval"]], columns=["Name", "Date", "Status"])
                df_leave = pd.concat([df_leave, new_row], ignore_index=True)
                conn.update(worksheet="Leaves", data=df_leave)
                st.success(f"Request for {u_date} sent to Manager!")
                st.rerun()

    with t2:
        st.subheader("Post a Swap Request")
        with st.form("swap_entry"):
            s_name = st.selectbox("Who are you?", TEAM_MEMBERS)
            s_give = st.date_input("Date you are giving UP")
            s_want = st.date_input("Date you want INSTEAD")
            if st.form_submit_button("Post to Market"):
                new_s = pd.DataFrame([[s_name, str(s_give), str(s_want), "Pending"]], columns=["Requester", "Date_To_Give", "Date_Wanted", "Status"])
                df_swaps = pd.concat([df_swaps, new_s], ignore_index=True)
                conn.update(worksheet="Swaps", data=df_swaps)
                st.success("Swap posted to marketplace!")
                st.rerun()
        
        st.divider()
        st.subheader("Open Swaps")
        open_swaps = df_swaps[df_swaps["Status"] == "Pending"]
        if not open_swaps.empty:
            for idx, row in open_swaps.iterrows():
                if st.button(f"Accept: {row['Requester']} ({row['Date_To_Give']} ↔️ {row['Date_Wanted']})", key=f"s_{idx}"):
                    df_swaps.at[idx, "Status"] = "Awaiting Manager"
                    conn.update(worksheet="Swaps", data=df_swaps)
                    st.info("Accepted! Manager must now finalize this swap.")
                    st.rerun()
        else:
            st.write("No open swaps available.")

# --- 3. PUBLIC CALENDAR ---
st.divider()
st.subheader("📅 Approved Team Leave List")
if not df_leave.empty:
    approved_leaves = df_leave[df_leave["Status"] == "Approved"].sort_values("Date")
    if not approved_leaves.empty:
        st.dataframe(approved_leaves, use_container_width=True)
    else:
        st.write("No leaves approved yet.")
else:
    st.write("The database is currently empty.")
