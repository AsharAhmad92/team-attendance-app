import streamlit as st
import pandas as pd
import os

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
LEAVE_DB = "leave_data.csv"
SWAP_DB = "swap_requests.csv"

# --- DATA LOADERS ---
def load_leave_data():
    cols = ["Name", "Date", "Status"]
    if os.path.exists(LEAVE_DB):
        df = pd.read_csv(LEAVE_DB)
        for col in cols:
            if col not in df.columns: df[col] = "Approved"
        return df[cols]
    return pd.DataFrame(columns=cols)

def load_swap_data():
    cols = ["Requester", "Date_To_Give", "Date_Wanted", "Status"]
    if os.path.exists(SWAP_DB):
        df = pd.read_csv(SWAP_DB)
        for col in cols:
            if col not in df.columns: df[col] = "Pending"
        return df[cols]
    return pd.DataFrame(columns=cols)

df_leave = load_leave_data()
df_swaps = load_swap_data()

# --- SIDEBAR AUTH ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = False
if access_mode == "Manager/Admin":
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    if pwd == ADMIN_PASSWORD: authenticated = True

st.title("🛡️ Content Team Leave & Swap Manager")

# --- 1. MANAGER VIEW ---
if access_mode == "Manager/Admin" and authenticated:
    st.header("🔑 Manager Approval Queue")
    
    # Approve New Leaves
    pending_leaves = df_leave[df_leave["Status"] == "Pending Approval"]
    if not pending_leaves.empty:
        st.subheader("New Leave Requests")
        for idx, row in pending_leaves.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{row['Name']}** requested **{row['Date']}**")
            if c2.button("Approve ✅", key=f"lp_{idx}"):
                df_leave.at[idx, "Status"] = "Approved"; df_leave.to_csv(LEAVE_DB, index=False); st.rerun()
            if c3.button("Deny ❌", key=f"ld_{idx}"):
                df_leave = df_leave.drop(idx); df_leave.to_csv(LEAVE_DB, index=False); st.rerun()
    
    # Approve Swaps
    pending_swaps = df_swaps[df_swaps["Status"] == "Awaiting Manager"]
    if not pending_swaps.empty:
        st.subheader("Peer Swap Requests")
        for idx, row in pending_swaps.iterrows():
            st.write(f"**{row['Requester']}** swapped with a teammate: Give **{row['Date_To_Give']}** / Take **{row['Date_Wanted']}**")
            if st.button("Confirm Swap ✅", key=f"sw_{idx}"):
                # Logic: Remove the old leave date, add the new approved date
                df_leave = df_leave[~((df_leave['Name'] == row['Requester']) & (df_leave['Date'] == row['Date_To_Give']))]
                new_entry = pd.DataFrame([[row['Requester'], row['Date_Wanted'], "Approved"]], columns=["Name", "Date", "Status"])
                df_leave = pd.concat([df_leave, new_entry])
                df_swaps.at[idx, "Status"] = "Completed"
                df_leave.to_csv(LEAVE_DB, index=False); df_swaps.to_csv(SWAP_DB, index=False); st.rerun()

# --- 2. TEAM MEMBER VIEW ---
elif access_mode == "Team Member":
    tab1, tab2 = st.tabs(["Request Leave", "Swap Marketplace"])
    
    with tab1:
        with st.form("leave_entry"):
            name = st.selectbox("Your Name", TEAM_MEMBERS)
            date = st.date_input("Choose Date")
            if st.form_submit_button("Submit Request"):
                new_row = pd.DataFrame([[name, str(date), "Pending Approval"]], columns=["Name", "Date", "Status"])
                df_leave = pd.concat([df_leave, new_row], ignore_index=True)
                df_leave.to_csv(LEAVE_DB, index=False); st.success("Sent to Manager!"); st.rerun()

    with tab2:
        st.subheader("Post a Swap Request")
        with st.form("swap_entry"):
            s_name = st.selectbox("Who are you?", TEAM_MEMBERS)
            s_give = st.date_input("Date you are giving UP")
            s_want = st.date_input("Date you want INSTEAD")
            if st.form_submit_button("Post to Market"):
                new_swap = pd.DataFrame([[s_name, str(s_give), str(s_want), "Pending"]], columns=["Requester", "Date_To_Give", "Date_Wanted", "Status"])
                df_swaps = pd.concat([df_swaps, new_swap], ignore_index=True)
                df_swaps.to_csv(SWAP_DB, index=False); st.success("Swap posted!"); st.rerun()
        
        st.divider()
        st.subheader("Available Swaps")
        open_swaps = df_swaps[df_swaps["Status"] == "Pending"]
        for idx, row in open_swaps.iterrows():
            if st.button(f"Accept: {row['Requester']} gives {row['Date_To_Give']} for {row['Date_Wanted']}", key=f"op_{idx}"):
                df_swaps.at[idx, "Status"] = "Awaiting Manager"
                df_swaps.to_csv(SWAP_DB, index=False); st.info("Accepted! Now waiting for Manager to finalize."); st.rerun()

# --- 3. PUBLIC CALENDAR ---
st.divider()
st.header("📅 Approved Team Schedule")
confirmed = df_leave[df_leave["Status"] == "Approved"]
if not confirmed.empty:
    st.dataframe(confirmed.sort_values("Date"), use_container_width=True)
else:
    st.info("No approved leaves yet.")
