import os
import json
from pathlib import Path
from typing import List
import openai
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
KB_JSON_PATH = Path(__file__).resolve().parent / "knowledge_base.json"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
INDEX_PATH = Path(__file__).resolve().parent / "embeddings" / "kb_index.json"

# Load environment from root-level .env
dotenv_path = ROOT / ".env"
load_dotenv(dotenv_path, override=True)

# Debugging
print(f"Loading .env from: {dotenv_path}")
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

EMBED_MODEL = "text-embedding-3-small"
MAX_CONTENT_CHARS = 6000

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_topics():
    with KB_JSON_PATH.open("r", encoding="utf-8") as f:
        kb = json.load(f)
    # Support both schema: with 'topics' key, or flat topic mapping
    if "topics" in kb:
        topics_dict = kb["topics"]
    else:
        topics_dict = kb
    return topics_dict

def read_markdown(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[:MAX_CONTENT_CHARS] if len(text) > MAX_CONTENT_CHARS else text

def get_openai_client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    openai.api_key = OPENAI_API_KEY
    return openai

def embed_text(text: str) -> List[float]:
    client = get_openai_client()
    resp = client.Embedding.create(
        model=EMBED_MODEL,
        input=text,
    )
    return resp["data"][0]["embedding"]

def main():
    topics = load_topics()
    records = []
    for topic, meta in topics.items():
        rel_path = meta.get("note_path")
        if not rel_path:
            continue
        project_root = Path(__file__).resolve().parents[1]
        note_path = (project_root / rel_path).resolve()
        print(f"Checking for note file at: {note_path}")
        if not note_path.exists():
            print(f"[SKIP] File not found for topic '{topic}': {rel_path}")
            continue
        content = read_markdown(note_path)
        if not content.strip():
            print(f"[SKIP] Empty note for topic '{topic}': {rel_path}")
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
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"Saved {len(records)} records to {INDEX_PATH}")

if __name__ == "__main__":
    main()
