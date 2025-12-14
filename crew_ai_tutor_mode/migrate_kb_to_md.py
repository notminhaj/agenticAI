import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # adjust if needed
KB_JSON = ROOT / "agentic_ai_tutor" / "knowledge" / "profile.json"
NOTES_DIR = ROOT / "agentic_ai_tutor" / "knowledge_base" / "notes"

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or "note"

def main():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    with KB_JSON.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    topics = profile["topics"]

    new_kb = {}
    for topic, data in topics.items():
        notes = data.get("notes", "").strip()
        slug = slugify(topic)
        note_path = NOTES_DIR / f"{slug}.md"

        # write markdown file
        with note_path.open("w", encoding="utf-8") as f:
            f.write(f"# {topic}\n\n")
            if notes:
                f.write(notes + "\n")
            else:
                f.write("_No notes yet. This file was created during migration._\n")

        # build new registry entry
        new_kb[topic] = {
            "mastery": data.get("mastery", 0.0),
            "confidence": data.get("confidence", 0.0),
            "note_path": str(note_path.relative_to(ROOT)),
            "last_reviewed": data.get("last_reviewed")
        }

    with KB_JSON.open("w", encoding="utf-8") as f:
        json.dump(new_kb, f, indent=2, ensure_ascii=False)

    print("Migration complete. Notes written to", NOTES_DIR)

if __name__ == "__main__":
    main()
