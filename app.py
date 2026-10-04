import streamlit as st
from components.db import init_db

# Initialize database schema if not present
init_db()

st.set_page_config(page_title="Dungeon Notes", layout="wide")

pg = st.navigation([
    st.Page("pages/characters.py", title="Characters", icon="🧙"),
    st.Page("pages/session_notes.py", title="Session Notes", icon="📝"),
    st.Page("pages/rag_asker.py", title="RAG Asker", icon="🐉"),
])
pg.run()
