# greeting_workflow_demo.py
import streamlit as st
import sqlite3
import datetime
import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64

# --- Configuration ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
SERVICE_ACCOUNT_FILE = 'gmail_service_account.json'  # Replace with your service account file
GMAIL_USER = st.secrets["GMAIL_USER"]

def get_gmail_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_creds = creds.with_subject(GMAIL_USER)
    service = build('gmail', 'v1', credentials=delegated_creds)
    return service

def send_email(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body)
    message['to'] = to
    message['from'] = GMAIL_USER
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    try:
        service.users().messages().send(userId='me', body=body).execute()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            birthday TEXT,
            area TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS greeting_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- Utility Functions ---
def get_today_birthdays():
    today = datetime.datetime.today().strftime("%m-%d")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE strftime('%m-%d', birthday) = ?", (today,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_users_by_area(area):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE area = ?", (area,))
    results = cursor.fetchall()
    conn.close()
    return results

def save_log(user_id, msg_type, message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO greeting_logs (user_id, type, message) VALUES (?, ?, ?)", (user_id, msg_type, message))
    conn.commit()
    conn.close()

def get_greeting_logs():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT greeting_logs.id, users.name, users.email, users.phone, greeting_logs.type, greeting_logs.message, greeting_logs.sent_at
        FROM greeting_logs
        JOIN users ON greeting_logs.user_id = users.id
        ORDER BY greeting_logs.sent_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- LangChain Email/SMS Generator ---
llm = ChatOpenAI(model_name="gpt-3.5-turbo")
prompt = PromptTemplate(
    input_variables=["name", "occasion"],
    template="""
    Create a professional and friendly {occasion} greeting for {name} suitable for sending via email and SMS.
    Keep the SMS under 160 characters.
    """
)
chain = LLMChain(llm=llm, prompt=prompt)

# --- Streamlit App ---
st.title("Dynamic Greeting Workflow Demo")
init_db()

menu = st.sidebar.selectbox("Menu", ["Send Greetings", "View Logs"])

if menu == "Send Greetings":
    option = st.radio("Select Greeting Type:", ("Birthday", "Festival by Area"))

    if option == "Birthday":
        users = get_today_birthdays()
        if users:
            for user in users:
                user_id, name, email, phone, birthday, area = user
                result = chain.run({"name": name, "occasion": "birthday"})
                st.write(f"**To:** {name} | **Email:** {email} | **Phone:** {phone}")
                st.write(result)
                if send_email(email, "Happy Birthday from Our Team!", result):
                    st.success("Email sent via Gmail API")
                st.warning("SMS sending skipped (mock)")
                save_log(user_id, "birthday", result)
        else:
            st.info("No birthdays today.")

    elif option == "Festival by Area":
        area = st.text_input("Enter Area (e.g., Maharashtra)")
        festival = st.text_input("Enter Today's Festival (e.g., Diwali)")
        if st.button("Send Greetings"):
            users = get_users_by_area(area)
            if users:
                for user in users:
                    user_id, name, email, phone, birthday, area = user
                    result = chain.run({"name": name, "occasion": festival})
                    st.write(f"**To:** {name} | **Email:** {email} | **Phone:** {phone}")
                    st.write(result)
                    if send_email(email, f"Happy {festival} from Our Team!", result):
                        st.success("Email sent via Gmail API")
                    st.warning("SMS sending skipped (mock)")
                    save_log(user_id, "festival", result)
            else:
                st.info("No users found in this area.")

elif menu == "View Logs":
    st.subheader("Greeting History")
    logs = get_greeting_logs()
    if logs:
        for log in logs:
            log_id, name, email, phone, log_type, message, sent_at = log
            st.markdown(f"**{log_type.title()}** | {name} ({email}, {phone})")
            st.text(f"{message}")
            st.caption(f"Sent at: {sent_at}")
            st.markdown("---")
    else:
        st.info("No greetings sent yet.")
