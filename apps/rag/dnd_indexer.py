"""
dnd_indexer.py
Scans your notes folder and indexes all text files into ChromaDB.
Run this whenever you add or update notes.
"""

import os
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions

# ── Config ────────────────────────────────────────────────────────────────────
_HERE     = Path(__file__).parent
NOTES_DIR = _HERE / "notes"
DB_DIR    = _HERE / ".chromadb"
HASH_FILE = _HERE / ".note_hashes.json"
COLLECTION_NAME = "dnd_notes"

# Uses a local sentence-transformer model (downloads once, ~90MB, no API key needed)
EMBED_MODEL = "all-MiniLM-L6-v2"
# ─────────────────────────────────────────────────────────────────────────────


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract key: value metadata and body from a plain text file.

    Metadata lines at the top of the file use 'key: value' format.
    A blank line separates metadata from the body. If the first line
    is not a 'key: value' pair, the entire file is treated as body.
    """
    meta = {}
    lines = text.splitlines()
    i = 0

    for i, line in enumerate(lines):
        if line.strip() == "":
            # blank line ends the header block
            break
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            # Parse simple lists like [a, b, c]
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip() for v in val[1:-1].split(",")]
            meta[key] = val
        else:
            # Non-metadata line before a blank line — no header block
            meta = {}
            i = 0
            break

    body = "\n".join(lines[i + 1:]).strip() if meta else text.strip()
    return meta, body


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks for better retrieval."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_hashes() -> dict:
    if HASH_FILE.exists():
        return json.loads(HASH_FILE.read_text())
    return {}


def save_hashes(hashes: dict):
    HASH_FILE.write_text(json.dumps(hashes, indent=2))


def index_notes(force: bool = False):
    print(f"🗡️  D&D Notes Indexer")
    print(f"   Notes dir : {NOTES_DIR.resolve()}")
    print(f"   Database  : {DB_DIR.resolve()}")
    print()

    # Set up ChromaDB
    client = chromadb.PersistentClient(path=str(DB_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    hashes = {} if force else load_hashes()
    new_hashes = {}

    txt_files = list(NOTES_DIR.rglob("*.txt"))
    if not txt_files:
        print("⚠️  No text files found in notes/")
        return

    added = updated = skipped = 0

    for path in txt_files:
        rel_path = str(path.relative_to(NOTES_DIR))
        h = file_hash(path)
        new_hashes[rel_path] = h

        if not force and hashes.get(rel_path) == h:
            skipped += 1
            continue

        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        # Build clean metadata for ChromaDB (strings only)
        chroma_meta = {
            "source":   rel_path,
            "filename": path.name,
            "type":     meta.get("type", path.parent.name),  # fallback to folder name
            "name":     meta.get("name", path.stem),
            "status":   meta.get("status", "unknown"),
            "tags":     ", ".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else str(meta.get("tags", "")),
            "indexed_at": datetime.now().isoformat(),
        }

        # Remove old chunks for this file
        existing = collection.get(where={"source": rel_path})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])

        # Chunk and index
        chunks = chunk_text(body)
        for i, chunk in enumerate(chunks):
            doc_id = f"{rel_path}::chunk_{i}"
            collection.add(
                documents=[chunk],
                metadatas=[chroma_meta],
                ids=[doc_id]
            )

        action = "updated" if hashes.get(rel_path) else "added"
        print(f"  {'✏️ ' if action == 'updated' else '✅'} {action:7s}  {rel_path}  ({len(chunks)} chunk{'s' if len(chunks) != 1 else ''})")
        if action == "added":
            added += 1
        else:
            updated += 1

    # Report deleted files
    deleted_files = set(hashes.keys()) - set(new_hashes.keys())
    for rel_path in deleted_files:
        existing = collection.get(where={"source": rel_path})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
        print(f"  🗑️  deleted   {rel_path}")

    save_hashes(new_hashes)

    print()
    print(f"  Done. {added} added, {updated} updated, {skipped} skipped, {len(deleted_files)} deleted.")
    print(f"  Total chunks in DB: {collection.count()}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Index D&D notes into ChromaDB")
    parser.add_argument("--force", action="store_true", help="Re-index all files even if unchanged")
    args = parser.parse_args()
    index_notes(force=args.force)
