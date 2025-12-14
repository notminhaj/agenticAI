import json
import os
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from crewai.tools import tool
from openai import OpenAI

# Constants
ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
EMBEDDINGS_PATH = KNOWLEDGE_BASE_DIR / "embeddings" / "kb_index.json"
METADATA_PATH = KNOWLEDGE_BASE_DIR / "kb_metadata.json"
TIMELINE_PATH = KNOWLEDGE_BASE_DIR / "timeline.json"

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)

def get_embedding(text: str) -> List[float]:
    client = get_client()
    try:
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def slugify(text: str) -> str:
    return text.lower().replace(" ", "-").replace("/", "-")

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
        topic (str): The main topic name (e.g., "Agentic AI", "Python Loops"). Required.
        mastery (float, optional): Your assessment of the user's mastery (0-10). Use -1.0 to skip updating.
        confidence (float, optional): Your assessment of the user's confidence (0-10). Use -1.0 to skip updating.
        reason (str, optional): Why are you updating this? (e.g., "User asked about X", "User demonstrated knowledge of Y").
        source (str, optional): Where did this info come from? (e.g., "agent", "user").
        note (str, optional): A concise summary of the NEW information you are teaching the user. 
                              Defaults to "" (no note).
        mode (str, REQUIRED): "append" to add to existing notes (RECOMMENDED), "replace" to overwrite. Default "append".
        
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
    
    # Load Metadata
    metadata = {"updated_at": "", "topics": {}}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except:
            pass
            
    # Find or create topic record
    if topic not in metadata["topics"]:
        metadata["topics"][topic] = {
            "mastery": 0.0,
            "confidence": 0.0,
            "last_reviewed": None,
            "note_path": f"knowledge_base/notes/{slugify(topic)}.md"
        }
    
    record = metadata["topics"][topic]
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

    # Save Metadata if changed or new
    # We save if there are changes OR if the topic was just added (since we modified metadata["topics"])
    if changes or topic in metadata["topics"]: 
        metadata["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if changes:
             record["last_reviewed"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    # Log to timeline
    if changes or reason:
        _log_event(topic, changes, reason, source)

    return {
        "status": "success",
        "topic": topic,
        "changes": [f"{k}: {v1}->{v2}" for k, v1, v2 in changes],
        "current_state": record
    }

def _write_note(topic: str, content: str, mode: str) -> Dict[str, Any]:
    slug = slugify(topic)
    filename = f"{slug}.md"
    notes_dir = KNOWLEDGE_BASE_DIR / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    filepath = notes_dir / filename
    
    # Write file
    if mode == "replace":
        filepath.write_text(content, encoding="utf-8")
    else:
        existing = ""
        if filepath.exists():
            existing = filepath.read_text(encoding="utf-8") + "\n\n"
        filepath.write_text(existing + content, encoding="utf-8")
        
    # Update Embeddings Index
    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    kb_index = []
    if EMBEDDINGS_PATH.exists():
        try:
            kb_index = json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))
        except:
            kb_index = []
            
    # Find or create index record
    record = None
    for item in kb_index:
        if item.get("title") == topic:
            record = item
            break
            
    full_text = filepath.read_text(encoding="utf-8")
    embedding = get_embedding(full_text)
    
    if record:
        record["embedding"] = embedding
        # Ensure path is correct
        record["note_path"] = f"knowledge_base/notes/{filename}"
    else:
        kb_index.append({
            "id": slug,
            "title": topic,
            "note_path": f"knowledge_base/notes/{filename}",
            "embedding": embedding
        })
        
    EMBEDDINGS_PATH.write_text(json.dumps(kb_index, indent=2), encoding="utf-8")
    
    # Ensure metadata also has the correct note path
    _ensure_metadata_path(topic, f"knowledge_base/notes/{filename}")
    
    return {
        "status": "success",
        "file": str(filepath),
        "size": len(full_text),
        "embeddings_updated": True
    }

def _ensure_metadata_path(topic: str, note_path: str):
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            if topic in metadata["topics"]:
                if metadata["topics"][topic].get("note_path") != note_path:
                    metadata["topics"][topic]["note_path"] = note_path
                    metadata["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
        except:
            pass

def _log_event(topic: str, changes: List[tuple], reason: str, source: str):
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "type": "update",
        "changes": [{"field": k, "old": v1, "new": v2} for k, v1, v2 in changes],
        "reason": reason,
        "source": source
    }
    
    timeline = []
    if TIMELINE_PATH.exists():
        try:
            timeline = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
        except:
            timeline = []
            
    timeline.append(event)
    TIMELINE_PATH.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
