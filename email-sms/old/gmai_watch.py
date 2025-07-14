from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate():
    creds = None
    if os.path.exists("token.pkl"):
        with open("token.pkl", "rb") as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.pkl", "wb") as token:
            pickle.dump(creds, token)
    return creds

def setup_watch():
    creds = authenticate()
    service = build("gmail", "v1", credentials=creds)
    response = service.users().watch(userId="me", body={
        "labelIds": ["INBOX"],
        "topicName": "projects/YOUR_PROJECT_ID/topics/gmail-push-topic"
    }).execute()
    print("Watch response:", response)

if __name__ == "__main__":
    setup_watch()
