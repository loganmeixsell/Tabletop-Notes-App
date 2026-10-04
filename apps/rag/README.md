# 🐉 D&D Notes AI Assistant

Ask questions about your campaign notes in plain English. Fully local — no API keys, no internet required after setup.

---

## How It Works

1. You write notes as Markdown files in the `notes/` folder
2. `dnd_indexer.py` reads them and stores them in a local vector database (ChromaDB)
3. `dnd_query.py` lets you ask questions — it finds the relevant notes and uses a local LLM (via Ollama) to give you a clear answer

---

## Setup

### 1. Install Ollama
Download from https://ollama.com and install it.

Then pull a model (Llama 3.1 is recommended):
```bash
ollama pull llama3.1
```

> **Lighter option** if you have limited RAM: `ollama pull mistral` (4GB vs 8GB)

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

> First run will download the embedding model (~90MB). This is a one-time download.

### 3. Index your notes
```bash
python dnd_indexer.py
```

### 4. Start asking questions
```bash
python dnd_query.py
```

---

## Notes Folder Structure

```
notes/
├── characters/      ← NPCs and player characters
├── locations/       ← Towns, dungeons, buildings
├── factions/        ← Guilds, cults, governments
├── sessions/        ← Session recaps
└── items/           ← Magic items, artifacts
```

---

## Writing Notes (Markdown Format)

Every note file can have optional frontmatter at the top for better filtering:

```markdown
---
type: character
name: Mira Stonewhisper
status: alive
location: Thornhaven
tags: [innkeeper, informant]
---

# Mira Stonewhisper

Your notes here...
```

**Supported `type` values:** `character`, `location`, `faction`, `session`, `item`

If you skip the frontmatter, the folder name is used as the type automatically.

---

## Query Commands

| Command | Description |
|---|---|
| `> What do we know about Mira?` | Ask any question |
| `/filter character` | Only search character notes |
| `/filter location` | Only search location notes |
| `/filter off` | Remove filter |
| `/list` | List all indexed notes |
| `/stats` | Show DB stats |
| `/help` | Show help |
| `/quit` | Exit |

---

## Updating Notes

Just edit or add markdown files in the `notes/` folder, then re-run:

```bash
python dnd_indexer.py
```

Only changed files are re-indexed — it's fast.

To force a full re-index:
```bash
python dnd_indexer.py --force
```

---

## Changing the LLM Model

Edit the top of `dnd_query.py`:

```python
OLLAMA_MODEL = "llama3.1"   # change to any model you have in Ollama
```

Other good options: `mistral`, `gemma2`, `phi3`

---

## Example Questions to Try

```
> What do we know about the Thieves Guild?
> Where have we encountered Mira?
> What's suspicious about the Silver Coin Inn?
> /filter session
> What happened in the most recent session?
> /filter character
> Which characters are based in Thornhaven?
```
