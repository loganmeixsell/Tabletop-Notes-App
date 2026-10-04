"""
dnd_query.py
Ask questions about your D&D notes using a local Ollama LLM + ChromaDB RAG.
Run: python dnd_query.py
"""

import sys
import textwrap
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
import ollama

# ── Config ────────────────────────────────────────────────────────────────────
DB_DIR          = Path(".chromadb")
COLLECTION_NAME = "dnd_notes"
EMBED_MODEL     = "all-MiniLM-L6-v2"

# Change this to any model you have pulled in Ollama
# Recommended: "llama3.1", "mistral", "gemma2"
OLLAMA_MODEL    = "llama3.1:latest"

# How many note chunks to retrieve per query
TOP_K = 6
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful Dungeon Master's assistant with deep knowledge of the campaign.
You answer questions about characters, locations, factions, items, and events based ONLY on the notes provided.
Be concise and accurate. If the notes don't contain enough information to answer, say so clearly.
When referencing information, mention which note file it came from (shown as 'Source:').
Format your responses clearly. Use bullet points for lists of facts."""


def get_collection():
    if not DB_DIR.exists():
        print("❌ No database found. Run 'python dnd_indexer.py' first.")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(DB_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    ) 
    return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)


def retrieve(collection, query: str, type_filter: str = None, n: int = TOP_K) -> list[dict]:
    """Retrieve relevant note chunks for a query."""
    where = {"type": type_filter} if type_filter else None

    results = collection.query(
        query_texts=[query],
        n_results=min(n, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "name":     meta.get("name", ""),
            "type":     meta.get("type", ""),
            "distance": dist,
        })
    return chunks


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    seen_sources = {}

    for chunk in chunks:
        src = chunk["source"]
        if src not in seen_sources:
            seen_sources[src] = True
            parts.append(f"--- Source: {src} ---")
        parts.append(chunk["text"])

    return "\n\n".join(parts)


def ask(collection, question: str, type_filter: str = None) -> str:
    """Full RAG pipeline: retrieve → build prompt → call Ollama."""
    chunks = retrieve(collection, question, type_filter=type_filter)

    if not chunks:
        return "No relevant notes found. Try indexing your notes first."

    context = build_context(chunks)
    prompt  = f"Here are the relevant campaign notes:\n\n{context}\n\n---\n\nQuestion: {question}"

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"❌ Ollama error: {e}\n\nMake sure Ollama is running and '{OLLAMA_MODEL}' is pulled.\nRun: ollama pull {OLLAMA_MODEL}"


def print_sources(chunks: list[dict]):
    """Print which notes were used to answer."""
    seen = set()
    sources = []
    for c in chunks:
        if c["source"] not in seen:
            seen.add(c["source"])
            sources.append(f"  • {c['source']}  (relevance: {1 - c['distance']:.0%})")
    if sources:
        print("\n📚 Sources consulted:")
        print("\n".join(sources))


def print_help():
    print("""
Commands:
  /filter <type>   Filter by note type: character, location, faction, session, item
  /filter off      Remove type filter
  /list            List all indexed notes
  /stats           Show database stats
  /help            Show this help
  /quit            Exit

Just type a question to search your notes, e.g.:
  > What do we know about Mira?
  > Where have we encountered the Thieves Guild?
  > /filter location
  > What's suspicious about the Silver Coin Inn?
""")


def list_notes(collection):
    results = collection.get(include=["metadatas"])
    seen = {}
    for meta in results["metadatas"]:
        src = meta.get("source", "?")
        if src not in seen:
            seen[src] = meta
    
    by_type = {}
    for src, meta in sorted(seen.items()):
        t = meta.get("type", "other")
        by_type.setdefault(t, []).append((meta.get("name", src), src))
    
    for t, entries in sorted(by_type.items()):
        print(f"\n  📁 {t.upper()}S")
        for name, src in sorted(entries):
            print(f"     • {name}  ({src})")


def main():
    print("🐉 D&D Notes AI Assistant")
    print(f"   Model: {OLLAMA_MODEL}  |  DB: {DB_DIR}")
    print("   Type /help for commands, /quit to exit\n")

    collection  = get_collection()
    type_filter = None

    print(f"   {collection.count()} chunks indexed across your notes.\n")

    while True:
        try:
            prefix = f"[{type_filter}] " if type_filter else ""
            user_input = input(f"🎲 {prefix}> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nFarewell, adventurer! 🗡️")
            break

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd   = parts[0].lower()
            arg   = parts[1] if len(parts) > 1 else ""

            if cmd == "/quit":
                print("Farewell, adventurer! 🗡️")
                break
            elif cmd == "/help":
                print_help()
            elif cmd == "/filter":
                if arg == "off" or arg == "":
                    type_filter = None
                    print("  Filter removed.")
                else:
                    type_filter = arg.lower()
                    print(f"  Filtering by type: {type_filter}")
            elif cmd == "/list":
                list_notes(collection)
                print()
            elif cmd == "/stats":
                print(f"\n  Chunks in DB  : {collection.count()}")
                print(f"  Active filter : {type_filter or 'none'}")
                print(f"  Ollama model  : {OLLAMA_MODEL}\n")
            else:
                print(f"  Unknown command: {cmd}. Type /help for help.")
            continue

        # Query
        print()
        chunks   = retrieve(collection, user_input, type_filter=type_filter)
        answer   = ask(collection, user_input, type_filter=type_filter)

        # Word-wrap the answer nicely
        for line in answer.splitlines():
            if line.startswith(("•", "-", "*", "#")) or line == "":
                print(line)
            else:
                print(textwrap.fill(line, width=80))

        print_sources(chunks)
        print()


if __name__ == "__main__":
    main()
