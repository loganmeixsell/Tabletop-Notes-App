import streamlit as st
from components.db import init_db
from components.profile_cards import display_all_profiles, add_profile, save_profile_image
import sqlite3

init_db()


st.title("Characters")

def load_profiles():
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, age, history, photo_url FROM profiles")
    rows = cursor.fetchall()
    conn.close()
    return [
        {'id': row[0], 'name': row[1], 'age': row[2], 'history': row[3], 'photo_url': row[4]}
        for row in rows
    ]

if st.button("Add Profile"):
    st.session_state["adding_profile"] = True

if st.session_state.get("adding_profile", False):
    with st.form("add_profile_form"):
        st.subheader("New Profile")
        new_name = st.text_input("Name")
        new_age = st.number_input("Age", min_value=0, value=25)
        new_history = st.text_area("History")
        uploaded_photo = st.file_uploader("Profile Photo", type=["png", "jpg", "jpeg", "webp"])
        col_submit, col_cancel = st.columns([1, 5])
        with col_submit:
            submitted = st.form_submit_button("Add")
        with col_cancel:
            cancelled = st.form_submit_button("Cancel")

    if submitted and new_name:
        photo_path = save_profile_image(uploaded_photo) if uploaded_photo else ""
        add_profile(new_name, new_age, new_history, photo_path)
        st.session_state["adding_profile"] = False
        st.rerun()
    elif cancelled:
        st.session_state["adding_profile"] = False
        st.rerun()

profiles = load_profiles()
display_all_profiles(profiles, on_change=st.rerun)
