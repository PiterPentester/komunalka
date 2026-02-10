import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
import re
import datetime
import email
from email import policy
import time
from bs4 import BeautifulSoup
import pdfplumber

# Google API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Constants & Config ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
KEYWORDS = ["receipt", "invoice", "payment", "переказ", "рахунок", "order", "квитанція"]
DB_FILE = "receipts_database.csv"

st.set_page_config(page_title="Komunalka", page_icon="🧾", layout="wide")

# --- Styling ---
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff8a00, #e52e71);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Helpers ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Date", "Amount", "Merchant", "Category", "Address", "Source", "ID"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def get_gmail_service(creds_path, token_path="token.json"):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                st.error(f"Credentials file not found at {creds_path}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def parse_text_content(text):
    data = {}
    
    # 1. Dates (DD.MM.YYYY or YYYY-MM-DD)
    date_match = re.search(r'(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})', text)
    if date_match:
        try:
            d_str = date_match.group(1).replace('.', '-').replace('/', '-')
            if d_str[2] == '-': # DD-MM-YYYY
                data['Date'] = datetime.datetime.strptime(d_str, "%d-%m-%Y").strftime("%Y-%m-%d")
            else:
                data['Date'] = d_str
        except:
            data['Date'] = datetime.date.today().strftime("%Y-%m-%d")
    else:
        data['Date'] = datetime.date.today().strftime("%Y-%m-%d")

    # 2. Amount (Look for currency symbols or patterns)
    # Ukraine/General regex: '150.00 грн', '120,50 uah', '$50.00'
    amount_match = re.search(r'(?:Total|Сума|Amount|Suma).*?(\d+[.,]\d{2})', text, re.IGNORECASE)
    if not amount_match:
        # Fallback loose search
        amount_match = re.search(r'(\d+[.,]\d{2})\s*(?:грн|UAH|USD|\$|EUR|€)', text, re.IGNORECASE)
    
    if amount_match:
        val = amount_match.group(1).replace(',', '.')
        try:
            data['Amount'] = float(val)
        except:
            data['Amount'] = 0.0
    else:
        data['Amount'] = 0.0

    # 3. Address
    addr_match = re.search(r'(вул\.|str\.|St\.).{5,40}', text, re.IGNORECASE)
    data['Address'] = addr_match.group(0) if addr_match else ""

    return data

def get_category(text, merchant, use_ai=False):
    text_lower = (text + " " + merchant).lower()
    
    # Static Rules
    if any(x in text_lower for x in ['privatbank', 'transfer', 'переказ']): return "Bank Transfer"
    if any(x in text_lower for x in ['silpo', 'atb', 'novus', 'grocery', 'market']): return "Groceries"
    if any(x in text_lower for x in ['vodafone', 'kyivstar', 'lifecell', 'internet', 'wifi']): return "Utilities"
    if any(x in text_lower for x in ['coffee', 'cafe', 'restaurant', 'mcdonalds']): return "Dining"
    if any(x in text_lower for x in ['uber', 'bolt', 'uklon', 'ticket']): return "Transport"

    # AI Hook
    if use_ai:
        try:
            from transformers import pipeline
            classifier = pipeline("zero-shot-classification", model="distilbert-base-uncased-mnli")
            labels = ["Groceries", "Utilities", "Bank Transfer", "Dining", "Transport", "Shopping", "Services"]
            result = classifier(text[:512], labels) # Clip text for speed
            return result['labels'][0]
        except Exception as e:
            st.warning(f"AI Error: {e}")
            return "Other"
            
    return "Other"

def process_message(service, msg_id, use_ai):
    try:
        msg = service.users().messages().get(userId='me', id=msg_id).execute()
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        subject = headers.get('Subject', 'No Subject')
        sender = headers.get('From', 'Unknown')
        
        # Get content
        full_text = f"{subject} {sender} "
        
        # Determine Body
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    full_text += data
                elif part['mimeType'] == 'application/pdf':
                    att_id = part['body'].get('attachmentId')
                    if att_id:
                        att = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=att_id).execute()
                        file_data = base64.urlsafe_b64decode(att['data'])
                        with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                            for page in pdf.pages:
                                full_text += page.extract_text() + " "
        else:
            # Simple body
            if 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                full_text += base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

        # Parse
        parsed = parse_text_content(full_text)
        
        # Refine Data
        merchant = sender.split('<')[0].strip().replace('"', '')
        category = get_category(full_text, merchant, use_ai)
        
        return {
            "Date": parsed['Date'],
            "Amount": parsed['Amount'],
            "Merchant": merchant,
            "Category": category,
            "Address": parsed['Address'],
            "Source": f"Gmail: {subject[:30]}...",
            "ID": msg_id
        }
    except Exception as e:
        print(f"Error parsing {msg_id}: {e}")
        return None

# --- Main Setup ---
st.title("🏠 Komunalka Dashboard")

# User Inputs Sidebar
with st.sidebar:
    st.header("Settings")
    creds_file = st.text_input("Credentials Path", "credentials.json")
    use_ai = st.toggle("Enable AI Classification", value=False)
    
    st.subheader("Data Actions")
    if st.button("Scan Inbox (Last 12mo)"):
        status = st.status("Connecting to Gmail...", expanded=True)
        try:
            service = get_gmail_service(creds_file)
            if service:
                status.write("Searching emails...")
                # Search query
                query = f"({' OR '.join(KEYWORDS)}) newer_than:1y"
                results = service.users().messages().list(userId='me', q=query, maxResults=30).execute()
                messages = results.get('messages', [])
                
                status.write(f"Found {len(messages)} potential receipts. Parsing...")
                
                new_data = []
                progress_bar = status.progress(0)
                
                for idx, m in enumerate(messages):
                    data = process_message(service, m['id'], use_ai)
                    if data and data['Amount'] > 0: # Filter empty/zero
                        new_data.append(data)
                    progress_bar.progress((idx + 1) / len(messages))
                
                if new_data:
                    current_df = load_data()
                    new_df = pd.DataFrame(new_data)
                    # Merge avoiding dupes
                    combined = pd.concat([current_df, new_df]).drop_duplicates(subset=['ID'])
                    save_data(combined)
                    status.update(label="Scan Complete!", state="complete", expanded=False)
                    st.success(f"Added {len(new_df)} new records.")
                    st.rerun()
                else:
                    status.update(label="No valid receipts found.", state="complete")
        except Exception as e:
            status.update(label="Error occurred", state="error")
            st.error(f"Details: {e}")
            
    if st.button("Load Sample Data"):
        sample_data = [{
            "Date": "2026-01-18",
            "Amount": 151.61,
            "Merchant": "PrivatBank",
            "Category": "Bank Transfer",
            "Address": "вул. Шевченка, 25, кв. 48",
            "Source": "Sample Data",
            "ID": "sample_1"
        }, {
             "Date": "2026-01-15",
             "Amount": 450.00,
             "Merchant": "Silpo",
             "Category": "Groceries",
             "Address": "Unknown",
             "Source": "Sample Data",
             "ID": "sample_2"
        }]
        current_df = load_data()
        new_df = pd.DataFrame(sample_data)
        combined = pd.concat([current_df, new_df]).drop_duplicates(subset=['ID'])
        save_data(combined)
        st.rerun()

# --- Dashboard View ---
df = load_data()

# Ensure types
df['Date'] = pd.to_datetime(df['Date'])
df['Amount'] = pd.to_numeric(df['Amount'])

# Filters
col1, col2 = st.columns([1,3])
with col1:
    st.subheader("Filters")
    # Date Filter
    min_date = df['Date'].min().date() if not df.empty else datetime.date.today()
    max_date = df['Date'].max().date() if not df.empty else datetime.date.today()
    date_range = st.date_input("Date Range", [min_date, max_date])
    
    # Cat Filter
    all_cats = ["All"] + list(df['Category'].unique()) if not df.empty else ["All"]
    cat_filter = st.selectbox("Category", all_cats)

# Filter Logic
if len(date_range) == 2:
    start_d, end_d = date_range
    mask = (df['Date'].dt.date >= start_d) & (df['Date'].dt.date <= end_d)
    if cat_filter != "All":
        mask = mask & (df['Category'] == cat_filter)
    filtered_df = df.loc[mask]
else:
    filtered_df = df

# Metrics
st.markdown("### 📊 Overview")
m1, m2, m3 = st.columns(3)
if not filtered_df.empty:
    with m1:
        st.markdown(f'<div class="metric-card"><h3>Total Spent</h3><h2>{filtered_df["Amount"].sum():.2f} UAH</h2></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><h3>Avg Payment</h3><h2>{filtered_df["Amount"].mean():.2f} UAH</h2></div>', unsafe_allow_html=True)
    with m3:
        top_merch = filtered_df.groupby('Merchant')['Amount'].sum().idxmax()
        st.markdown(f'<div class="metric-card"><h3>Top Merchant</h3><h2>{top_merch}</h2></div>', unsafe_allow_html=True)
else:
    st.info("No data available. Scan your inbox or check filters.")

# Visualization
st.divider()
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📅 Spending Calendar")
    if not filtered_df.empty:
        # Prepare heatmap data
        daily_sum = filtered_df.groupby('Date')['Amount'].sum().reset_index()
        fig_cal = go.Figure(data=go.Scatter(
            x=daily_sum['Date'],
            y=daily_sum['Amount'],
            mode='markers',
            marker=dict(
                size=[min(max(x/10, 10), 50) for x in daily_sum['Amount']],
                color=daily_sum['Amount'],
                colorscale='Viridis',
                showscale=True
            ),
            text=daily_sum['Amount'].apply(lambda x: f"{x} UAH"),
            hovertemplate="<b>Date</b>: %{x}<br><b>Total</b>: %{y} UAH<extra></extra>"
        ))
        fig_cal.update_layout(title="Daily Spending Intensity", height=400, template="plotly_dark")
        st.plotly_chart(fig_cal, use_container_width=True)

with c2:
    st.subheader("🛍️ Categories")
    if not filtered_df.empty:
        cat_fig = px.pie(filtered_df, values='Amount', names='Category', hole=0.4, template="plotly_dark")
        cat_fig.update_layout(height=400)
        st.plotly_chart(cat_fig, use_container_width=True)

# Data Table
st.subheader("📝 Recent Transactions")
st.dataframe(
    filtered_df.sort_values("Date", ascending=False),
    use_container_width=True,
    column_config={
        "Amount": st.column_config.NumberColumn("Amount (UAH)", format="%.2f"),
        "Date": st.column_config.DateColumn("Date", format="DD.MM.YYYY"),
    }
)

# Downloads
st.download_button(
    label="Download CSV Report",
    data=filtered_df.to_csv().encode('utf-8'),
    file_name='komunalka_report.csv',
    mime='text/csv',
)
