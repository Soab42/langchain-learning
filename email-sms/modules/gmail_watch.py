import streamlit as st
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

def setup_watch(topic_name):
    creds = authenticate()
    service = build("gmail", "v1", credentials=creds)
    body = {
        "labelIds": ["INBOX"],
        "topicName": topic_name
    }
    response = service.users().watch(userId="me", body=body).execute()
    return response

def streamlit_watch_ui():
    st.header("Gmail Push Notification Watch Setup")
    st.write("Set up Gmail push notifications to a Google Cloud Pub/Sub topic.")
    topic = st.text_input("Pub/Sub Topic Name", "projects/syfuddhin2k23/topics/gmail-push-topic")
    if st.button("Set up Gmail Watch"):
        try:
            resp = setup_watch(topic)
            st.success(f"Watch set! Response: {resp}")
        except Exception as e:
            st.error(f"Failed to set up watch: {e}")