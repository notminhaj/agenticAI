import json
import os
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from crewai.tools import tool

from sentence_transformers import SentenceTransformer

# -------------------------------
# GLOBALS
# -------------------------------
EMBED_MODEL = SentenceTransformer("intfloat/e5-base-v2")

# Base paths
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

PROFILE_PATH = KNOWLEDGE_DIR / "profile.json"
TIMELINE_PATH = KNOWLEDGE_DIR / "timeline.json"
EMBED_INDEX_PATH = KNOWLEDGE_DIR / "embeddings.json"
NOTES_DIR = KNOWLEDGE_DIR / "notes"

# Ensure dirs exist
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------
# 🔥 NEW: Embed text with e5 instruction style formatting
# -------------------------------------------------------
def embed_text(text: str) -> List[float]:
    prompt = f"passage: {text}"
    vec = EMBED_MODEL.encode(prompt, convert_to_numpy=True)
    return vec.tolist()


# -------------------------------------------------------
# 🔥 NEW: Save note text to markdown file
# -------------------------------------------------------
def save_note_markdown(topic: str, text: str) -> str:
    safe_name = topic.replace(" ", "_").lower()
    file_path = NOTES_DIR / f"{safe_name}.md"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n{text}\n")

    return str(file_path)


# -------------------------------------------------------
# 🔥 NEW: Update embedding index for topic
# -------------------------------------------------------
def update_embedding(topic: str, text: str):
    vec = embed_text(text)

    if EMBED_INDEX_PATH.exists():
        with open(EMBED_INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {}

    index[topic] = vec

    with open(EMBED_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return vec


# -------------------------------------------------------
# 🔥 NEW TOOL: Retrieve top-K relevant topics
# -------------------------------------------------------
@tool
def kb_retrieve(query: str, k: int = 5) -> Dict[str, Any]:
    """
    Retrieves the top-K most relevant topics from the hybrid knowledge base.
    Uses embedding similarity over stored topic notes.
    """

    if not EMBED_INDEX_PATH.exists():
        return {
            "status": "error",
            "message": "No embedding index found.",
            "results": []
        }

    # Load index
    with open(EMBED_INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    # Embed query
    query_vec = np.array(embed_text(query))

    # Compute cosine similarities
    results = []
    for topic, vec in index.items():
        vec = np.array(vec)
        sim = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
        results.append({"topic": topic, "similarity": float(sim)})

    # Sort + pick top-K
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)[:k]

    return {
        "status": "success",
        "query": query,
        "results": results
    }


# -------------------------------------------------------
# ORIGINAL UPDATE TOOL (expanded to integrate embeddings)
# -------------------------------------------------------
@tool
def kb_update(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates the user's knowledge profile (mastery, confidence, notes)
    AND writes full notes to markdown + updates embedding index.
    """

    if not isinstance(updates, dict):
        return {"status": "error", "message": "Updates must be a dictionary"}

    topic = updates.get("topic")
    if not topic:
        return {"status": "error", "message": "Missing 'topic' field"}

    # Load or create profile
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
        except Exception:
            profile_data = {"topics": {}}
    else:
        profile_data = {"topics": {}}

    if "topics" not in profile_data:
        profile_data["topics"] = {}

    # Get or create topic entry
    entry = profile_data["topics"].get(topic, {})
    changes = []

    # Update mastery
    if "mastery" in updates:
        new = float(updates["mastery"])
        new = max(0, min(10, new))
        old = entry.get("mastery")
        if old != new:
            entry["mastery"] = new
            changes.append(("mastery", old, new))

    # Update confidence
    if "confidence" in updates:
        new = float(updates["confidence"])
        new = max(0, min(10, new))
        old = entry.get("confidence")
        if old != new:
            entry["confidence"] = new
            changes.append(("confidence", old, new))

    # Update notes (also triggers markdown & embedding updates)
    if "notes" in updates:
        new = updates["notes"]
        if isinstance(new, str):
            old = entry.get("notes")
            if old != new:
                entry["notes"] = new
                changes.append(("notes", old, new))

                # SAVE MARKDOWN
                md_path = save_note_markdown(topic, new)
                entry["note_file"] = md_path

                # UPDATE EMBEDDING
                update_embedding(topic, new)

    # Update last reviewed
    if changes:
        entry["last_reviewed"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Save profile
    profile_data["topics"][topic] = entry
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)

    # Timeline logging
    if changes:
        if TIMELINE_PATH.exists():
            try:
                with open(TIMELINE_PATH, "r", encoding="utf-8") as f:
                    timeline = json.load(f)
                if not isinstance(timeline, list):
                    timeline = []
            except:
                timeline = []
        else:
            timeline = []

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        reason = updates.get("reason", "Knowledge profile updated")
        source = updates.get("source", "agent")

        for (field, old, new) in changes:
            timeline.append({
                "timestamp": timestamp,
                "event": "knowledge_update",
                "topic": topic,
                "field": field,
                "old_value": old,
                "new_value": new,
                "reason": reason,
                "source": source
            })

        with open(TIMELINE_PATH, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=2)

    # Summary
    if changes:
        updated_fields = ", ".join([c[0] for c in changes])
        msg = f"Updated {topic}: {updated_fields}"
    else:
        msg = f"No changes to {topic}"

    return {
        "status": "success",
        "message": msg,
        "updated_topic": topic
    }
