import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

ROOT = Path("c:/Users/ehsan/Documents/practicingAI/agenticAI/agentic_ai_tutor")
KB_DIR = ROOT / "knowledge_base"
NOTES_DIR = KB_DIR / "notes"
INDEX_PATH = KB_DIR / "embeddings" / "kb_index.json"

def reembed():
    print("Starting re-embedding process...")
    
    # Initialize model
    print("Loading model intfloat/e5-base-v2...")
    model = SentenceTransformer("intfloat/e5-base-v2")
    
    # Load existing index to preserve IDs/titles if possible
    existing_index = []
    if INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                existing_index = json.load(f)
        except:
            pass
            
    # Map existing records by note_path for easy lookup
    existing_map = {rec.get("note_path"): rec for rec in existing_index if rec.get("note_path")}
    
    new_index = []
    
    # Iterate over all markdown files
    if not NOTES_DIR.exists():
        print("No notes directory found.")
        return

    files = list(NOTES_DIR.glob("*.md"))
    print(f"Found {len(files)} notes to embed.")
    
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            rel_path = f"knowledge_base/notes/{file_path.name}"
            
            # Generate embedding
            # e5 models expect "query: " or "passage: " prefix, but for symmetric search or general usage
            # usually "passage: " is used for documents.
            # However, standard usage often omits if not strictly retrieval task.
            # Let's follow standard usage: "passage: " for docs, "query: " for queries.
            embedding = model.encode(f"passage: {content}").tolist()
            
            # Reuse ID/Title if available
            record = existing_map.get(rel_path, {})
            
            new_record = {
                "id": record.get("id", file_path.stem),
                "title": record.get("title", file_path.stem.replace("-", " ").title()),
                "note_path": rel_path,
                "embedding": embedding
            }
            new_index.append(new_record)
            print(f"Processed {file_path.name}")
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            
    # Save new index
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(new_index, f, indent=2)
        
    print(f"Re-embedding complete. Index saved to {INDEX_PATH}")

if __name__ == "__main__":
    reembed()
