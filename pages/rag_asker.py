import sys
from pathlib import Path

import streamlit as st

RAG_DIR = Path(__file__).parent.parent / "apps" / "rag"
sys.path.insert(0, str(RAG_DIR))

import dnd_query

dnd_query.DB_DIR = RAG_DIR / ".chromadb"

st.title("🐉 RAG Asker")
st.caption("Ask questions about your campaign notes using local AI.")


@st.cache_resource
def load_collection():
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=str(dnd_query.DB_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=dnd_query.EMBED_MODEL
    )
    return client.get_collection(name=dnd_query.COLLECTION_NAME, embedding_function=ef)


if not dnd_query.DB_DIR.exists():
    st.error("No database found. Run `python apps/rag/dnd_indexer.py` first to index your notes.")
    st.stop()

try:
    collection = load_collection()
except Exception as e:
    st.error(f"Failed to load note database: {e}")
    st.stop()

st.caption(f"{collection.count()} chunks indexed | Model: {dnd_query.OLLAMA_MODEL}")

st.divider()

TYPE_OPTIONS = ["All", "character", "location", "faction", "session", "item"]

col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_input("Your question", placeholder="e.g. What do we know about Mira?")
with col2:
    type_filter_label = st.selectbox("Filter by type", TYPE_OPTIONS)

type_filter = None if type_filter_label == "All" else type_filter_label

if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching notes and generating answer..."):
            chunks = dnd_query.retrieve(collection, question, type_filter=type_filter)
            answer = dnd_query.ask(collection, question, type_filter=type_filter)
        st.session_state["rag_answer"] = answer
        st.session_state["rag_chunks"] = chunks

if "rag_answer" in st.session_state:
    st.markdown(st.session_state["rag_answer"])

    chunks = st.session_state.get("rag_chunks", [])
    seen = {}
    sources = []
    for c in chunks:
        if c["source"] not in seen:
            seen[c["source"]] = True
            sources.append((c["source"], 1 - c["distance"]))

    if sources:
        with st.expander("📚 Sources consulted"):
            for src, relevance in sources:
                st.markdown(f"- **{src}** — {relevance:.0%} relevance")