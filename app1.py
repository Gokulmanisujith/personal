import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from datetime import date

# Backend URL
BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Personal Expense Analyser", layout="wide")

# Sidebar Navigation
st.sidebar.title("ExpenseTracker")
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Debts & Loans", "Reminders", "AI Assistant"]
)

# Function to fetch data from backend
def fetch_data(endpoint: str):
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error {response.status_code}: Could not fetch {endpoint}")
            return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ------------------- 1. Dashboard ------------------- #
if menu == "Dashboard":
    st.title("ExpenseTracker")
    st.caption(datetime.now().strftime("%A %d %B, %Y"))

    # Function to add transaction to backend
    def add_transaction_to_backend(payload):
        """Send transaction data to backend"""
        try:
            response = requests.post(f"{BASE_URL}/add_transaction", json=payload)
            if response.status_code == 200:
                st.success("Transaction added successfully!")
                return True
            else:
                st.error(f"Error: {response.text}")
                return False
        except Exception as e:
            st.error(f"Error: {e}")
            return False

    # Function to fetch dashboard data
    def fetch_dashboard_data():
        summary = fetch_data("overall") or {}
        category_data = fetch_data("by_category") or {}
        trend_data = fetch_data("monthly_trends") or []
        return summary, category_data, trend_data

    # Fetch initial data
    col1, col2, col3 = st.columns(3)
    main_placeholder = col1.empty()
    savings_placeholder = col2.empty()
    spent_placeholder = col3.empty()

    # Function to update metrics
    def update_metrics(summary):
        main_placeholder.metric("Main Account", f"₹{summary.get('Total Income', 0):,.2f}")
        savings_placeholder.metric("Savings Account", f"₹{summary.get('Net Savings', 0):,.2f}")
        spent_placeholder.metric("This Month Spent", f"₹{summary.get('Total Expense', 0):,.2f}")

    # Initial load
    summary, category_data, trend_data = fetch_dashboard_data()
    update_metrics(summary)
    # ---------------- Quick Actions ---------------- #
    st.markdown("### Quick Actions")
    col1, col2 = st.columns(2)

    # Add Expense Form
    with col1:
        with st.form("expense_form", clear_on_submit=True):
            st.markdown("### ➕ Add Expense")
            description = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.0, step=10.0)
            merchant = st.text_input("Merchant (optional)")
            payment_method = st.selectbox("Payment Method", ["UPI", "ATM", "NEFT", "Other"])
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                payload = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Description": description,
                    "Amount": -abs(amount),  # Expense is negative
                    "Merchant": merchant or None,
                    "Payment_method": payment_method
                }
                if add_transaction_to_backend(payload):
                    summary, category_data, trend_data = fetch_dashboard_data()  # Refresh data
                    update_metrics(summary)

    # Add Income Form
    with col2:
        with st.form("income_form", clear_on_submit=True):
            st.markdown("### ➕ Add Income")
            description = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.0, step=10.0)
            merchant = st.text_input("Merchant (optional)")
            payment_method = st.selectbox("Payment Method", ["UPI", "ATM", "NEFT", "Other"])
            submitted = st.form_submit_button("Add Income")
            if submitted:
                payload = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Description": description,
                    "Amount": abs(amount),  # Income is positive
                    "Merchant": merchant or None,
                    "Payment_method": payment_method
                }
                if add_transaction_to_backend(payload):
                    summary, category_data, trend_data = fetch_dashboard_data()  # Refresh data
                    update_metrics(summary)
   

    st.markdown("---")

    # ---------------- Spending Analytics Section ---------------- #
    st.subheader("📊 Spending Overview")
    col1, col2 = st.columns(2)

    # Pie Chart (Category Breakdown)
    with col1:
        if category_data and len(category_data) > 0:
            df_cat = pd.DataFrame(list(category_data.items()), columns=["Category", "Total Spent"])
            fig = px.pie(df_cat, names="Category", values="Total Spent", hole=0.3,
                         title="Category Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available")

    # Bar Chart (Monthly Spending Trends)
    with col2:
        if trend_data and len(trend_data) > 0:
            df_trend = pd.DataFrame(trend_data)
            df_trend.rename(columns={"AbsAmount": "Total Spent"}, inplace=True)
            df_trend["Month"] = pd.to_datetime(df_trend["Month"])
            fig = px.bar(df_trend, x="Month", y="Total Spent",
                         title="Monthly Spending Trend")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available")



# ------------------- 3. Debts & Loans ------------------- #
elif menu == "Debts & Loans":
    st.title("💰 Debts & Loans")

    # Fetch debts from backend
    def fetch_debts():
        expected_cols = ["person", "amount", "type", "due_date", "notes"]
        try:
            response = requests.get(f"{BASE_URL}/debts")
            if response.status_code == 200:
                data = response.json()
            if data:  # not empty
                df = pd.DataFrame(data)
                # Ensure all expected columns exist
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = None
                return df[expected_cols]
            # If empty or not 200 → return empty DF with correct columns
            return pd.DataFrame(columns=expected_cols)
        except Exception as e:
            st.error(f"Error fetching debts: {e}")
        return pd.DataFrame(columns=expected_cols)


    debts_df = fetch_debts()

    # Summary
    total_owe = debts_df[debts_df["type"] == "owe"]["amount"].sum()
    total_owed = debts_df[debts_df["type"] == "owed"]["amount"].sum()
    net_balance = total_owed - total_owe

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("You Owe", f"₹{total_owe}")
    with col2:
        st.metric("Owed to You", f"₹{total_owed}")
    with col3:
        st.metric("Net Balance", f"₹{net_balance}")

    # Active Debts section
    st.markdown("### 📌 Active Debts & Loans")

    if not debts_df.empty:
        st.dataframe(debts_df)
    else:
        st.info("No active debts. Add a debt record to get started.")

    # Add Debt Form
    with st.expander("➕ Add Debt"):
        with st.form("add_debt_form", clear_on_submit=True):
            person = st.text_input("Person Name")
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            debt_type = st.selectbox("Type", ["owe", "owed"])
            due_date = st.date_input("Due Date", value=date.today())
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save")
            if submitted:
                payload = {
                    "person": person,
                    "amount": amount,
                    "type": debt_type,
                    "due_date": str(due_date),
                    "notes": notes,
                }
                res = requests.post(f"{BASE_URL}/debts", json=payload)
                if res.status_code == 200:
                    st.success("✅ Debt/Loan added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add debt")


# ------------------- 4. Reminders ------------------- #
elif menu == "Reminders":
    st.title("⏰ Reminders")

    # Fetch existing reminders
    reminders = requests.get(f"{BASE_URL}/reminders").json()
    reminders_df = pd.DataFrame(reminders)

    st.subheader("📌 Upcoming Reminders")
    if not reminders_df.empty:
        st.table(reminders_df)
    else:
        st.info("No upcoming reminders. Add a reminder to get started.")

    with st.expander("➕ Add Reminder"):
        with st.form("reminder_form"):
            title = st.text_input("Reminder Title")
            date = st.date_input("Date")
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            time = st.time_input("Time")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Add Reminder")
            if submitted:
                new_reminder = {
                    "title": title,
                    "date": str(date),
                    "time": str(time),
                    "Amount":amount,
                    "notes": notes,
                }
                res = requests.post(f"{BASE_URL}/add_reminder", json=new_reminder)
                if res.status_code == 200:
                    st.success("✅ Reminder added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add reminder")


# ------------------- 5. AI Assistant ------------------- #
elif menu == "AI Assistant":
    st.title("💬 Personal Finance Chatbot (Bard AI)")

    # Initialize chat history once
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        # Add greeting message only the first time
        st.session_state.chat_history.append(("Bot", "Hey hi! how can I help you"))

    # User input box
    user_input = st.chat_input("Ask me about your expenses, debts, or reminders...")

    if user_input:
        # Call backend
        try:
            res = requests.post(f"{BASE_URL}/chatbot", json={"message": user_input})
            if res.status_code == 200:
                bot_reply = res.json().get("response", "⚠️ No response key in JSON")
            else:
                bot_reply = f"⚠️ Backend error {res.status_code}: {res.text}"
        except Exception as e:
            bot_reply = f"⚠️ Connection error: {e}"

        # Save conversation
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", bot_reply))

    # Display chat
    for role, text in st.session_state.chat_history:
        if role == "You":
            st.markdown(f"🧑 **{role}:** {text}")
        else:
            st.markdown(f"🤖 **{role}:** {text}")
