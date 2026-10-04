import streamlit as st
import sqlite3
from components.db import init_db
from components.session_notes import display_all_sessions, display_all_notes_page, add_session

init_db()

st.title("📝 Session Notes")

if "view_all_notes" not in st.session_state:
    st.session_state.view_all_notes = False

def load_sessions():
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, session_name, created_date FROM sessions ORDER BY created_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'session_name': r[1], 'created_date': r[2]} for r in rows]

# Top bar: toggle button
if st.session_state.view_all_notes:
    if st.button("← Back to Sessions"):
        st.session_state.view_all_notes = False
        st.rerun()
    st.subheader("All Notes")
    display_all_notes_page()
else:
    if st.button("📖 View All Notes"):
        st.session_state.view_all_notes = True
        st.rerun()

    # Create new session section
    st.subheader("New Session")
    col1, col2 = st.columns([4, 1])
    with col1:
        new_session_name = st.text_input("Session Name", placeholder="e.g., Campaign Session #1")
    with col2:
        st.write("")
        if st.button("Create Session", type="primary"):
            if new_session_name.strip():
                add_session(new_session_name)
                st.rerun()
            else:
                st.warning("Please enter a session name")

    st.divider()

    sessions = load_sessions()
    display_all_sessions(sessions, on_change=st.rerun)
