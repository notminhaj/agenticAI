import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("c:/Users/ehsan/Documents/practicingAI/agenticAI/agentic_ai_tutor")
KB_DIR = ROOT / "knowledge_base"
KB_INDEX_PATH = KB_DIR / "embeddings" / "kb_index.json"
METADATA_PATH = KB_DIR / "kb_metadata.json"

def migrate():
    print("Starting metadata migration...")
    
    if not KB_INDEX_PATH.exists():
        print("kb_index.json not found!")
        return

    with open(KB_INDEX_PATH, "r", encoding="utf-8") as f:
        kb_index = json.load(f)
        
    metadata = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "topics": {}
    }
    
    new_index = []
    
    for record in kb_index:
        title = record.get("title")
        if not title:
            continue
            
        # Extract metadata
        metadata["topics"][title] = {
            "mastery": record.get("mastery", 0.0),
            "confidence": record.get("confidence", 0.0),
            "last_reviewed": record.get("last_reviewed"),
            "note_path": record.get("note_path", "")
        }
        
        # Clean record for index
        clean_record = {
            "id": record.get("id"),
            "title": title,
            "note_path": record.get("note_path", ""),
            "embedding": record.get("embedding", [])
        }
        new_index.append(clean_record)
        
    # Save metadata
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {METADATA_PATH}")
    
    # Save cleaned index
    with open(KB_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(new_index, f, indent=2)
    print(f"Saved cleaned index to {KB_INDEX_PATH}")
    
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
