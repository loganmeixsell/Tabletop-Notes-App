import streamlit as st
from typing import List, Dict, Callable
import sqlite3

def add_session(session_name: str):
    """Add a new session to the database"""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (session_name) VALUES (?)",
        (session_name,)
    )
    conn.commit()
    conn.close()

def delete_session(session_id: int):
    """Delete a session and all its notes from the database"""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    # Delete all notes associated with the session
    cursor.execute("DELETE FROM notes WHERE session_id = ?", (session_id,))
    # Delete the session
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def save_note(session_id: int, note_text: str):
    """Save (upsert) the note text for a session."""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notes WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE notes SET note_text = ? WHERE id = ?", (note_text, row[0]))
    else:
        cursor.execute("INSERT INTO notes (session_id, note_text) VALUES (?, ?)", (session_id, note_text))
    conn.commit()
    conn.close()

def get_session_note(session_id: int) -> str:
    """Get the single note text for a session, or empty string if none."""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT note_text FROM notes WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def display_session_card(session_id: int, session_name: str, created_date: str, on_change: Callable = None):
    """Display a single session card with notes"""
    with st.container():
        st.markdown("""
        <style>
        .session-card {
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            background-color: #f9f9f9;
            background-color: #1C2541;
            color: #F8FAFC;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Session header with delete button
        col_title, col_delete = st.columns([4, 1])
        
        with col_title:
            st.subheader(f"📋 {session_name}")
            st.caption(f"Created: {created_date}")
        
        with col_delete:
            if st.button("🗑️ Delete Session", key=f"delete_session_{session_id}", type="secondary"):
                delete_session(session_id)
                if on_change:
                    on_change()
                st.rerun()
        
        note_text = get_session_note(session_id)
        edited = st.text_area("Notes:", value=note_text, key=f"note_{session_id}", height=200)

        if st.button("Update", key=f"update_note_{session_id}"):
            save_note(session_id, edited)
            if on_change:
                on_change()
            st.rerun()

        st.divider()

def get_all_session_notes() -> List[Dict]:
    """Return all sessions with their note text."""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.session_name, n.note_text
        FROM sessions s
        LEFT JOIN notes n ON n.session_id = s.id
        ORDER BY s.created_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'session_name': r[1], 'note_text': r[2] or ''} for r in rows]

def display_all_notes_page():
    """Render all sessions and their notes as one readable page."""
    all_notes = get_all_session_notes()
    if not all_notes:
        st.info("No sessions yet.")
        return
    for entry in all_notes:
        st.subheader(f"📋 {entry['session_name']}")
        if entry['note_text']:
            st.write(entry['note_text'])
        else:
            st.caption("No notes for this session.")
        st.divider()

def display_all_sessions(sessions: List[Dict], on_change: Callable = None):
    """Display all session cards"""
    if not sessions:
        st.info("No sessions yet. Create one to get started!")
        return
    
    for session in sessions:
        display_session_card(
            session_id=session['id'],
            session_name=session['session_name'],
            created_date=session['created_date'],
            on_change=on_change
        )
