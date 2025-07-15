import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import modules.db as db
print("Current working directory:", os.getcwd())
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, 'greetings.html')
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
print("File path:", file_path)
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

def get_email_header(msg_detail, name):
    if not msg_detail or 'payload' not in msg_detail or 'headers' not in msg_detail['payload']:
        return "(N/A)"

    headers = msg_detail['payload']['headers']
    for header in headers:
        if header['name'] == name:
            return header['value']
    return "(N/A)"

def get_email_content(msg_detail):
    if not msg_detail or 'payload' not in msg_detail:
        return "(No content found or invalid message detail)"

    payload = msg_detail['payload']
    parts = payload.get('parts')

    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
    elif payload.get('body') and payload['body'].get('data'):
        data = payload['body'].get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    return "(No content found)"

def convert_timestamp_to_datetime(timestamp_ms):
    if timestamp_ms is None:
        return "(N/A)"
    try:
        # Convert milliseconds to seconds
        dt_object = datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000)
        return dt_object.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "(Invalid Date)"

def fetch_unread_emails(max_results=20):
    service = gmail_authenticate()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    email_list = []
    for msg in messages:
        msg_id = msg['id']
        msg_detail = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
        
        sender = get_email_header(msg_detail, 'From')
        subject = get_email_header(msg_detail, 'Subject')
        snippet = msg_detail.get('snippet', '(No snippet)')

        email_list.append({
            'id': msg_id,
            'sender': sender,
            'subject': subject,
            'snippet': snippet,
            'received_at': convert_timestamp_to_datetime(msg_detail.get('internalDate')),
            'body': get_email_content(msg_detail),
            'replied': False,  # Default to False, can be updated later
            'reply': ''  # Default empty reply
        })
        db.save_emails_to_db(email_list)
    return email_list

def get_email_detail(message_id):
    service = gmail_authenticate()
    # Requesting 'full' format to get internalDate
    msg_detail = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    return msg_detail

def send_email(to, subject, body):
    service = gmail_authenticate()
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['subject'] = subject

        # Determine if the file is HTML or plain text
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found -> greetings.html")
        return

    ext = os.path.splitext(file_path)[1].lower()

    # Assuming plain text for now. Can extend to HTML later.
    msg_text = MIMEText(content, 'html' if ext == '.html' else 'plain')
    message.attach(msg_text)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    try:
        sent_message = service.users().messages().send(
            userId='me', 
            body={'raw': raw_message}
        ).execute()
        print(f"Message Id: {sent_message['id']}")
        return sent_message
    except Exception as e:
        print(f"An error occurred: {e}")
        raise # Re-raise the exception to be caught by Streamlit UI

def mark_as_read(message_id):
    service = gmail_authenticate()
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()

def process_emails():
    unread_emails = fetch_unread_emails()
    for email in unread_emails:
        email_id = email['id']
        # msg_detail = get_email_detail(email_id) # No longer needed here if fetch_unread_emails returns details
        print(f"Processing email ID: {email_id}")
        # Add your processing logic here
        mark_as_read(email_id)

if __name__ == '__main__':
    process_emails()
