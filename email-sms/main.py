import streamlit as st
from modules import greetings, auto_reply, db, gmail_watch, user_manage,festive_manage, manage_gmail

st.set_page_config(page_title="Unified Email AI App", layout="wide")
st.sidebar.title("Navigation")

# ...existing sidebar...
page = st.sidebar.radio(
    "Go to",
    [
        "Greeting Workflow",
        "Auto-Reply",
        "Email Logs",
        "Manage Users",
        "Manage Festivals",
        # "Gmail Watch Setup",
        "Manage Gmail"
    ]
)

db.init_db()  # Ensure DB is ready

if page == "Greeting Workflow":
    greetings.greeting_workflow()
elif page == "Auto-Reply":
    auto_reply.auto_reply_ui()
elif page == "Email Logs":
    db.show_email_logs()
elif page == "Manage Users":
    user_manage.user_manage_ui()
elif page == "Manage Festivals":
    festive_manage.festive_manage_ui()
elif page == "Gmail Watch Setup":
    gmail_watch.streamlit_watch_ui()
elif page == "Manage Gmail":
    manage_gmail.gmail_manage_ui()


