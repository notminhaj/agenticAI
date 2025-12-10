"""
Build KB Index - Generates embeddings for all notes in the knowledge base.

This script:
1. Reads topics from kb_metadata.json
2. Loads markdown content from each note file
3. Generates E5 embeddings (same model as kb_read and kb_write)
4. Saves to kb_index.json

Run with: python build_kb_index.py
"""

import json
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer

# Constants
ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "kb_metadata.json"
NOTES_DIR = ROOT / "notes"
INDEX_PATH = ROOT / "embeddings" / "kb_index.json"
MAX_CONTENT_CHARS = 6000

# Load embedding model
print("Loading E5 embedding model...")
model = SentenceTransformer("intfloat/e5-base-v2")


def load_topics() -> dict:
    """Load topics from kb_metadata.json."""
    if not METADATA_PATH.exists():
        print(f"[ERROR] Metadata file not found: {METADATA_PATH}")
        return {}
    
    with METADATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("topics", {})


def read_markdown(path: Path) -> str:
    """Read markdown file content."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[:MAX_CONTENT_CHARS] if len(text) > MAX_CONTENT_CHARS else text


def embed_text(text: str) -> List[float]:
    """Generate E5 embedding for text."""
    # E5 model expects "passage: " prefix for documents
    embedding = model.encode(f"passage: {text}", normalize_embeddings=True)
    return embedding.tolist()


def main():
    """Main function to build the KB index."""
    topics = load_topics()
    
    if not topics:
        print("[ERROR] No topics found in metadata")
        return
    
    print(f"Found {len(topics)} topics in metadata")
    
    records = []
    
    for topic, meta in topics.items():
        rel_path = meta.get("note_path", "")
        
        if not rel_path:
            print(f"[SKIP] No note_path for topic '{topic}'")
            continue
        
        # Resolve note path relative to conversational_mode directory
        note_path = ROOT.parent / rel_path
        
        if not note_path.exists():
            print(f"[SKIP] File not found for '{topic}': {note_path}")
            continue
        
        content = read_markdown(note_path)
        
        if not content.strip():
            print(f"[SKIP] Empty note for '{topic}'")
            continue
        
        print(f"[EMBED] {topic}")
        embedding = embed_text(content)
        
        slug = Path(rel_path).stem
        records.append({
            "id": slug,
            "title": topic,
            "note_path": rel_path,
            "embedding": embedding
        })
    
    # Save index
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(records)} records to {INDEX_PATH}")


if __name__ == "__main__":
    main()
