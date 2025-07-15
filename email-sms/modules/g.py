import os
import pickle
import base64
import datetime
import sqlite3
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# === Configuration ===
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, 'greetings.html')
DB_PATH = os.path.join(base_dir, 'emails.db')

# === Gmail Authentication ===
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

# === Email Utilities ===
def get_email_header(msg_detail, name):
    headers = msg_detail.get('payload', {}).get('headers', [])
    for header in headers:
        if header['name'] == name:
            return header['value']
    return "(N/A)"

def get_email_content(msg_detail):
    payload = msg_detail.get('payload', {})
    parts = payload.get('parts', [])
    if parts:
        for part in parts:
            if part['mimeType'] in ['text/plain', 'text/html']:
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
    body_data = payload.get('body', {}).get('data')
    if body_data:
        return base64.urlsafe_b64decode(body_data).decode('utf-8')
    return "(No content found)"

def convert_timestamp_to_datetime(timestamp_ms):
    try:
        return datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "(Invalid Date)"

def extract_body(mime_msg):
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        return mime_msg.get_payload(decode=True).decode(errors="ignore")
    return "(No Body Found)"

# === Gmail Actions ===
def fetch_unread_emails(max_results=10):
    service = gmail_authenticate()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=max_results).execute()
    messages = results.get('messages', [])
    email_list = []
    for msg in messages:
        msg_id = msg['id']
        msg_detail = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
        email_list.append({
            'id': msg_id,
            'sender': get_email_header(msg_detail, 'From'),
            'subject': get_email_header(msg_detail, 'Subject'),
            'snippet': msg_detail.get('snippet', '(No snippet)')
        })
    return email_list

def get_email_detail(message_id):
    service = gmail_authenticate()
    return service.users().messages().get(userId='me', id=message_id, format='full').execute()

def send_email(to, subject, body_file_path):
    service = gmail_authenticate()
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['subject'] = subject

    try:
        with open(body_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found -> {body_file_path}")
        return

    ext = os.path.splitext(body_file_path)[1].lower()
    msg_text = MIMEText(content, 'html' if ext == '.html' else 'plain')
    message.attach(msg_text)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent_message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
    print(f"Message Id: {sent_message['id']}")
    return sent_message

def mark_as_read(message_id):
    service = gmail_authenticate()
    service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()

# === Database Handling ===
def save_emails_to_db(email_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            subject TEXT,
            sender TEXT,
            snippet TEXT,
            body TEXT,
            replied INTEGER DEFAULT 0,
            reply TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    for item in email_list:
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

# === AI Reply Generation ===
def generate_reply(subject, body):
    chat = ChatOpenAI(temperature=0.7)
    message = HumanMessage(content=f"You are an AI assistant. Read the email below and generate a professional reply.\n\nSubject: {subject}\n\nBody:\n{body}")
    response = chat([message])
    return response.content

# === Email Processing Logic ===
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

def process_emails():
    unread_emails = fetch_unread_emails()
    for email in unread_emails:
        print(f"Processing email ID: {email['id']}")
        mark_as_read(email['id'])

# === Main Runner ===
if __name__ == '__main__':
    process_emails()
