import streamlit as st
from modules.gmail import fetch_unread_emails, get_email_detail, mark_as_read, send_email, get_email_header, get_email_content
import html # Import the html module

def gmail_manage_ui():
    st.header("Gmail Inbox")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Navigation")
        if st.button("Compose", use_container_width=True):
            st.session_state.show_compose = True
            st.session_state.selected_email_id = None
        if st.button("Inbox", use_container_width=True):
            st.session_state.show_compose = False
            st.session_state.selected_email_id = None
            st.session_state.refresh_inbox = True
        # Add more navigation options here if needed (e.g., Sent, Drafts)

    with col2:
        if st.session_state.get('show_compose', False):
            st.subheader("New Message")
            with st.form("send_email_form"):
                to_email = st.text_input("To")
                subject = st.text_input("Subject")
                body = st.text_area("Body", height=200)
                submitted = st.form_submit_button("Send")
                if submitted:
                    try:
                        # Note: The send_email function in modules/gmail.py is currently a 'pass' function.
                        # It needs to be implemented there for this to work.
                        send_email(to_email, subject, body)
                        st.success("Email send request initiated. (Note: send_email function needs full implementation in modules/gmail.py)")
                        st.session_state.show_compose = False # Hide compose after sending
                    except Exception as e:
                        st.error(f"Error sending email: {e}")
        else:
            st.subheader("Inbox")
            if st.session_state.get('refresh_inbox', True):
                st.session_state.unread_emails = fetch_unread_emails()
                st.session_state.refresh_inbox = False

            if st.session_state.unread_emails:
                st.write(f"Displaying {len(st.session_state.unread_emails)} unread emails.")
                for email in st.session_state.unread_emails:
                    email_id = email.get('id', '(No ID)')
                    # Escape the strings before embedding in HTML
                    escaped_sender = html.escape(email.get('sender', '(No Sender)'))
                    escaped_subject = html.escape(email.get('subject', '(No Subject)'))
                    escaped_snippet = html.escape(email.get('snippet', '(No Snippet)'))

                    # Display email summary
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 5px;">
                        <b>From:</b> {escaped_sender}<br>
                        <b>Subject:</b> {escaped_subject}<br>
                        <small>{escaped_snippet}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    col_buttons_1, col_buttons_2 = st.columns(2)
                    with col_buttons_1:
                        if st.button("Mark as Read", key=f"mark_read_{email_id}"):
                            mark_as_read(email_id)
                            st.success(f"Email {email_id} marked as read.")
                            st.session_state.refresh_inbox = True # Refresh inbox to remove read email
                            st.experimental_rerun()
            else:
                st.info("No unread emails found.")

    # Initialize session state variables
    if 'show_compose' not in st.session_state:
        st.session_state.show_compose = False
    if 'selected_email_id' not in st.session_state:
        st.session_state.selected_email_id = None
    if 'unread_emails' not in st.session_state:
        st.session_state.unread_emails = []
    if 'refresh_inbox' not in st.session_state:
        st.session_state.refresh_inbox = True
