import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

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

def fetch_unread_emails(max_results=10):
    service = gmail_authenticate()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=max_results).execute()
    messages = results.get('messages', [])
    return messages

def get_email_detail(message_id):
    service = gmail_authenticate()
    msg_detail = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
    return msg_detail

def send_email(to, subject, body):
    # Implement sending email using Gmail API or SMTP as needed
    pass

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
        msg_detail = get_email_detail(email_id)
        print(f"Processing email ID: {email_id}")
        # Add your processing logic here
        mark_as_read(email_id)

if __name__ == '__main__':
    process_emails()