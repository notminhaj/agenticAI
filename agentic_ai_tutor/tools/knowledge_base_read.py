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
TIMELINE_PATH = ROOT / "knowledge_base" / "timeline.json"

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
def knowledge_base_read(query: str = "", top_k: int = 5) -> Dict[str, Any]:
    """
    Unified tool for reading from the user's knowledge base.
    
    CRITICAL INSTRUCTION FOR AGENT:
    Your primary goal is to cater responses to the user's level of understanding. 
    Use this tool to search for what the user already knows about a topic BEFORE answering.
    If the user asks about any topic, e.g. "Software Development, Biology, Physics", check if they already know the basics so you don't bore them.
    
    Args:
        query (str, optional): Search query to find relevant notes (e.g., "agentic AI", "python basics"). 
                               Defaults to "" (no search).
        top_k (int, optional): Number of search results to return. Default 5.
        
    Returns:
        dict: A dictionary containing:
            - "profile": The user's entire knowledge profile (topics, mastery levels) and recent events.
            - "search_results": A list of relevant notes matching your query (if query provided).
    """
    
    results = {}
    
    # Always read profile
    results["profile"] = _read_profile()
    
    # Search notes if query provided
    if query:
        results["search_results"] = _search_notes(query, top_k)
        
    return results

def _read_profile() -> Dict[str, Any]:
    """
    Reads the profile from kb_index.json and transforms it into the expected dictionary format.
    """
    profile_data = {"topics": {}}
    timeline_data = []
    status = "success"
    messages = []
    
    # Load kb_index.json (acting as profile)
    if not INDEX_PATH.exists():
        messages.append(f"KB Index file not found: {INDEX_PATH}")
        status = "partial" if status == "success" else "error"
    else:
        try:
            with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                kb_index = json.load(f)
                
            if isinstance(kb_index, list):
                for record in kb_index:
                    title = record.get("title")
                    if title:
                        profile_data["topics"][title] = {
                            "mastery": record.get("mastery", 0.0),
                            "confidence": record.get("confidence", 0.0),
                            "last_reviewed": record.get("last_reviewed"),
                            "note_path": record.get("note_path")
                        }
            else:
                 messages.append("KB Index is not a list")
                 status = "error"

        except json.JSONDecodeError as e:
            messages.append(f"KB Index JSON is malformed: {str(e)}")
            status = "error"
        except Exception as e:
            messages.append(f"Error reading KB Index: {str(e)}")
            status = "error"
    
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
        return [{"error": f"KB Index not found at {INDEX_PATH}. Run build_kb_index.py first."}]

    client = get_client()

    # embed query
    try:
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        q_emb = resp.data[0].embedding
    except Exception as e:
        return [{"error": f"Embedding generation failed: {str(e)}"}]

    # load index
    try:
        with INDEX_PATH.open("r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        return [{"error": f"Failed to load index: {str(e)}"}]

    scored = []
    for rec in records:
        # Skip records with no embedding
        if not rec.get("embedding"):
            continue
            
        score = cosine_sim(q_emb, rec["embedding"])

        note_path = rec.get("note_path", "")
        if note_path:
            note_file = ROOT / note_path
            try:
                if note_file.is_file():
                    text = note_file.read_text(encoding="utf-8")
                else:
                    text = ""
            except Exception:
                text = ""
        else:
            text = ""
            
        # Return full content as 'content' instead of just preview, since we removed note_path reading
        # But wait, user said "use embeddings to find most relevant notes".
        # I'll stick to returning a generous preview or full content?
        # Let's return full content in 'content' field so the agent can actually read it.
        content = text 

        scored.append({
            "title": rec.get("title", "Untitled"),
            "note_path": note_path,
            "score": score,
            "content": content, # Changed from preview to content
            "mastery": rec.get("mastery"),
            "confidence": rec.get("confidence")
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
