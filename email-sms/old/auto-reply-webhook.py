from flask import Flask, request
import base64, email, json, os, pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

app = Flask(__name__)
os.environ["OPENAI_API_KEY"] = "your-openai-key"

def load_gmail_service():
    with open("token.pkl", "rb") as token:
        creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)

def get_latest_message(service):
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])
    if not messages:
        return None, None, None
    msg_id = messages[0]["id"]
    msg = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
    raw_msg = base64.urlsafe_b64decode(msg["raw"].encode("ASCII"))
    mime_msg = email.message_from_bytes(raw_msg)
    subject = mime_msg["Subject"]
    sender = mime_msg["From"]
    body = ""
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = mime_msg.get_payload(decode=True).decode()
    return subject, sender, body

def generate_reply(subject, body):
    chat = ChatOpenAI(temperature=0.7)
    msg = HumanMessage(
        content=f"You're a polite assistant. Reply to this email professionally:\nSubject: {subject}\nBody:\n{body}"
    )
    response = chat([msg])
    return response.content

def send_reply(service, to_email, original_subject, reply_text):
    message = email.message.EmailMessage()
    message.set_content(reply_text)
    message["To"] = to_email
    message["Subject"] = "Re: " + original_subject
    message["From"] = "me"
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_body = {"raw": encoded_message}
    service.users().messages().send(userId="me", body=send_body).execute()

@app.route("/gmail-webhook", methods=["POST"])
def gmail_webhook():
    print("🔔 Gmail notification received.")
    service = load_gmail_service()
    subject, sender, body = get_latest_message(service)

    if subject and sender and body:
        reply = generate_reply(subject, body)
        send_reply(service, sender, subject, reply)
        print("✅ AI reply sent.")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
