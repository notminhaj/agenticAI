import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from crewai.tools import tool
from sentence_transformers import SentenceTransformer
import re

# Constants
ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
PROFILE_PATH = KNOWLEDGE_DIR / "profile.json"
TIMELINE_PATH = KNOWLEDGE_DIR / "timeline.json"
NOTES_DIR = ROOT / "knowledge_base" / "notes"
EMBEDDINGS_PATH = ROOT / "knowledge_base" / "embeddings" / "kb_index.json"

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

@tool
def knowledge_base_write(topic: str, 
                         mastery: float = None, 
                         confidence: float = None, 
                         reason: str = "", 
                         source: str = "agent",
                         note: str = None,
                         mode: str = "append") -> Dict[str, Any]:
    """
    Unified tool for writing to the user's knowledge base.
    
    Args:
        topic (str): The topic name. Required.
        mastery (float, optional): New mastery level (0-10).
        confidence (float, optional): New confidence level (0-10).
        reason (str, optional): Reason for update.
        source (str, optional): Source of information ('agent' or 'user').
        note (str, optional): Content of the note to write.
        mode (str, optional): "append" or "replace" for note writing. Default "append".
        
    Returns:
        dict: A dictionary containing results from the executed operations:
            - "metadata_update": Result of metadata update (always executed).
            - "note_write": Result of note writing (if note provided).
    """
    
    results = {}
    
    # Always update metadata (even if no changes, it checks/creates profile)
    results["metadata_update"] = _update_metadata(topic, mastery, confidence, reason, source)
    
    # Write note if provided
    if note:
        results["note_write"] = _write_note(topic, note, mode)
        
    return results

def _update_metadata(topic: str, mastery: Optional[float], confidence: Optional[float], reason: str, source: str) -> Dict[str, Any]:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    # Load or create profile
    if PROFILE_PATH.exists():
        try:
            profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except:
            profile = {"updated_at": None, "topics": {}}
    else:
        profile = {"updated_at": None, "topics": {}}

    if "topics" not in profile:
        profile["topics"] = {}

    # Topic entry
    topic_entry = profile["topics"].get(topic, {})

    changes = []

    if mastery is not None:
        mastery = float(max(0, min(10, mastery)))
        old = topic_entry.get("mastery")
        if old != mastery:
            topic_entry["mastery"] = mastery
            changes.append(("mastery", old, mastery))

    if confidence is not None:
        confidence = float(max(0, min(10, confidence)))
        old = topic_entry.get("confidence")
        if old != confidence:
            topic_entry["confidence"] = confidence
            changes.append(("confidence", old, confidence))

    if changes:
        topic_entry["last_reviewed"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        profile["topics"][topic] = topic_entry
        profile["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    # Timeline logging
    if changes:
        if TIMELINE_PATH.exists():
            try:
                timeline = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
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
    record = {
        "title": topic,
        "note_path": note_rel_path,
        "embedding": vec.tolist()
    }
    
    updated = False
    for i, item in enumerate(index):
        if item.get("title") == topic or item.get("note_path") == note_rel_path:
            index[i] = record
            updated = True
            break
            
    if not updated:
        index.append(record)

    EMBEDDINGS_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "slugified-topic": slugify(topic),
        "message": "Note written and embeddings updated.",
        "embedding_dim": len(vec)
    }
