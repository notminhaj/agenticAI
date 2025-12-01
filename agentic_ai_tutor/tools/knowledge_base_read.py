import json
import math
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from openai import OpenAI
from crewai.tools import tool

# Constants
ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "knowledge_base" / "embeddings" / "kb_index.json"
PROFILE_PATH = ROOT / "knowledge" / "profile.json"
TIMELINE_PATH = ROOT / "knowledge" / "timeline.json"

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)

def cosine_sim(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

@tool
def knowledge_base_read(query: str = None, note_path: str = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Unified tool for reading from the user's knowledge base.
    
    Args:
        query (str, optional): Search query to find relevant notes.
        note_path (str, optional): Path to a specific note to read.
        top_k (int, optional): Number of search results to return. Default 5.
        
    Returns:
        dict: A dictionary containing results from the executed operations:
            - "profile": User's knowledge profile and recent events (always returned).
            - "search_results": List of relevant notes (if query provided).
            - "note_content": Content of the specified note (if note_path provided).
    """
    
    results = {}
    
    # Always read profile
    results["profile"] = _read_profile()
    
    # Search notes if query provided
    if query:
        results["search_results"] = _search_notes(query, top_k)
        
    # Read note if path provided
    if note_path:
        results["note_content"] = _read_note(note_path)
        
    return results

def _read_profile() -> Dict[str, Any]:
    profile_data = {}
    timeline_data = []
    status = "success"
    messages = []
    
    # Load profile.json
    if not PROFILE_PATH.exists():
        messages.append(f"Profile file not found: {PROFILE_PATH}")
        status = "partial" if status == "success" else "error"
        profile_data = {"updated_at": None, "topics": {}}
    else:
        try:
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        except json.JSONDecodeError as e:
            messages.append(f"Profile JSON is malformed: {str(e)}")
            status = "error"
            profile_data = {"updated_at": None, "topics": {}}
        except Exception as e:
            messages.append(f"Error reading profile: {str(e)}")
            status = "error"
            profile_data = {"updated_at": None, "topics": {}}
    
    # Load timeline.json
    if not TIMELINE_PATH.exists():
        messages.append(f"Timeline file not found: {TIMELINE_PATH}")
        status = "partial" if status == "success" else "error"
        timeline_data = []
    else:
        try:
            with open(TIMELINE_PATH, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
                
            # Ensure timeline_data is a list
            if not isinstance(timeline_data, list):
                messages.append("Timeline data is not a list, returning empty")
                timeline_data = []
            else:
                # Sort by timestamp (most recent first) and take last 10
                sorted_events = sorted(
                    timeline_data,
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )
                timeline_data = sorted_events[:10]
                
        except json.JSONDecodeError as e:
            messages.append(f"Timeline JSON is malformed: {str(e)}")
            status = "error"
            timeline_data = []
        except Exception as e:
            messages.append(f"Error reading timeline: {str(e)}")
            status = "error"
            timeline_data = []
    
    return {
        "profile": profile_data,
        "recent_events": timeline_data,
        "status": status,
        "message": "; ".join(messages) if messages else None
    }

def _search_notes(query: str, top_k: int) -> List[dict]:
    if not INDEX_PATH.exists():
        return [{"error": f"KB index not found at {INDEX_PATH}. Run build_kb_index.py first."}]

    client = get_client()

    # embed query
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    q_emb = resp.data[0].embedding

    # load index
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        records = json.load(f)

    scored = []
    for rec in records:
        score = cosine_sim(q_emb, rec["embedding"])

        note_file = ROOT / rec["note_path"]
        try:
            text = note_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            text = ""
        preview = text[:200].replace("\n", " ")

        scored.append({
            "title": rec["title"],
            "note_path": rec["note_path"],
            "score": score,
            "preview": preview
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]

def _read_note(note_path: str) -> str:
    path = ROOT / note_path
    if not path.exists():
        return f"Note not found: {note_path}"
    return path.read_text(encoding="utf-8")
