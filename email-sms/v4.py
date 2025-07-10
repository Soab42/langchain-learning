# greeting_workflow_demo.py
import streamlit as st
import sqlite3
import datetime
import openai
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.chains import LLMChain
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import os

# --- Configuration ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GMAIL_USER = st.secrets["GMAIL_USER"]

# --- Gmail Functions ---
def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        from google.auth.transport.requests import Request
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_email(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body)
    message['to'] = to
    message['from'] = f'"Sam Haque, Commartial Landers Ltd" <{GMAIL_USER}>'  # Custom sender name 
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    try:
        service.users().messages().send(userId='me', body=body).execute()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False
    
def send_email_smtp(to, subject, body):
    from_email = GMAIL_USER
    # Use an App Password for Gmail SMTP, not your regular password
    from_name = "Sam Haque, Commartial Landers Ltd"
    password = st.secrets["GMAIL_APP_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email via SMTP: {e}")
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS festivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT,
            name TEXT
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

def add_user(name, email, phone, birthday, area):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, email, phone, birthday, area) VALUES (?, ?, ?, ?, ?)",
                   (name, email, phone, birthday, area))
    conn.commit()
    conn.close()

def import_users_from_csv(file):
    df = pd.read_csv(file)
    conn = sqlite3.connect("users.db")
    df.to_sql('users', conn, if_exists='append', index=False)
    conn.close()

def get_festivals_by_area(area):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM festivals WHERE area = ?", (area,))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def add_festival(area, name):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO festivals (area, name) VALUES (?, ?)", (area, name))
    conn.commit()
    conn.close()

def import_festivals_from_csv(file):
    df = pd.read_csv(file)
    conn = sqlite3.connect("users.db")
    df.to_sql('festivals', conn, if_exists='append', index=False)
    conn.close()

# --- Pydantic Model for Greeting Output ---
class GreetingOutput(BaseModel):
    subject: str = Field(description="Subject line for the email")
    email: str = Field(description="Full email greeting message")
    sms: str = Field(description="Short SMS greeting message under 160 characters")

greeting_parser = PydanticOutputParser(pydantic_object=GreetingOutput)

# --- LangChain Email/SMS Generator ---
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.8,
)
prompt = PromptTemplate(
    input_variables=["name", "occasion"],
    template="""
    Create a professional and friendly {occasion} greeting for {name} suitable for sending via email and SMS.
    - Generate a subject line for the email.
    - Write a full email greeting message.
    - Write a short SMS greeting message (under 160 characters).
    - The sender is "sam haque, commartial landers ltd! 123 Main Street New York, NY 10001 USA".
    {format_instructions}
    """,
    partial_variables={'format_instructions':greeting_parser.get_format_instructions()}
)
chain = prompt | llm | greeting_parser

# --- Streamlit App ---
st.title("Dynamic Greeting Workflow Demo")
init_db()

menu = st.sidebar.selectbox("Menu", ["Send Greetings", "View Logs", "Manage Users", "Manage Festivals"])

if menu == "Send Greetings":
    option = st.radio("Select Greeting Type:", ("Birthday", "Festival by Area"))

    if option == "Birthday":
        users = get_today_birthdays()
        if users:
            for user in users:
                user_id, name, email, phone, birthday, area = user
                result = chain.invoke({"name": name, "occasion": "birthday"})
                st.write(f"**To:** {name} | **Email:** {email} | **Phone:** {phone}")
                st.write(result)
                if send_email_smtp(email, result.subject, result.email):
                    st.success("Email sent via SMTP")
                    st.warning("SMS sending skipped (mock)")
                save_log(user_id, "birthday", result.email)
        else:
            st.info("No birthdays today.")

    elif option == "Festival by Area":
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT area FROM users WHERE area IS NOT NULL AND area != ''")
        areas = [row[0] for row in cursor.fetchall()]
        conn.close()

        col1, col2 = st.columns([2, 3])

        with col1:
            area = st.selectbox("Select Area", areas, key="area_select") if areas else st.text_input("Enter Area", key="area_input")

            festivals = get_festivals_by_area(area) if area else []
            if festivals:
                festival = st.selectbox("Select Festival", festivals, key="festival_select")
            else:
                festival = st.text_input("Enter Today's Festival", key="festival_input")

            if st.button("Send Greetings"):
                users = get_users_by_area(area)
                if users:
                    for user in users:
                        user_id, name, email, phone, birthday, area = user
                        result = chain.invoke({"name": name, "occasion": festival})
                        st.write(f"**To:** {name} | **Email:** {email} | **Phone:** {phone}")
                        st.write(result)
                        if send_email(email, result.subject, result.email):
                            st.success("Email sent via Gmail API")
                        st.warning("SMS sending skipped (mock)")
                        save_log(user_id, "festival", result.email)
                else:
                    st.info("No users found in this area.")

        with col2:
            if 'area' in locals() and area:
                users_in_area = get_users_by_area(area)
                if users_in_area:
                    users_df = pd.DataFrame(users_in_area, columns=["ID", "Name", "Email", "Phone", "Birthday", "Area"])
                    st.subheader(f"Users in {area}")
                    st.dataframe(users_df[["Name", "Email", "Phone"]])
                else:
                    st.info(f"No users found in {area} area.")

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

elif menu == "Manage Users":
    st.subheader("Add New User")
    with st.form("add_user_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        birthday = st.date_input("Birthday")
        area = st.text_input("Area")
        submitted = st.form_submit_button("Add User")
        if submitted:
            add_user(name, email, phone, birthday.strftime('%Y-%m-%d'), area)
            st.success("User added successfully.")

    st.subheader("Import Users via CSV")
    csv_file = st.file_uploader("Upload CSV", type="csv")
    if csv_file is not None:
        import_users_from_csv(csv_file)
        st.success("Users imported successfully.")

    st.subheader("All Users")
    conn = sqlite3.connect("users.db")
    df = pd.read_sql_query("SELECT * FROM users", conn)
    st.dataframe(df)
    conn.close()

elif menu == "Manage Festivals":
    st.subheader("Add Festival Manually")

    # Get unique areas from user table for selection
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT area FROM users WHERE area IS NOT NULL AND area != ''")
    user_areas = [row[0] for row in cursor.fetchall()]
    conn.close()

    with st.form("add_festival_form"):
        area = st.selectbox("Select Area (from users)", user_areas, key="festival_area_select") if user_areas else st.text_input("Area")
        name = st.text_input("Festival Name")
        submitted = st.form_submit_button("Add Festival")
        if submitted:
            add_festival(area, name)
            st.success("Festival added successfully.")

    st.subheader("Import Festivals via CSV")
    csv_file = st.file_uploader("Upload Festival CSV", type="csv")
    if csv_file is not None:
        import_festivals_from_csv(csv_file)
        st.success("Festivals imported successfully.")

    st.subheader("All Festivals")
    conn = sqlite3.connect("users.db")
    df = pd.read_sql_query("SELECT * FROM festivals", conn)
    st.dataframe(df)
    conn.close()