import streamlit as st
import sqlite3
import pandas as pd
from tomlkit import date
from modules import db
print(st.__version__)
def add_festival_to_db(area, name,date):
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO festivals (area, name, date) VALUES (?, ?, ?)",
        (area, name, date)
    )
    conn.commit()
    conn.close()

def update_festival_in_db(festival_id, area, name, date=None):
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE festivals SET area=?, name=?, date=? WHERE id=?",
        (area, name, date, festival_id)
    )
    conn.commit()
    conn.close()

def import_festivals_from_csv(csv_file):
    df = pd.read_csv(csv_file)
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute(
            "INSERT INTO festivals (area, name, date) VALUES (?, ?, ?)",
            (row.get("area"), row.get("name"), row.get("date"))
        )
    conn.commit()
    conn.close()

def delete_festival_from_db(festival_id):
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM festivals WHERE id=?", (festival_id,))
    conn.commit()
    conn.close()

    
def festive_manage_ui():
    # Get current user's area from user table
    user_area = st.session_state.get("user_area")

    col1, col2 = st.columns(2)

    with col1:
        st.header("Add New Festival")
        with st.form("add_festival_form"):
            # If user_area is available, prefill and disable area input
            if user_area:
                area = st.selectbox("Area", [user_area], disabled=True)
            else:
                # Fetch all unique areas from the users table for selection
                conn = sqlite3.connect(db.DB_PATH)
                df_areas = pd.read_sql_query("SELECT DISTINCT area FROM users", conn)
                conn.close()
                areas = df_areas["area"].dropna().unique().tolist()
                area = st.selectbox("Area", areas)
            name = st.text_input("Festival Name")
            date = st.date_input("Festival Date")   # Optional date input, not stored in DB but can be used for display
            submitted = st.form_submit_button("Add Festival")
            if submitted:
                add_festival_to_db(area, name, date)
                st.success("Festival added successfully.")

    with col2:
        st.subheader("Import Festivals via CSV")
        csv_file = st.file_uploader("Upload Festival CSV", type="csv")
        if csv_file is not None:
            import_festivals_from_csv(csv_file)
            st.success("Festivals imported successfully.")

    st.subheader("All Festivals")
    conn = sqlite3.connect(db.DB_PATH)
    if user_area:
        df = pd.read_sql_query("SELECT * FROM festivals WHERE area = ?", conn, params=(user_area,))
    else:
        df = pd.read_sql_query("SELECT * FROM festivals", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df)

        st.subheader("Update or Delete Festival")
        festival_ids = df["id"].tolist()
        selected_festival_id = st.selectbox(
            "Select Festival to Update/Delete",
            festival_ids,
            format_func=lambda x: f"{x} - {df[df['id']==x]['name'].values[0]}"
        )
        festival_row = df[df["id"] == selected_festival_id].iloc[0]

        with st.form("update_festival_form"):
            # Area field is prefilled and disabled if user_area is set
            if user_area:
                area = st.text_input("Area", value=user_area, disabled=True)
            else:
                area = st.text_input("Area", value=festival_row["area"])
            name = st.text_input("Festival Name", value=festival_row["name"])
            date = st.date_input("Festival Date", value=pd.to_datetime(festival_row["date"]).date() if pd.notna(festival_row["date"]) else None)
            update_submitted = st.form_submit_button("Update Festival")
            if update_submitted:
                update_festival_in_db(selected_festival_id, area, name)
                st.success("Festival updated successfully.")
                st.experimental_rerun()

        # Delete option
        if st.button("Delete Selected Festival"):
            delete_festival_from_db(selected_festival_id)
            st.success("Festival deleted successfully.")
            st.experimental_rerun()