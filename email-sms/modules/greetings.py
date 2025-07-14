import streamlit as st
from modules import db, ai

def greeting_workflow():
    st.header("Greeting Workflow")

    tab1, tab2, tab3 = st.tabs([
        "🎂 Birthday Greetings",
        "🎉 Festival Greetings",
        "🌍 Global/Custom Message"
    ])

    # --- Birthday Greetings ---
    with tab1:
        col1, col2 = st.columns([2, 3])
        with col1:
            users = db.get_today_birthdays()
            if users:
                st.subheader("Today's Birthdays")
                for user in users:
                    user_id, name, email, phone, birthday, area = user[:6]
                    dnc = user[6] if len(user) > 6 else 0
                    st.markdown(f"**Name:** {name} | **Email:** {email} | **Phone:** {phone} | **Area:** {area} | **DNC:** {'Yes' if dnc else 'No'}")
                    if dnc:
                        st.warning("Do Not Contact is enabled for this user. Greeting will not be sent.")
                        continue
                    llm = ai.get_llm()
                    greeting_chain = ai.get_greeting_chain(llm)
                    if st.button(f"Generate Birthday Greeting for {name}", key=f"bday_{user_id}"):
                        result = greeting_chain.invoke({"name": name, "occasion": "Birthday"})
                        st.write(f"**Subject:** {result.subject}")
                        st.write(f"**Email:** {result.email}")
                        st.write(f"**SMS:** {result.sms}")
                        st.markdown("---")
                        st.markdown("**HTML Card Preview:**", unsafe_allow_html=True)
                        st.markdown(result.html_card, unsafe_allow_html=True)
            else:
                st.info("No birthdays today.")

        with col2:
            users = db.get_today_birthdays()
            if users:
                import pandas as pd
                columns = ["ID", "Name", "Email", "Phone", "Birthday", "Area"]
                if len(users[0]) > 6:
                    columns.append("DNC")
                df = pd.DataFrame(users, columns=columns)
                st.subheader("Birthday Users List")
                st.dataframe(df[["Name", "Email", "Phone", "Area"] + (["DNC"] if "DNC" in df.columns else [])])
            else:
                st.info("No birthdays today.")

    # --- Festival Greetings ---
    with tab2:
        col1, col2 = st.columns([2, 3])
        with col1:
            st.subheader("Festival Greetings by Area")
            # Get unique areas from users table
            conn = db.sqlite3.connect(db.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT area FROM users WHERE area IS NOT NULL AND area != ''")
            areas = [row[0] for row in cursor.fetchall()]
         

            area = st.selectbox("Select Area", areas) if areas else st.text_input("Enter Area")
            if area:
                cursor.execute("SELECT name FROM festivals WHERE area=?", (area,))
                festivals = [row[0] for row in cursor.fetchall()]
                festival = st.selectbox("Select Festival", festivals) if festivals else st.text_input("Enter Festival Name")

            if area and festival and st.button("Generate Festival Greetings"):
                # Get users by area
                conn = db.sqlite3.connect(db.DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE area=?", (area,))
                users_in_area = cursor.fetchall()
                conn.close()
                if users_in_area:
                    llm = ai.get_llm()
                    greeting_chain = ai.get_greeting_chain(llm)
                    for user in users_in_area:
                        user_id, name, email, phone, birthday, area = user[:6]
                        dnc = user[6] if len(user) > 6 else 0
                        st.markdown(f"**Name:** {name} | **Email:** {email} | **Phone:** {phone} | **DNC:** {'Yes' if dnc else 'No'}")
                        if dnc:
                            st.warning("Do Not Contact is enabled for this user. Greeting will not be sent.")
                            continue
                        result = greeting_chain.invoke({"name": name, "occasion": festival})
                        st.write(f"**Subject:** {result.subject}")
                        st.write(f"**Email:** {result.email}")
                        st.write(f"**SMS:** {result.sms}")
                        st.markdown("---")
                        st.markdown("**HTML Card Preview:**", unsafe_allow_html=True)
                        st.markdown(result.html_card, unsafe_allow_html=True)
                else:
                    st.info("No users found in this area.")

        with col2:
            # Show users in selected area
            conn = db.sqlite3.connect(db.DB_PATH)
            cursor = conn.cursor()
            if 'area' in locals() and area:
                cursor.execute("SELECT name, email, phone, dnc FROM users WHERE area=?", (area,))
                area_users = cursor.fetchall()
                if area_users:
                    import pandas as pd
                    df = pd.DataFrame(area_users, columns=["Name", "Email", "Phone", "DNC"])
                    st.subheader(f"Users in {area}")
                    st.dataframe(df)
                else:
                    st.info(f"No users found in {area}.")
            conn.close()

    # --- Global/Custom Message ---
    with tab3:
        st.subheader("Send Global/Custom Message")
        # Fetch all unique areas from users table for selection
        conn = db.sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT area FROM users WHERE area IS NOT NULL AND area != ''")
        areas = [row[0] for row in cursor.fetchall()]
        conn.close()

        area_options = ["All (Global)"] + areas if areas else ["All (Global)"]
        selected_areas = st.multiselect(
            "Select Area(s) (leave empty or select 'All (Global)' for all users)",
            area_options,
            default=["All (Global)"]
        )
        custom_occasion = st.text_input("Occasion/Message Title", value="New Year")
        custom_message = st.text_area("Custom Message (optional, will be used as context for AI)", value="")

        if st.button("Generate Global Greetings"):
            # Determine which users to select
            conn = db.sqlite3.connect(db.DB_PATH)
            cursor = conn.cursor()
            if not selected_areas or "All (Global)" in selected_areas:
                cursor.execute("SELECT * FROM users")
            else:
                placeholders = ",".join("?" for _ in selected_areas)
                query = f"SELECT * FROM users WHERE area IN ({placeholders})"
                cursor.execute(query, selected_areas)
            all_users = cursor.fetchall()
            conn.close()
            llm = ai.get_llm()
            greeting_chain = ai.get_greeting_chain(llm)
            for user in all_users:
                user_id, name, email, phone, birthday, area = user[:6]
                dnc = user[6] if len(user) > 6 else 0
                if dnc:
                    continue
                context = custom_message if custom_message else custom_occasion
                result = greeting_chain.invoke({"name": name, "occasion": context})
                st.markdown(f"**Name:** {name} | **Email:** {email} | **Phone:** {phone}")
                st.write(f"**Subject:** {result.subject}")
                st.write(f"**Email:** {result.email}")
                st.write(f"**SMS:** {result.sms}")
                st.markdown("---")
                st.markdown("**HTML Card Preview:**", unsafe_allow_html=True)
                st.markdown(result.html_card, unsafe_allow_html=True)