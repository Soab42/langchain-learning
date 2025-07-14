# greeting_workflow_demo.py
import streamlit as st
import sqlite3
import datetime
import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# --- Configuration ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

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

option = st.radio("Select Greeting Type:", ("Birthday", "Festival by Area"))

if option == "Birthday":
    users = get_today_birthdays()
    if users:
        for user in users:
            user_id, name, email, phone, birthday, area = user
            result = chain.run({"name": name, "occasion": "birthday"})
            st.write(f"**To:** {name} | **Email:** {email} | **Phone:** {phone}")
            st.write(result)
            st.success("Mock email sent via Gmail API")
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
                st.success("Mock email sent via Gmail API")
                st.warning("SMS sending skipped (mock)")
                save_log(user_id, "festival", result)
        else:
            st.info("No users found in this area.")
