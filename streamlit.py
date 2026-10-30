import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- BACKGROUND HTTP HEALTH-CHECK SERVER (KEEP-ALIVE) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Fraud Detection Dashboard is Alive")
    
    def log_message(self, format, *args):
        # Suppress standard HTTP access logs to keep runtime clean
        return

def run_health_server():
    try:
        server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
        server.serve_forever()
    except Exception:
        pass

# Start the background HTTP listener in a daemon thread (cached globally)
@st.cache_resource
def init_keep_alive_server():
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    return "Running"

init_keep_alive_server()

# Page Configuration
st.set_page_config(
    page_title="Fraud Detection Risk Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("Fraud Detection & Risk Intelligence Dashboard")
st.markdown("Operational risk monitoring, model performance tracking, and suspicious transaction triage.")

# Load Data Caching
@st.cache_data
def load_dashboard_data():
    np.random.seed(42)
    data = {
        'TransactionID': range(1, 1001),
        'TransactionDate': pd.date_range(start='2026-10-01', periods=1000, freq='min').strftime('%H:%M.%s'),
        'Amount': np.random.exponential(scale=500, size=1000),
        'MerchantID': np.random.randint(100, 999, size=1000),
        'TransactionType': np.random.choice(['purchase', 'refund', 'transfer'], size=1000, p=[0.7, 0.15, 0.15]),
        'Location': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'San Antonio', 'Dallas', 'Philadelphia'], size=1000),
        'IsFraud': np.random.choice([0, 1], size=1000, p=[0.95, 0.05])
    }
    df_dash = pd.DataFrame(data)
    df_dash['RiskScore'] = np.where(df_dash['IsFraud'] == 1, np.random.uniform(0.75, 0.99, size=1000), np.random.uniform(0.01, 0.40, size=1000))
    return df_dash

df_dash = load_dashboard_data()

# Sidebar Filters
st.sidebar.header("Filter Controls")
selected_location = st.sidebar.selectbox("Select Location", ["All"] + list(df_dash['Location'].unique()))
if selected_location != "All":
    df_dash = df_dash[df_dash['Location'] == selected_location]

# Executive Metrics
total_tx = len(df_dash)
fraud_tx = int(df_dash['IsFraud'].sum())
fraud_rate = (fraud_tx / total_tx) * 100 if total_tx > 0 else 0
total_val = df_dash['Amount'].sum()
fraud_val = df_dash[df_dash['IsFraud'] == 1]['Amount'].sum()

st.subheader("Executive Overview")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Transactions", f"{total_tx:,}")
col2.metric("Fraud Transactions", f"{fraud_tx:,}")
col3.metric("Fraud Rate", f"{fraud_rate:.2f}%")
col4.metric("Total Value", f"${total_val:,.2f}")
col5.metric("Fraud Value", f"${fraud_val:,.2f}")

st.markdown("---")

# Visualizations
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Fraud Rate by Transaction Type")
    type_fraud = df_dash.groupby('TransactionType')['IsFraud'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x='TransactionType', y='IsFraud', data=type_fraud, ax=ax, palette='Blues_d')
    ax.set_ylabel("Fraud Rate")
    st.pyplot(fig)

with col_right:
    st.subheader("Top Locations by Fraud Volume")
    loc_fraud = df_dash.groupby('Location')['IsFraud'].sum().reset_index().sort_values(by='IsFraud', ascending=False).head(5)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x='Location', y='IsFraud', data=loc_fraud, ax=ax, palette='Reds_d')
    ax.set_ylabel("Fraud Count")
    st.pyplot(fig)

st.markdown("---")
st.subheader("Suspicious Transactions Review Queue")

flagged_df = df_dash[df_dash['RiskScore'] > 0.75][['TransactionDate', 'Amount', 'MerchantID', 'TransactionType', 'Location', 'RiskScore']]
flagged_df['Status'] = 'Pending Review'
st.dataframe(flagged_df.head(20), use_container_width=True)
