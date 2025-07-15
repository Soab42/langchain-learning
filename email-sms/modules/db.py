import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
from modules import gmail
DB_PATH = "emails.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Emails table
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
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            birthday TEXT,
            area TEXT,
            dnc INTEGER DEFAULT 0
        )
    ''')
    # Festivals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS festivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT,
            name TEXT,
            date DATE DEFAULT CURRENT_DATE
        )
    ''')
    # Add date column if not exists
    try:
        cursor.execute("ALTER TABLE festivals ADD COLUMN date TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

def get_today_birthdays():
    today = datetime.now().strftime("%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE strftime('%m-%d', birthday) = ?", (today,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_unreplied_emails_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, sender, snippet, body, replied, reply FROM emails WHERE replied=0 ORDER BY received_at DESC")
    rows = cursor.fetchall()
    gmail.fetch_unread_emails()
    conn.close()
    return rows

def update_reply_in_db(email_id, reply):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    send_mail = gmail.get_email_detail(email_id, reply.subject, reply.reply)
    if not send_mail:
        st.error("Email not found in the database.")
        return
    cursor.execute(
        "UPDATE emails SET replied=1, reply=? WHERE id=?",
        (str(reply), email_id)
    )
    conn.commit()
    conn.close()


def show_email_logs():
    st.header("Email Logs")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM emails ORDER BY received_at DESC", conn)
    gmail.fetch_unread_emails()
    conn.close()
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No emails found in the database.")

def manage_users_ui():
    st.header("Manage Users")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    st.dataframe(df)
    # Add more user management features as needed

def manage_festivals_ui():
    st.header("Manage Festivals")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM festivals", conn)
    conn.close()
    st.dataframe(df)
    # Add more festival management features as needed

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
            "INSERT INTO emails (id, subject, sender, snippet, body, replied, reply) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item["id"], item["subject"], item["sender"], item["snippet"], item["body"], item["replied"], item["reply"])
        )
    conn.commit()
    conn.close()
