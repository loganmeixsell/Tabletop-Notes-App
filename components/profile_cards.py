import streamlit as st
from typing import List, Dict, Callable
import sqlite3
import os

PROFILES_DIR = "assets/images/profiles"
DEFAULT_PROFILE_IMAGE = f"{PROFILES_DIR}/NoProfile.png"

def save_profile_image(uploaded_file) -> str:
    """Save an uploaded image to the profiles directory and return its path."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    file_path = f"{PROFILES_DIR}/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def add_profile(name: str, age: int, history: str, photo_url: str):
    """Insert a new profile into the database"""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO profiles (name, age, history, photo_url) VALUES (?, ?, ?, ?)",
        (name, age, history, photo_url or DEFAULT_PROFILE_IMAGE)
    )
    conn.commit()
    conn.close()

def update_profile(profile_id: int, name: str, age: int, history: str, photo_url: str):
    """Update a profile in the database"""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE profiles SET name = ?, age = ?, history = ?, photo_url = ? WHERE id = ?",
        (name, age, history, photo_url, profile_id)
    )
    conn.commit()
    conn.close()

def delete_profile(profile_id: int):
    """Delete a profile from the database"""
    conn = sqlite3.connect('note_database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()

def display_profile_card(profile_id: int, name: str, age: int, history: str, photo_url: str, on_change: Callable = None):
    """Display a single profile card with edit capability"""
    with st.container():
        # Card styling
        st.markdown("""
        <style>
        .profile-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create a unique session state key for this profile
        edit_key = f"editing_{profile_id}"
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(photo_url or DEFAULT_PROFILE_IMAGE, width=150)
        
        with col2:
            if st.session_state.get(edit_key, False):
                # Edit mode
                st.subheader("Edit Profile")
                
                edited_name = st.text_input("Name", value=name, key=f"name_{profile_id}")
                edited_age = st.number_input("Age", value=age, key=f"age_{profile_id}")
                edited_history = st.text_area("History", value=history, key=f"history_{profile_id}")
                uploaded = st.file_uploader("Replace Photo", type=["png", "jpg", "jpeg", "webp"], key=f"photo_upload_{profile_id}")
                edited_photo_url = save_profile_image(uploaded) if uploaded else photo_url

                col_save, col_cancel, col_delete = st.columns(3)

                with col_save:
                    if st.button("Save", key=f"save_{profile_id}"):
                        update_profile(profile_id, edited_name, edited_age, edited_history, edited_photo_url)
                        st.session_state[edit_key] = False
                        if on_change:
                            on_change()
                        st.rerun()
                
                with col_cancel:
                    if st.button("Cancel", key=f"cancel_{profile_id}"):
                        st.session_state[edit_key] = False
                        st.rerun()
                
                with col_delete:
                    if st.button("Delete", key=f"delete_{profile_id}", type="secondary"):
                        delete_profile(profile_id)
                        if on_change:
                            on_change()
                        st.rerun()
            else:
                # View mode
                st.subheader(name)
                st.write(f"**Age:** {age}")
                st.write(f"**History:** {history}")
                
                col_edit, col_spacer = st.columns([1, 4])
                with col_edit:
                    if st.button("Edit", key=f"edit_{profile_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
        
        st.divider()

def display_all_profiles(profiles: List[Dict], on_change: Callable = None):
    """Display all profile cards from database rows, 3 per row"""
    for i in range(0, len(profiles), 3):
        cols = st.columns(3)
        for col, profile in zip(cols, profiles[i:i+3]):
            with col:
                display_profile_card(
                    profile_id=profile['id'],
                    name=profile['name'],
                    age=profile['age'],
                    history=profile['history'],
                    photo_url=profile['photo_url'],
                    on_change=on_change
                )