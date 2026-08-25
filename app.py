import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# DIGITAL PAYMENT TRANSACTION TRENDS DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Digital Payment Transaction Trends Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main {
        background-color: #f5f7fb;
    }

    .dashboard-title {
        font-size: 34px;
        font-weight: 700;
        text-align: center;
        color: #1f2937;
        margin-bottom: 5px;
    }

    .dashboard-subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 600;
        color: #111827;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .info-box {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="dashboard-title">💳 Digital Payment Transaction Trends Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'UPI Transaction Analysis Dashboard – 2024'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# LOAD DATA
# IMPORTANT:
# Keep upi_transactions_2024_cleaned.csv.gz in the same
# GitHub folder as app.py
# ============================================================

@st.cache_data
def load_data():

    file_path = "upi_transactions_2024_cleaned.csv.gz"

    df = pd.read_csv(
        file_path,
        compression="gzip",
        low_memory=False
    )

    # Convert date/time
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # Numeric columns
    df["amount_inr"] = pd.to_numeric(
        df["amount_inr"],
        errors="coerce"
    )

    df["hour_of_day"] = pd.to_numeric(
        df["hour_of_day"],
        errors="coerce"
    )

    df["fraud_flag"] = pd.to_numeric(
        df["fraud_flag"],
        errors="coerce"
    ).fillna(0)

    df["is_weekend"] = pd.to_numeric(
        df["is_weekend"],
        errors="coerce"
    ).fillna(0)

    # Clean text columns
    text_columns = [
        "transaction_type",
        "merchant_category",
        "transaction_status",
        "sender_age_group",
        "receiver_age_group",
        "sender_state",
        "sender_bank",
        "receiver_bank",
        "device_type",
        "network_type",
        "day_of_week"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.lower()
            )

    # Remove invalid rows
    df.dropna(
        subset=[
            "timestamp",
            "amount_inr",
            "transaction_status"
        ],
        inplace=True
    )

    return df


try:
    df = load_data()

except FileNotFoundError:
    st.error(
        "Dataset not found. Make sure "
        "'upi_transactions_2024_cleaned.csv.gz' "
        "is in the same GitHub repository folder as app.py."
    )
    st.stop()

except Exception as e:
    st.error(f"Unable to load dataset: {e}")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔎 Dashboard Filters")

st.sidebar.write(
    "Use the filters below to interact with the dashboard."
)

# ------------------------------------------------------------
# Transaction Type
# ------------------------------------------------------------

transaction_types = sorted(
    df["transaction_type"].dropna().unique()
)

selected_transaction_types = st.sidebar.multiselect(
    "Transaction Type",
    options=transaction_types,
    default=transaction_types
)

# ------------------------------------------------------------
# Sender State
# ------------------------------------------------------------

states = sorted(
    df["sender_state"].dropna().unique()
)

selected_states = st.sidebar.multiselect(
    "Sender State",
    options=states,
    default=states
)

# ------------------------------------------------------------
# Transaction Status
# ------------------------------------------------------------

statuses = sorted(
    df["transaction_status"].dropna().unique()
)

selected_statuses = st.sidebar.multiselect(
    "Transaction Status",
    options=statuses,
    default=statuses
)

# ------------------------------------------------------------
# Device Type
# ------------------------------------------------------------

devices = sorted(
    df["device_type"].dropna().unique()
)

selected_devices = st.sidebar.multiselect(
    "Device Type",
    options=devices,
    default=devices
)

# ------------------------------------------------------------
# Network Type
# ------------------------------------------------------------

networks = sorted(
    df["network_type"].dropna().unique()
)

selected_networks = st.sidebar.multiselect(
    "Network Type",
    options=networks,
    default=networks
)

# ------------------------------------------------------------
# Date Range
# ------------------------------------------------------------

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

selected_dates = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()

if selected_transaction_types:
    filtered_df = filtered_df[
        filtered_df["transaction_type"].isin(
            selected_transaction_types
        )
    ]

if selected_states:
    filtered_df = filtered_df[
        filtered_df["sender_state"].isin(
            selected_states
        )
    ]

if selected_statuses:
    filtered_df = filtered_df[
        filtered_df["transaction_status"].isin(
            selected_statuses
        )
    ]

if selected_devices:
    filtered_df = filtered_df[
        filtered_df["device_type"].isin(
            selected_devices
        )
    ]

if selected_networks:
    filtered_df = filtered_df[
        filtered_df["network_type"].isin(
            selected_networks
        )
    ]

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:

    start_date, end_date = selected_dates

    filtered_df = filtered_df[
        (filtered_df["timestamp"].dt.date >= start_date)
        &
        (filtered_df["timestamp"].dt.date <= end_date)
    ]

# ============================================================
# EMPTY DATA CHECK
# ============================================================

if filtered_df.empty:

    st.warning(
        "No transactions match the selected filters. "
        "Please change the filters."
    )

    st.stop()

# ============================================================
# KPI CALCULATIONS
# ============================================================

total_transactions = len(filtered_df)

total_amount = filtered_df["amount_inr"].sum()

successful_transactions = (
    filtered_df["transaction_status"]
    .str.lower()
    .eq("success")
    .sum()
)

failed_transactions = (
    total_transactions -
    successful_transactions
)

success_rate = (
    successful_transactions /
    total_transactions *
    100
)

failure_rate = (
    failed_transactions /
    total_transactions *
    100
)

fraud_transactions = (
    filtered_df["fraud_flag"]
    .astype(int)
    .sum()
)

fraud_rate = (
    fraud_transactions /
    total_transactions *
    100
)

average_transaction = (
    filtered_df["amount_inr"].mean()
)

# ============================================================
# KPI CARDS
# ============================================================

st.markdown(
    '<div class="section-title">📊 Key Performance Indicators</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Transactions",
        f"{total_transactions:,}"
    )

with col2:
    st.metric(
        "Total Transaction Value",
        f"₹{total_amount:,.0f}"
    )

with col3:
    st.metric(
        "Success Rate",
        f"{success_rate:.2f}%"
    )

with col4:
    st.metric(
        "Failure Rate",
        f"{failure_rate:.2f}%"
    )

with col5:
    st.metric(
        "Fraud Transactions",
        f"{fraud_transactions:,}"
    )

# ============================================================
# ADDITIONAL KPI ROW
# ============================================================

col6, col7, col8 = st.columns(3)

with col6:
    st.metric(
        "Average Transaction",
        f"₹{average_transaction:,.2f}"
    )

with col7:
    st.metric(
        "Failed Transactions",
        f"{failed_transactions:,}"
    )

with col8:
    st.metric(
        "Fraud Rate",
        f"{fraud_rate:.2f}%"
    )

# ============================================================
# 1. SUCCESS RATE BY PAYMENT METHOD
# ============================================================

st.markdown(
    '<div class="section-title">'
    '1. Success Rate by Payment Method'
    '</div>',
    unsafe_allow_html=True
)

success_rate_df = (
    filtered_df
    .groupby("transaction_type")["transaction_status"]
    .apply(
        lambda x:
        (x.str.lower() == "success").mean() * 100
    )
    .reset_index(
        name="success_rate"
    )
    .sort_values(
        "success_rate",
        ascending=False
    )
)

fig1 = px.bar(
    success_rate_df,
    x="transaction_type",
    y="success_rate",
    text="success_rate",
    title="Success Rate by Payment Method",
    labels={
        "transaction_type": "Payment Method",
        "success_rate": "Success Rate (%)"
    }
)

fig1.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig1.update_yaxes(range=[0, 100])

st.plotly_chart(
    fig1,
    use_container_width=True
)

# ============================================================
# 2. FAILURE RATE BY PAYMENT METHOD
# ============================================================

st.markdown(
    '<div class="section-title">'
    '2. Failure Rate by Transaction Method'
    '</div>',
    unsafe_allow_html=True
)

failure_rate_df = (
    filtered_df
    .groupby("transaction_type")["transaction_status"]
    .apply(
        lambda x:
        (x.str.lower() != "success").mean() * 100
    )
    .reset_index(
        name="failure_rate"
    )
    .sort_values(
        "failure_rate",
        ascending=False
    )
)

fig2 = px.bar(
    failure_rate_df,
    x="transaction_type",
    y="failure_rate",
    text="failure_rate",
    title="Failure Rate by Transaction Method",
    labels={
        "transaction_type": "Transaction Method",
        "failure_rate": "Failure Rate (%)"
    }
)

fig2.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# ============================================================
# 3. TRANSACTIONS BY AGE GROUP
# ============================================================

st.markdown(
    '<div class="section-title">'
    '3. Transactions by Sender Age Group'
    '</div>',
    unsafe_allow_html=True
)

age_group_counts = (
    filtered_df["sender_age_group"]
    .value_counts()
    .reset_index()
)

age_group_counts.columns = [
    "age_group",
    "transaction_count"
]

fig3 = px.bar(
    age_group_counts,
    x="age_group",
    y="transaction_count",
    text="transaction_count",
    title="Transaction Count by Sender Age Group",
    labels={
        "age_group": "Age Group",
        "transaction_count": "Transactions"
    }
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# ============================================================
# 4. TRANSACTION TYPE DISTRIBUTION
# ============================================================

st.markdown(
    '<div class="section-title">'
    '4. Transaction Type Distribution'
    '</div>',
    unsafe_allow_html=True
)

transaction_distribution = (
    filtered_df["transaction_type"]
    .value_counts()
    .reset_index()
)

transaction_distribution.columns = [
    "transaction_type",
    "count"
]

fig4 = px.pie(
    transaction_distribution,
    names="transaction_type",
    values="count",
    hole=0.45,
    title="Distribution of Transaction Types"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

# ============================================================
# 5. MERCHANT CATEGORY
# ============================================================

st.markdown(
    '<div class="section-title">'
    '5. Transactions by Merchant Category'
    '</div>',
    unsafe_allow_html=True
)

merchant_df = (
    filtered_df["merchant_category"]
    .value_counts()
    .reset_index()
)

merchant_df.columns = [
    "merchant_category",
    "count"
]

fig5 = px.bar(
    merchant_df.head(10),
    x="count",
    y="merchant_category",
    orientation="h",
    text="count",
    title="Top Merchant Categories",
    labels={
        "merchant_category": "Merchant Category",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig5,
    use_container_width=True
)

# ============================================================
# 6. TRANSACTIONS BY STATE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '6. Transactions by Sender State'
    '</div>',
    unsafe_allow_html=True
)

state_df = (
    filtered_df["sender_state"]
    .value_counts()
    .reset_index()
)

state_df.columns = [
    "sender_state",
    "count"
]

fig6 = px.bar(
    state_df.head(10),
    x="sender_state",
    y="count",
    text="count",
    title="Top Sender States by Transaction Volume",
    labels={
        "sender_state": "State",
        "count": "Transactions"
    }
)

fig6.update_layout(
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig6,
    use_container_width=True
)

# ============================================================
# 7. DEVICE TYPE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '7. Transactions by Device Type'
    '</div>',
    unsafe_allow_html=True
)

device_df = (
    filtered_df["device_type"]
    .value_counts()
    .reset_index()
)

device_df.columns = [
    "device_type",
    "count"
]

fig7 = px.pie(
    device_df,
    names="device_type",
    values="count",
    hole=0.4,
    title="Transactions by Device Type"
)

st.plotly_chart(
    fig7,
    use_container_width=True
)

# ============================================================
# 8. NETWORK TYPE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '8. Transactions by Network Type'
    '</div>',
    unsafe_allow_html=True
)

network_df = (
    filtered_df["network_type"]
    .value_counts()
    .reset_index()
)

network_df.columns = [
    "network_type",
    "count"
]

fig8 = px.bar(
    network_df,
    x="network_type",
    y="count",
    text="count",
    title="Transactions by Network Type",
    labels={
        "network_type": "Network Type",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig8,
    use_container_width=True
)

# ============================================================
# 9. HOURLY TRANSACTION TREND
# ============================================================

st.markdown(
    '<div class="section-title">'
    '9. Transaction Activity by Hour'
    '</div>',
    unsafe_allow_html=True
)

hour_df = (
    filtered_df
    .groupby("hour_of_day")
    .size()
    .reset_index(
        name="transaction_count"
    )
)

hour_df["hour_of_day"] = (
    hour_df["hour_of_day"]
    .astype(int)
)

hour_df = hour_df.sort_values(
    "hour_of_day"
)

fig9 = px.line(
    hour_df,
    x="hour_of_day",
    y="transaction_count",
    markers=True,
    title="Transaction Activity by Hour of Day",
    labels={
        "hour_of_day": "Hour of Day",
        "transaction_count": "Transactions"
    }
)

st.plotly_chart(
    fig9,
    use_container_width=True
)

# ============================================================
# 10. DAY OF WEEK
# ============================================================

st.markdown(
    '<div class="section-title">'
    '10. Transactions by Day of Week'
    '</div>',
    unsafe_allow_html=True
)

day_order = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
]

day_df = (
    filtered_df["day_of_week"]
    .value_counts()
    .reindex(day_order)
    .fillna(0)
    .reset_index()
)

day_df.columns = [
    "day_of_week",
    "count"
]

fig10 = px.bar(
    day_df,
    x="day_of_week",
    y="count",
    text="count",
    title="Transaction Volume by Day of Week",
    labels={
        "day_of_week": "Day",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig10,
    use_container_width=True
)

# ============================================================
# 11. MONTHLY TRANSACTION TREND
# ============================================================

st.markdown(
    '<div class="section-title">'
    '11. Monthly Transaction Trend'
    '</div>',
    unsafe_allow_html=True
)

monthly_df = (
    filtered_df
    .assign(
        month=filtered_df["timestamp"].dt.to_period("M")
    )
    .groupby("month")
    .agg(
        transactions=("transaction_id", "count"),
        total_value=("amount_inr", "sum")
    )
    .reset_index()
)

monthly_df["month"] = (
    monthly_df["month"].astype(str)
)

fig11 = px.line(
    monthly_df,
    x="month",
    y="transactions",
    markers=True,
    title="Monthly Transaction Volume",
    labels={
        "month": "Month",
        "transactions": "Transactions"
    }
)

st.plotly_chart(
    fig11,
    use_container_width=True
)

# ============================================================
# 12. MONTHLY TRANSACTION VALUE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '12. Monthly Transaction Value'
    '</div>',
    unsafe_allow_html=True
)

fig12 = px.bar(
    monthly_df,
    x="month",
    y="total_value",
    text="total_value",
    title="Monthly Transaction Value",
    labels={
        "month": "Month",
        "total_value": "Transaction Value (₹)"
    }
)

fig12.update_traces(
    texttemplate="₹%{text:,.0f}",
    textposition="outside"
)

st.plotly_chart(
    fig12,
    use_container_width=True
)

# ============================================================
# 13. FRAUD ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '13. Fraud Analysis'
    '</div>',
    unsafe_allow_html=True
)

fraud_df = (
    filtered_df["fraud_flag"]
    .value_counts()
    .reset_index()
)

fraud_df.columns = [
    "fraud_flag",
    "count"
]

fraud_df["fraud_status"] = fraud_df[
    "fraud_flag"
].map({
    0: "Non-Fraud",
    1: "Fraud"
})

fig13 = px.pie(
    fraud_df,
    names="fraud_status",
    values="count",
    hole=0.45,
    title="Fraud vs Non-Fraud Transactions"
)

st.plotly_chart(
    fig13,
    use_container_width=True
)

# ============================================================
# 14. SENDER BANK ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '14. Sender Bank Analysis'
    '</div>',
    unsafe_allow_html=True
)

bank_df = (
    filtered_df["sender_bank"]
    .value_counts()
    .reset_index()
)

bank_df.columns = [
    "sender_bank",
    "count"
]

fig14 = px.bar(
    bank_df.head(10),
    x="sender_bank",
    y="count",
    text="count",
    title="Top Sender Banks",
    labels={
        "sender_bank": "Bank",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig14,
    use_container_width=True
)

# ============================================================
# 15. RECEIVER AGE GROUP
# ============================================================

st.markdown(
    '<div class="section-title">'
    '15. Transactions by Receiver Age Group'
    '</div>',
    unsafe_allow_html=True
)

receiver_age_df = (
    filtered_df["receiver_age_group"]
    .value_counts()
    .reset_index()
)

receiver_age_df.columns = [
    "receiver_age_group",
    "count"
]

fig15 = px.bar(
    receiver_age_df,
    x="receiver_age_group",
    y="count",
    text="count",
    title="Transactions by Receiver Age Group",
    labels={
        "receiver_age_group": "Receiver Age Group",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig15,
    use_container_width=True
)

# ============================================================
# 16. TOP RECEIVER BANKS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '16. Receiver Bank Analysis'
    '</div>',
    unsafe_allow_html=True
)

receiver_bank_df = (
    filtered_df["receiver_bank"]
    .value_counts()
    .reset_index()
)

receiver_bank_df.columns = [
    "receiver_bank",
    "count"
]

fig16 = px.bar(
    receiver_bank_df.head(10),
    x="receiver_bank",
    y="count",
    text="count",
    title="Top Receiver Banks",
    labels={
        "receiver_bank": "Receiver Bank",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig16,
    use_container_width=True
)

# ============================================================
# 17. TRANSACTION VALUE BY STATE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '17. Transaction Value by State'
    '</div>',
    unsafe_allow_html=True
)

state_value_df = (
    filtered_df
    .groupby("sender_state")["amount_inr"]
    .sum()
    .reset_index()
    .sort_values(
        "amount_inr",
        ascending=False
    )
)

fig17 = px.bar(
    state_value_df.head(10),
    x="sender_state",
    y="amount_inr",
    text="amount_inr",
    title="Top States by Transaction Value",
    labels={
        "sender_state": "State",
        "amount_inr": "Transaction Value (₹)"
    }
)

fig17.update_layout(
    xaxis_tickangle=-45
)

fig17.update_traces(
    texttemplate="₹%{text:,.0f}",
    textposition="outside"
)

st.plotly_chart(
    fig17,
    use_container_width=True
)

# ============================================================
# 18. SUCCESS RATE BY STATE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '18. Success Rate by State'
    '</div>',
    unsafe_allow_html=True
)

state_success_df = (
    filtered_df
    .groupby("sender_state")["transaction_status"]
    .apply(
        lambda x:
        (x.str.lower() == "success").mean() * 100
    )
    .reset_index(
        name="success_rate"
    )
    .sort_values(
        "success_rate",
        ascending=False
    )
)

fig18 = px.bar(
    state_success_df,
    x="sender_state",
    y="success_rate",
    text="success_rate",
    title="Success Rate by Sender State",
    labels={
        "sender_state": "State",
        "success_rate": "Success Rate (%)"
    }
)

fig18.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

st.plotly_chart(
    fig18,
    use_container_width=True
)

# ============================================================
# 19. FRAUD RATE BY STATE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '19. Fraud Rate by State'
    '</div>',
    unsafe_allow_html=True
)

state_fraud_df = (
    filtered_df
    .groupby("sender_state")["fraud_flag"]
    .mean()
    .mul(100)
    .reset_index(
        name="fraud_rate"
    )
    .sort_values(
        "fraud_rate",
        ascending=False
    )
)

fig19 = px.bar(
    state_fraud_df,
    x="sender_state",
    y="fraud_rate",
    text="fraud_rate",
    title="Fraud Rate by Sender State",
    labels={
        "sender_state": "State",
        "fraud_rate": "Fraud Rate (%)"
    }
)

fig19.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig19.update_layout(
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig19,
    use_container_width=True
)

# ============================================================
# 20. WEEKEND VS WEEKDAY
# ============================================================

st.markdown(
    '<div class="section-title">'
    '20. Weekend vs Weekday Transactions'
    '</div>',
    unsafe_allow_html=True
)

weekend_df = (
    filtered_df["is_weekend"]
    .map({
        0: "Weekday",
        1: "Weekend"
    })
    .value_counts()
    .reset_index()
)

weekend_df.columns = [
    "day_type",
    "count"
]

fig20 = px.pie(
    weekend_df,
    names="day_type",
    values="count",
    hole=0.4,
    title="Weekday vs Weekend Transactions"
)

st.plotly_chart(
    fig20,
    use_container_width=True
)

# ============================================================
# 21. AVERAGE TRANSACTIONS PER DAY
# ============================================================

st.markdown(
    '<div class="section-title">'
    '21. Daily Transaction Activity'
    '</div>',
    unsafe_allow_html=True
)

daily_df = (
    filtered_df
    .assign(
        date=filtered_df["timestamp"].dt.date
    )
    .groupby("date")
    .size()
    .reset_index(
        name="transactions"
    )
)

average_daily_transactions = (
    daily_df["transactions"].mean()
)

st.info(
    f"Average transactions per day: "
    f"{average_daily_transactions:,.2f}"
)

fig21 = px.line(
    daily_df,
    x="date",
    y="transactions",
    title="Daily Transaction Volume",
    labels={
        "date": "Date",
        "transactions": "Transactions"
    }
)

st.plotly_chart(
    fig21,
    use_container_width=True
)

# ============================================================
# 22. TOP TRANSACTION HOURS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '22. Transaction Volume by Hour'
    '</div>',
    unsafe_allow_html=True
)

hour_summary = (
    filtered_df["hour_of_day"]
    .value_counts()
    .sort_index()
    .reset_index()
)

hour_summary.columns = [
    "hour",
    "transactions"
]

busiest_hour = (
    hour_summary.loc[
        hour_summary["transactions"].idxmax(),
        "hour"
    ]
)

st.info(
    f"Busiest transaction hour: {int(busiest_hour):02d}:00"
)

# ============================================================
# 23. MOST COMMON TRANSACTION DAY
# ============================================================

day_counts = (
    filtered_df["day_of_week"]
    .value_counts()
)

if not day_counts.empty:
    most_common_day = day_counts.idxmax()

    st.info(
        f"Most common transaction day: "
        f"{most_common_day.title()}"
    )

# ============================================================
# 24. MOST COMMON RECEIVER AGE GROUP
# ============================================================

receiver_age_counts = (
    filtered_df["receiver_age_group"]
    .value_counts()
)

if not receiver_age_counts.empty:

    common_receiver_age = (
        receiver_age_counts.idxmax()
    )

    st.info(
        f"Most common receiver age group: "
        f"{common_receiver_age}"
    )

# ============================================================
# 25. 5G TRANSACTIONS BY STATE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '25. 5G Transactions by State'
    '</div>',
    unsafe_allow_html=True
)

five_g_df = filtered_df[
    filtered_df["network_type"].str.lower() == "5g"
]

if not five_g_df.empty:

    five_g_state_df = (
        five_g_df["sender_state"]
        .value_counts()
        .reset_index()
    )

    five_g_state_df.columns = [
        "sender_state",
        "count"
    ]

    fig25 = px.bar(
        five_g_state_df.head(10),
        x="sender_state",
        y="count",
        text="count",
        title="Top States for 5G Transactions",
        labels={
            "sender_state": "State",
            "count": "5G Transactions"
        }
    )

    fig25.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig25,
        use_container_width=True
    )

else:
    st.info("No 5G transactions available for the selected filters.")

# ============================================================
# 26. PAYMENT METHOD VS DEVICE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '26. Payment Method vs Device Type'
    '</div>',
    unsafe_allow_html=True
)

method_device_df = (
    filtered_df
    .groupby(
        ["transaction_type", "device_type"]
    )
    .size()
    .reset_index(
        name="transactions"
    )
)

fig26 = px.bar(
    method_device_df,
    x="transaction_type",
    y="transactions",
    color="device_type",
    barmode="group",
    title="Payment Method by Device Type",
    labels={
        "transaction_type": "Payment Method",
        "transactions": "Transactions",
        "device_type": "Device"
    }
)

st.plotly_chart(
    fig26,
    use_container_width=True
)

# ============================================================
# 27. PAYMENT METHOD VS NETWORK
# ============================================================

st.markdown(
    '<div class="section-title">'
    '27. Payment Method vs Network Type'
    '</div>',
    unsafe_allow_html=True
)

method_network_df = (
    filtered_df
    .groupby(
        ["transaction_type", "network_type"]
    )
    .size()
    .reset_index(
        name="transactions"
    )
)

fig27 = px.bar(
    method_network_df,
    x="transaction_type",
    y="transactions",
    color="network_type",
    barmode="group",
    title="Payment Method by Network Type",
    labels={
        "transaction_type": "Payment Method",
        "transactions": "Transactions",
        "network_type": "Network"
    }
)

st.plotly_chart(
    fig27,
    use_container_width=True
)

# ============================================================
# 28. TRANSACTION AMOUNT DISTRIBUTION
# ============================================================

st.markdown(
    '<div class="section-title">'
    '28. Transaction Amount Distribution'
    '</div>',
    unsafe_allow_html=True
)

fig28 = px.histogram(
    filtered_df,
    x="amount_inr",
    nbins=50,
    title="Distribution of Transaction Amounts",
    labels={
        "amount_inr": "Amount (₹)",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig28,
    use_container_width=True
)

# ============================================================
# 29. TOP REVENUE-GENERATING STATES
# ============================================================

st.markdown(
    '<div class="section-title">'
    '29. Revenue-Generating States'
    '</div>',
    unsafe_allow_html=True
)

revenue_state_df = (
    filtered_df
    .groupby("sender_state")["amount_inr"]
    .sum()
    .reset_index()
    .sort_values(
        "amount_inr",
        ascending=False
    )
)

if not revenue_state_df.empty:

    highest_revenue_state = (
        revenue_state_df.iloc[0]["sender_state"]
    )

    st.info(
        f"Highest transaction-value state: "
        f"{highest_revenue_state.title()}"
    )

# ============================================================
# 30. LOWEST FRAUD RATE STATE
# ============================================================

if not state_fraud_df.empty:

    lowest_fraud_state = (
        state_fraud_df.iloc[-1]["sender_state"]
    )

    lowest_fraud_rate = (
        state_fraud_df.iloc[-1]["fraud_rate"]
    )

    st.info(
        f"Lowest fraud-rate state: "
        f"{lowest_fraud_state.title()} "
        f"({lowest_fraud_rate:.2f}%)"
    )

# ============================================================
# FILTERED DATA TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📋 Filtered Transaction Data'
    '</div>',
    unsafe_allow_html=True
)

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400
)

# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered Data",
    data=csv_data,
    file_name="filtered_upi_transactions.csv",
    mime="text/csv"
)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; color:#6b7280;">
        <b>Digital Payment Transaction Trends Dashboard</b><br>
        UPI Transaction Analysis – 2024<br>
        Developed using Python, Pandas, Plotly and Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
