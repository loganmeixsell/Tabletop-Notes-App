"""
extract_pdf.py
Extracts clean text from PDF documents using PyMuPDF and saves them as
Markdown notes formatted for the D&D RAG assistant (dnd_indexer.py).

Usage Examples:
    # Convert a single PDF into notes/
    python apps/rag/extract_pdf.py path/to/sourcebook.pdf

    # Convert with custom note type and name
    python apps/rag/extract_pdf.py sourcebook.pdf --type rules --name "Monster Manual"

    # Convert all PDFs found in apps/rag/notes/
    python apps/rag/extract_pdf.py --all

    # Split a large 300-page book into parts of 50 pages each
    python apps/rag/extract_pdf.py monster_manual.pdf --split-pages 50
"""

import re
import sys
import argparse
from pathlib import Path
import pymupdf

# Fix Windows console UTF-8 encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

_HERE = Path(__file__).resolve().parent
DEFAULT_NOTES_DIR = _HERE / "notes"


def clean_page_text(raw_text: str) -> str:
    """Clean common PDF extraction artifacts."""
    if not raw_text:
        return ""

    # Rejoin hyphenated line breaks (e.g. "com-\npanion" -> "companion")
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', raw_text)

    # Normalize excessive carriage returns and trailing whitespace
    lines = [line.strip() for line in text.splitlines()]

    # Collapse multiple blank lines into at most two
    cleaned = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)

    return "\n".join(cleaned).strip()


def extract_pdf_to_notes(
    pdf_path: Path,
    output_dir: Path = DEFAULT_NOTES_DIR,
    note_type: str = "rules",
    note_name: str = None,
    split_pages: int = None,
    include_page_headers: bool = True
) -> list[Path]:
    """
    Extract text from a PDF file and save as Markdown file(s) with RAG frontmatter.
    Returns the list of generated file paths.
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    doc_title = note_name or pdf_path.stem.replace("_", " ").title()

    print(f"📖 Opening PDF: {pdf_path.name}")
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print(f"❌ Could not open PDF {pdf_path.name}: {e}")
        return []

    total_pages = len(doc)
    print(f"   Total Pages: {total_pages}")

    created_files = []

    # If splitting into chunks of pages
    chunk_size = split_pages if (split_pages and split_pages > 0) else total_pages

    for start_idx in range(0, total_pages, chunk_size):
        end_idx = min(start_idx + chunk_size, total_pages)
        part_num = (start_idx // chunk_size) + 1
        total_parts = (total_pages + chunk_size - 1) // chunk_size

        # Determine output filename
        if total_parts > 1:
            out_stem = f"{pdf_path.stem}_part_{part_num:02d}"
            part_title = f"{doc_title} (Part {part_num}: Pages {start_idx + 1}-{end_idx})"
        else:
            out_stem = f"{pdf_path.stem}"
            part_title = doc_title

        out_file = output_dir / f"{out_stem}.md"

        page_texts = []
        for pno in range(start_idx, end_idx):
            page = doc[pno]
            # sort=True ensures multi-column reading order (column 1 then column 2)
            raw = page.get_text("text", sort=True)
            cleaned = clean_page_text(raw)
            if cleaned:
                if include_page_headers:
                    page_texts.append(f"### Page {pno + 1}\n\n{cleaned}")
                else:
                    page_texts.append(cleaned)

        body_content = "\n\n---\n\n".join(page_texts)

        # Build frontmatter compatible with dnd_indexer.py
        frontmatter = (
            f"---\n"
            f"type: {note_type}\n"
            f"name: {part_title}\n"
            f"source: {pdf_path.name}\n"
            f"pages: {start_idx + 1}-{end_idx}\n"
            f"---\n\n"
            f"# {part_title}\n\n"
        )

        full_content = frontmatter + body_content
        out_file.write_text(full_content, encoding="utf-8")
        created_files.append(out_file)

        print(f"   ✅ Saved: {out_file.name} (pages {start_idx + 1} to {end_idx})")

    doc.close()
    return created_files


def main():
    parser = argparse.ArgumentParser(
        description="Convert D&D PDFs into Markdown notes formatted for RAG indexing."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=None,
        help="Path to the PDF file to convert"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert all .pdf files found in the notes folder"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(DEFAULT_NOTES_DIR),
        help=f"Destination directory for markdown notes (default: {DEFAULT_NOTES_DIR})"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="rules",
        help="RAG note type tag (e.g. rules, character, location, faction, item). Default: rules"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Display title of the document for frontmatter metadata"
    )
    parser.add_argument(
        "--split-pages",
        type=int,
        default=None,
        help="Split large PDFs into multiple markdown notes every N pages (e.g. --split-pages 50)"
    )
    parser.add_argument(
        "--no-page-numbers",
        action="store_true",
        help="Do not insert '### Page N' markers between pages"
    )

    args = parser.parse_args()
    out_dir = Path(args.out)

    if args.all:
        pdf_files = list(DEFAULT_NOTES_DIR.rglob("*.pdf"))
        if not pdf_files:
            print(f"⚠️  No .pdf files found in {DEFAULT_NOTES_DIR}")
            return
        print(f"Found {len(pdf_files)} PDF(s) to convert.")
        for pdf in pdf_files:
            extract_pdf_to_notes(
                pdf_path=pdf,
                output_dir=out_dir,
                note_type=args.type,
                split_pages=args.split_pages,
                include_page_headers=not args.no_page_numbers
            )
            print()
        print("🎉 All conversions finished! Run 'python apps/rag/dnd_indexer.py' to index into ChromaDB.")
        return

    if not args.pdf:
        parser.print_help()
        print("\n⚠️ Please provide a PDF file path or use --all.")
        sys.exit(1)

    created = extract_pdf_to_notes(
        pdf_path=Path(args.pdf),
        output_dir=out_dir,
        note_type=args.type,
        note_name=args.name,
        split_pages=args.split_pages,
        include_page_headers=not args.no_page_numbers
    )

    if created:
        print("\n🎉 Done! To index the newly created notes into your vector database, run:")
        print("   python apps/rag/dnd_indexer.py")


if __name__ == "__main__":
    main()
