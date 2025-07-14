import streamlit as st
from modules import db, gmail, ai

def auto_reply_ui():
    st.header("Gmail Auto-Reply")

    emails = db.get_unreplied_emails_from_db()

    if emails:
        col1, col2 = st.columns([2, 5])
        with col1:
            email_options = [
                f"{i+1}. {subject} | {sender}" for i, (_, subject, sender, _, _, _, _) in enumerate(emails)
            ]
            selected_idx = st.radio("Select an email", email_options, index=0, key="auto_reply_email_select")
            idx = email_options.index(selected_idx)
            selected_email = emails[idx]
            email_id, subject, sender, snippet, body, replied, reply = selected_email

        with col2:
            st.markdown(f"**Subject:** {subject}")
            st.markdown(f"**From:** {sender}")
            st.text_area("Email Body", body, height=200)

            if not replied:
                if st.button("🤖 Generate AI Reply", key=f"auto_reply_{email_id}"):
                    with st.spinner("Generating AI reply..."):
                        llm = ai.get_llm()
                        ai_reply = ai.generate_ai_reply(llm, subject, body)
                        db.update_reply_in_db(email_id, ai_reply)
                        st.success("Reply generated and saved!")
                        st.experimental_rerun()
            else:
                st.subheader("🤖 Suggested Reply")
                st.text_area("Reply", reply, height=200)
                st.info("Reply already generated and saved for this email.")
    else:
        st.info("No unreplied emails found.")