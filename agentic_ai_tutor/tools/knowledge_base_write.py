import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from crewai.tools import tool
from sentence_transformers import SentenceTransformer
import re

# Constants
# Constants
ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
TIMELINE_PATH = KNOWLEDGE_BASE_DIR / "timeline.json"
NOTES_DIR = KNOWLEDGE_BASE_DIR / "notes"
EMBEDDINGS_PATH = KNOWLEDGE_BASE_DIR / "embeddings" / "kb_index.json"

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

@tool
def knowledge_base_write(topic: str, 
                         mastery: float = -1.0, 
                         confidence: float = -1.0, 
                         reason: str = "", 
                         source: str = "agent",
                         note: str = "",
                         mode: str = "append") -> Dict[str, Any]:
    """
    Unified tool for writing to the user's knowledge base.
    
    CRITICAL INSTRUCTION FOR AGENT:
    You MUST update the knowledge base with any new information you are about to explain to the user 
    BEFORE you send your final response. The user is learning from you, so if you teach them something new, 
    record it in their knowledge base so you remember next time that they know it.
    
    Args:
        topic (str, required): The main topic name (e.g., "Agentic AI", "Python Loops"). Required.
        mastery (float, optional): Your assessment of the user's mastery (0-10). Use -1.0 to skip updating.
        confidence (float, optional): Your assessment of the user's confidence (0-10). Use -1.0 to skip updating.
        reason (str, optional): Why are you updating this? (e.g., "User asked about X", "User demonstrated knowledge of Y").
        source (str, optional): Where did this info come from? (e.g., "agent", "user").
        note (str, optional): A concise summary of the NEW information you are teaching the user. 
                              Defaults to "" (no note).
        mode (str, required): "append" to add to existing notes (RECOMMENDED), "replace" to overwrite. Default "append".
        
    Returns:
        dict: A dictionary containing:
            - "metadata_update": Confirmation that mastery/confidence were updated.
            - "note_write": Confirmation that the note was saved and embedded.
    """
    
    results = {}
    
    # Always update metadata (even if no changes, it checks/creates profile)
    results["metadata_update"] = _update_metadata(topic, mastery, confidence, reason, source)
    
    # Write note if provided
    if note:
        results["note_write"] = _write_note(topic, note, mode)
        
    return results

def _update_metadata(topic: str, mastery: float, confidence: float, reason: str, source: str) -> Dict[str, Any]:
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load KB Index
    kb_index = []
    if EMBEDDINGS_PATH.exists():
        try:
            kb_index = json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))
            if not isinstance(kb_index, list):
                kb_index = []
        except:
            kb_index = []

    # Find or create record
    record = None
    record_idx = -1
    for i, item in enumerate(kb_index):
        if item.get("title") == topic:
            record = item
            record_idx = i
            break
            
    if record is None:
        record = {
            "id": slugify(topic),
            "title": topic,
            "note_path": f"knowledge_base/notes/{slugify(topic)}.md",
            "embedding": [],
            "mastery": 0.0,
            "confidence": 0.0,
            "last_reviewed": None
        }
        kb_index.append(record)
        record_idx = len(kb_index) - 1

    changes = []

    if mastery >= 0:
        mastery = float(max(0, min(10, mastery)))
        old = record.get("mastery", 0.0)
        if old != mastery:
            record["mastery"] = mastery
            changes.append(("mastery", old, mastery))

    if confidence >= 0:
        confidence = float(max(0, min(10, confidence)))
        old = record.get("confidence", 0.0)
        if old != confidence:
            record["confidence"] = confidence
            changes.append(("confidence", old, confidence))

    if changes:
        record["last_reviewed"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        kb_index[record_idx] = record
        EMBEDDINGS_PATH.write_text(json.dumps(kb_index, indent=2), encoding="utf-8")

    # Timeline logging
    if changes:
        if TIMELINE_PATH.exists():
            try:
                timeline = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
                if not isinstance(timeline, list):
                    timeline = []
            except:
                timeline = []
        else:
            timeline = []

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for (field, old, new) in changes:
            timeline.append({
                "timestamp": ts,
                "event": "metadata_update",
                "topic": topic,
                "field": field,
                "old_value": old,
                "new_value": new,
                "reason": reason,
                "source": source
            })

        TIMELINE_PATH.write_text(json.dumps(timeline, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "topic": topic,
        "message": "Updated fields: " + ", ".join([c[0] for c in changes]) if changes else "No changes"
    }

def _write_note(topic: str, note: str, mode: str) -> Dict[str, Any]:
    md_path = NOTES_DIR / f"{slugify(topic)}.md"
    
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write or append markdown file
    if mode == "replace" or not md_path.exists():
        md_path.write_text(f"# {topic}\n\n{note}\n", encoding="utf-8")
    else:
        with open(md_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + note + "\n")

    # Load embedding index
    if EMBEDDINGS_PATH.exists():
        try:
            index = json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))
            if not isinstance(index, list):
                index = []
        except:
            index = []
    else:
        index = []

    # Generate embedding
    model = SentenceTransformer("intfloat/e5-base-v2")
    vec = model.encode([md_path.read_text(encoding="utf-8")])[0]
    
    # Update or append record
    note_rel_path = f"knowledge_base/notes/{slugify(topic)}.md"
    
    updated = False
    for i, item in enumerate(index):
        if item.get("title") == topic or item.get("note_path") == note_rel_path:
            # Preserve existing metadata
            record = item
            record["title"] = topic # Ensure title matches
            record["note_path"] = note_rel_path
            record["embedding"] = vec.tolist()
            # mastery, confidence, last_reviewed are preserved
            index[i] = record
            updated = True
            break
            
    if not updated:
        record = {
            "id": slugify(topic),
            "title": topic,
            "note_path": note_rel_path,
            "embedding": vec.tolist(),
            "mastery": 0.0,
            "confidence": 0.0,
            "last_reviewed": None
        }
        index.append(record)

    EMBEDDINGS_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "slugified-topic": slugify(topic),
        "message": "Note written and embeddings updated.",
        "embedding_dim": len(vec)
    }
