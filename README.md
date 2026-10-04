# 🐉 Dungeon Notes

A modern, local-first campaign management dashboard and AI assistant built with **Streamlit**, **SQLite**, and **ChromaDB + Ollama**.

Organize characters, chronicle sessions, and ask natural language questions about your world lore and notes—100% locally with no external API keys or cloud dependencies.

---

## ✨ Features

- 🧙 **Character Profiles**: Manage player characters and NPCs with portrait avatars, background history, and stats.
- 📝 **Session Chronicles**: Track session-by-session notes, edit recaps on the fly, and switch into a consolidated "Read All Notes" view.
- 🐉 **AI Campaign Assistant (RAG)**: Query your campaign notes in plain English using Retrieval-Augmented Generation (RAG) powered by **ChromaDB** vector search and local **Ollama** LLMs (e.g. `llama3.1`).
- 🔒 **100% Local & Private**: All notes, vector databases, and LLM inferences run directly on your machine.
- 🚀 **Zero-Config Database**: Automatic schema initialization for SQLite tables on startup.

---

## 📁 Project Structure

```text
Dungeon Notes/
├── app.py                      # Application entrypoint & navigation
├── components/
│   ├── db.py                   # Automatic SQLite database initialization
│   ├── profile_cards.py        # Character cards UI and database operations
│   └── session_notes.py        # Session management & note-taking components
├── pages/
│   ├── characters.py           # Character gallery page
│   ├── session_notes.py        # Session log & chronicle page
│   └── rag_asker.py            # AI note search & Q&A interface
├── apps/
│   └── rag/
│       ├── dnd_indexer.py      # Chunks & indexes markdown notes into ChromaDB
│       ├── dnd_query.py        # CLI & core RAG retrieval engine
│       ├── notes/              # Your campaign markdown / text notes
│       └── README.md           # RAG-specific documentation
├── assets/
│   └── images/profiles/        # Character profile photos & default avatars
├── requirements.txt            # Python dependencies
└── .gitignore                  # Git exclusions (caches, DBs, personal notes)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- (Optional, for AI Q&A) **[Ollama](https://ollama.com/)** installed and running.

### 2. Clone & Setup Environment

```bash
git clone https://github.com/<your-username>/dungeon-notes.git
cd "dungeon-notes"

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`. Database tables (`note_database.db`) will be automatically created on first launch.

---

## 🤖 Using the AI Campaign Assistant (RAG)

To enable asking questions against your campaign notes:

1. **Pull an Ollama Model:**
   ```bash
   ollama pull llama3.1
   ```
   *(Or a lighter model like `ollama pull mistral`)*

2. **Add Notes:**
   Place your Markdown (`.md`) or text (`.txt`) notes in `apps/rag/notes/`. Notes can include optional frontmatter headers:
   ```markdown
   ---
   type: character
   name: Mira Stonewhisper
   status: alive
   location: Thornhaven
   tags: [innkeeper, informant]
   ---

   # Mira Stonewhisper
   Owns the Silver Coin Inn. Rumored to hold information on the Thieves Guild.
   ```

3. **Index Notes into ChromaDB:**
   ```bash
   python apps/rag/dnd_indexer.py
   ```

4. **Ask Questions:**
   Navigate to the **RAG Asker** page in the Streamlit app, or run the interactive terminal interface:
   ```bash
   python apps/rag/dnd_query.py
   ```

---

## 🛡️ Privacy & Git

This repository is configured with a `.gitignore` that keeps your personal game data safe:
- Local SQLite databases (`*.db`) are ignored.
- Local vector stores (`.chromadb/`) and index hashes are ignored.
- Personal campaign note files (`apps/rag/notes/`) and uploaded character portraits are excluded from Git commits.

