import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os.path
import pickle
import base64
import email
import sqlite3
import time
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import pandas as pd

# Scopes to read Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

st.set_page_config(page_title="Gmail AI Responder", layout="wide")
st.title("📩 Gmail AI Responder with Streamlit & LangChain")

DB_PATH = "emails.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            subject TEXT,
            sender TEXT,
            snippet TEXT,
            body TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replied INTEGER DEFAULT 0,
            reply TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_emails_to_db(email_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for item in email_list:
        # Avoid duplicates
        cursor.execute("SELECT id FROM emails WHERE id=?", (item["id"],))
        if cursor.fetchone():
            continue
        cursor.execute(
            "INSERT INTO emails (id, subject, sender, snippet, body) VALUES (?, ?, ?, ?, ?)",
            (item["id"], item["subject"], item["from"], item["snippet"], item["body"])
        )
    conn.commit()
    conn.close()

def get_unreplied_emails_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, sender, snippet, body, replied, reply FROM emails WHERE replied=0 ORDER BY received_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_reply_in_db(email_id, reply):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE emails SET replied=1, reply=? WHERE id=?", (reply, email_id))
    conn.commit()
    conn.close()

def gmail_authenticate():
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def fetch_and_store_emails():
    service = gmail_authenticate()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=10).execute()
    messages = results.get('messages', [])
    email_list = []
    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
        raw_msg = base64.urlsafe_b64decode(msg_detail['raw'].encode('ASCII'))
        mime_msg = email.message_from_bytes(raw_msg)
        subject = mime_msg.get("Subject", "(No Subject)")
        sender = mime_msg.get("From", "(Unknown Sender)")
        snippet = msg_detail.get("snippet", "")
        body = extract_body(mime_msg)
        email_list.append({
            "id": msg['id'],
            "subject": subject,
            "from": sender,
            "snippet": snippet,
            "body": body
        })
    save_emails_to_db(email_list)

def extract_body(mime_msg):
    body = ""
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        body = mime_msg.get_payload(decode=True).decode(errors="ignore")
    return body

def generate_reply(subject, body):
    chat = ChatOpenAI(temperature=0.7)
    message = HumanMessage(
        content=f"You are an AI assistant. Read the email below and generate a professional reply.\n\nSubject: {subject}\n\nBody:\n{body}"
    )
    response = chat([message])
    return response.content

# --- Streamlit UI ---

init_db()

# Auto-refresh every 1 minute to fetch new emails
if "last_fetch" not in st.session_state or time.time() - st.session_state["last_fetch"] > 60:
    fetch_and_store_emails()
    st.session_state["last_fetch"] = time.time()

st.markdown("### 📬 Inbox (Unread, Last 10)")
emails = get_unreplied_emails_from_db()

if emails:
    col1, col2 = st.columns([2, 5])
    with col1:
        email_options = [f"{i+1}. {subject} | {sender}" for i, (_, subject, sender, _, _, _, _) in enumerate(emails)]
        selected_idx = st.radio("Select an email", email_options, index=0, key="email_select")
        idx = email_options.index(selected_idx)
        selected_email = emails[idx]
        email_id, subject, sender, snippet, body, replied, reply = selected_email

    with col2:
        st.markdown(f"**Subject:** {subject}")
        st.markdown(f"**From:** {sender}")
        st.text_area("Email Body", body, height=200)

        if not replied:
            if st.button("🤖 Generate AI Reply", key=f"reply_{email_id}"):
                with st.spinner("Generating AI reply..."):
                    ai_reply = generate_reply(subject, body)
                    update_reply_in_db(email_id, ai_reply)
                    st.success("Reply generated and saved!")
                    st.experimental_rerun()
        else:
            st.subheader("🤖 Suggested Reply")
            st.text_area("Reply", reply, height=200)
            st.info("Reply already generated and saved for this email.")
else:
    st.info("No unread emails found in the database.")

# --- Option to view all emails in the DB ---
st.markdown("---")
if st.checkbox("Show all emails in database"):
    conn = sqlite3.connect(DB_PATH)
    df = None
    try:
        df = pd.read_sql_query("SELECT * FROM emails ORDER BY received_at DESC", conn)
    except Exception as e:
        st.error(f"Error reading database: {e}")
    finally:
        conn.close()
    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.info("No emails found in the database.")

openai_api_key = st.secrets["OPENAI_API_KEY"]
gmail_user = st.secrets["GMAIL_USER"]
gmail_app_password = st.secrets["GMAIL_APP_PASSWORD"]
