import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Digital Payment Transaction Trends Dashboard",
    page_icon="💳",
    layout="wide"
)

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
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

    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .section-title {
        font-size: 23px;
        font-weight: 600;
        color: #111827;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():

    file_path = "upi_transactions_2024_cleaned.csv"

    df = pd.read_csv(file_path, on_bad_lines="skip")

    # Convert columns
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

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

    # Clean string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.lower()

    # Remove invalid critical rows
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
        "CSV file not found. Please keep "
        "'upi_transactions_2024_cleaned.csv' "
        "in the same folder as app.py."
    )
    st.stop()

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("🔎 Dashboard Filters")

# Transaction type
transaction_types = sorted(
    df["transaction_type"].dropna().unique()
)

selected_transaction_types = st.sidebar.multiselect(
    "Transaction Type",
    transaction_types,
    default=transaction_types
)

# States
states = sorted(
    df["sender_state"].dropna().unique()
)

selected_states = st.sidebar.multiselect(
    "Sender State",
    states,
    default=states
)

# Status
statuses = sorted(
    df["transaction_status"].dropna().unique()
)

selected_statuses = st.sidebar.multiselect(
    "Transaction Status",
    statuses,
    default=statuses
)

# Device
devices = sorted(
    df["device_type"].dropna().unique()
)

selected_devices = st.sidebar.multiselect(
    "Device Type",
    devices,
    default=devices
)

# Date range
min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

selected_dates = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------
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

if len(selected_dates) == 2:
    start_date, end_date = selected_dates

    filtered_df = filtered_df[
        (filtered_df["timestamp"].dt.date >= start_date)
        &
        (filtered_df["timestamp"].dt.date <= end_date)
    ]

# ---------------------------------------------------------
# CHECK EMPTY DATA
# ---------------------------------------------------------
if filtered_df.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

# ---------------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------------
total_transactions = len(filtered_df)

total_amount = filtered_df["amount_inr"].sum()

successful_transactions = (
    filtered_df["transaction_status"]
    .str.lower()
    .eq("success")
    .sum()
)

success_rate = (
    successful_transactions /
    total_transactions *
    100
)

failed_transactions = (
    total_transactions -
    successful_transactions
)

failure_rate = (
    failed_transactions /
    total_transactions *
    100
)

fraud_transactions = (
    filtered_df["fraud_flag"]
    .fillna(0)
    .astype(int)
    .sum()
)

average_transaction = (
    filtered_df["amount_inr"].mean()
)

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# SUCCESS RATE BY PAYMENT METHOD
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">1. Success Rate by Payment Method</div>',
    unsafe_allow_html=True
)

success_rate_df = (
    filtered_df
    .groupby("transaction_type")["transaction_status"]
    .apply(
        lambda x:
        np.mean(
            x.str.lower() == "success"
        ) * 100
    )
    .reset_index(
        name="success_rate_%"
    )
    .sort_values(
        "success_rate_%",
        ascending=False
    )
)

fig1 = px.bar(
    success_rate_df,
    x="transaction_type",
    y="success_rate_%",
    text_auto=".2f",
    title="Success Rate by Payment Method",
    labels={
        "transaction_type": "Payment Method",
        "success_rate_%": "Success Rate (%)"
    }
)

fig1.update_layout(
    yaxis_range=[
        max(0, success_rate_df["success_rate_%"].min() - 2),
        100
    ]
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# ---------------------------------------------------------
# FAILURE RATE BY PAYMENT METHOD
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">2. Failure Rate by Transaction Method</div>',
    unsafe_allow_html=True
)

failure_rate_df = (
    filtered_df
    .groupby("transaction_type")["transaction_status"]
    .apply(
        lambda x:
        np.mean(
            x.str.lower() != "success"
        ) * 100
    )
    .reset_index(
        name="failure_rate_%"
    )
    .sort_values(
        "failure_rate_%",
        ascending=False
    )
)

fig2 = px.bar(
    failure_rate_df,
    x="transaction_type",
    y="failure_rate_%",
    text_auto=".2f",
    title="Failure Rate by Transaction Method (%)",
    labels={
        "transaction_type": "Transaction Method",
        "failure_rate_%": "Failure Rate (%)"
    }
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# ---------------------------------------------------------
# TRANSACTIONS BY AGE GROUP
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">3. Transactions by Sender Age Group</div>',
    unsafe_allow_html=True
)

age_group_counts = (
    filtered_df["sender_age_group"]
    .value_counts()
    .reset_index()
)

age_group_counts.columns = [
    "age_group",
    "txn_count"
]

fig3 = px.bar(
    age_group_counts,
    x="age_group",
    y="txn_count",
    text_auto=True,
    title="Transaction Count by Sender Age Group",
    labels={
        "age_group": "Age Group",
        "txn_count": "Number of Transactions"
    }
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# ---------------------------------------------------------
# TRANSACTION TYPE DISTRIBUTION
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">4. Transaction Type Distribution</div>',
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

# ---------------------------------------------------------
# TRANSACTIONS BY MERCHANT CATEGORY
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">5. Transactions by Merchant Category</div>',
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
    text_auto=True,
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

# ---------------------------------------------------------
# TRANSACTIONS BY STATE
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">6. Transactions by Sender State</div>',
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
    text_auto=True,
    title="Top Sender States by Transaction Volume",
    labels={
        "sender_state": "State",
        "count": "Transactions"
    }
)

st.plotly_chart(
    fig6,
    use_container_width=True
)

# ---------------------------------------------------------
# TRANSACTIONS BY DEVICE TYPE
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">7. Device Type Analysis</div>',
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

# ---------------------------------------------------------
# NETWORK TYPE
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">8. Network Type Analysis</div>',
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
    text_auto=True,
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

# ---------------------------------------------------------
# HOURLY TRANSACTION TREND
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">9. Transaction Activity by Hour</div>',
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
        "hour_of_day": "Hour",
        "transaction_count": "Transactions"
    }
)

st.plotly_chart(
    fig9,
    use_container_width=True
)

# ---------------------------------------------------------
# DAY OF WEEK ANALYSIS
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">10. Transactions by Day of Week</div>',
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
    text_auto=True,
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

# ---------------------------------------------------------
# MONTHLY TRANSACTION TREND
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">11. Monthly Transaction Trend</div>',
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
    monthly_df["month"]
    .astype(str)
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

# ---------------------------------------------------------
# TRANSACTION VALUE TREND
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">12. Monthly Transaction Value</div>',
    unsafe_allow_html=True
)

fig12 = px.bar(
    monthly_df,
    x="month",
    y="total_value",
    text_auto=".2s",
    title="Monthly Transaction Value",
    labels={
        "month": "Month",
        "total_value": "Transaction Value (₹)"
    }
)

st.plotly_chart(
    fig12,
    use_container_width=True
)

# ---------------------------------------------------------
# FRAUD ANALYSIS
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">13. Fraud Analysis</div>',
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

# ---------------------------------------------------------
# TOP BANKS
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">14. Sender Bank Analysis</div>',
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
    text_auto=True,
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

# ---------------------------------------------------------
# DATA TABLE
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">📋 Transaction Data</div>',
    unsafe_allow_html=True
)

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400
)

# ---------------------------------------------------------
# DOWNLOAD FILTERED DATA
# ---------------------------------------------------------
csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered Data",
    data=csv_data,
    file_name="filtered_upi_transactions.csv",
    mime="text/csv"
)

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("---")

st.markdown(
    """
    <div style='text-align:center; color:#6b7280;'>
        <b>Digital Payment Transaction Trends Dashboard</b><br>
        Data Analysis using Python, Pandas, Plotly and Streamlit<br>
        Dataset: UPI Transactions 2024
    </div>
    """,
    unsafe_allow_html=True
)