import streamlit as st
import sqlite3
import pandas as pd
from modules import db

def add_user_to_db(name, email, phone, birthday, area, dnc):
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, phone, birthday, area, dnc) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, phone, birthday, area, int(dnc))
    )
    conn.commit()
    conn.close()

def update_user_in_db(user_id, name, email, phone, birthday, area, dnc):
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET name=?, email=?, phone=?, birthday=?, area=?, dnc=? WHERE id=?",
        (name, email, phone, birthday, area, int(dnc), user_id)
    )
    conn.commit()
    conn.close()

def import_users_from_csv(csv_file):
    df = pd.read_csv(csv_file)
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute(
            "INSERT INTO users (name, email, phone, birthday, area, dnc) VALUES (?, ?, ?, ?, ?, ?)",
            (row.get("name"), row.get("email"), row.get("phone"), row.get("birthday"), row.get("area"), int(row.get("dnc", 0)))
        )
    conn.commit()
    conn.close()

def delete_user_from_db(user_id):
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def user_manage_ui():
    col1, col2 = st.columns(2)

    with col1:
        st.header("Add New User")
        with st.form("add_user_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            birthday = st.date_input("Birthday")
            area = st.text_input("Area")
            dnc = st.checkbox("Do Not Contact")
            submitted = st.form_submit_button("Add User")
            if submitted:
                add_user_to_db(name, email, phone, birthday.strftime('%Y-%m-%d'), area, dnc)
                st.success("User added successfully.")

    with col2:
        st.header("Import Users via CSV")
        csv_file = st.file_uploader("Upload CSV", type="csv")
        if csv_file is not None:
            import_users_from_csv(csv_file)
            st.success("Users imported successfully.")

    st.subheader("All Users")
    conn = sqlite3.connect(db.DB_PATH)
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df)

        st.subheader("Update or Delete User")
        user_ids = df["id"].tolist()
        selected_user_id = st.selectbox(
            "Select User to Update/Delete",
            user_ids,
            format_func=lambda x: f"{x} - {df[df['id']==x]['name'].values[0]}"
        )
        user_row = df[df["id"] == selected_user_id].iloc[0]

        with st.form("update_user_form"):
            name = st.text_input("Name", value=user_row["name"])
            email = st.text_input("Email", value=user_row["email"])
            phone = st.text_input("Phone", value=user_row["phone"])
            birthday = st.text_input("Birthday", value=user_row["birthday"])
            area = st.text_input("Area", value=user_row["area"])
            dnc = st.checkbox("Do Not Contact", value=bool(user_row["dnc"]))
            update_submitted = st.form_submit_button("Update User")
            if update_submitted:
                update_user_in_db(selected_user_id, name, email, phone, birthday, area, dnc)
                st.success("User updated successfully.")
                st.experimental_rerun()

        # Delete option
        if st.button("Delete Selected User"):   
            delete_user_from_db(selected_user_id)
            st.success("User deleted successfully.")
            st.experimental_rerun()