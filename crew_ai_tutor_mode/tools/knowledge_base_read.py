import json
import math
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from crewai.tools import tool
from sentence_transformers import SentenceTransformer

# Constants
ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "knowledge_base" / "embeddings" / "kb_index.json"
METADATA_PATH = ROOT / "knowledge_base" / "kb_metadata.json"
TIMELINE_PATH = ROOT / "knowledge_base" / "timeline.json"

# Initialize model globally to avoid reloading on every call
try:
    MODEL = SentenceTransformer("intfloat/e5-base-v2")
except Exception as e:
    print(f"Error loading model: {e}")
    MODEL = None

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
    Reads the profile from kb_metadata.json and transforms it into the expected dictionary format.
    """
    profile_data = {"topics": {}}
    timeline_data = []
    status = "success"
    messages = []
    
    # Load kb_metadata.json
    if not METADATA_PATH.exists():
        messages.append(f"Metadata file not found: {METADATA_PATH}")
        status = "partial" if status == "success" else "error"
    else:
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        except json.JSONDecodeError as e:
            messages.append(f"Metadata JSON is malformed: {str(e)}")
            status = "error"
        except Exception as e:
            messages.append(f"Error reading Metadata: {str(e)}")
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

    if MODEL is None:
         return [{"error": "Embedding model not loaded."}]

    # embed query
    try:
        # e5 models expect "query: " prefix for queries
        q_emb = MODEL.encode(f"query: {query}").tolist()
    except Exception as e:
        return [{"error": f"Embedding generation failed: {str(e)}"}]

    # load index
    try:
        with INDEX_PATH.open("r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        return [{"error": f"Failed to load index: {str(e)}"}]

    # load metadata for enrichment
    metadata = {}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                meta_raw = json.load(f)
                metadata = meta_raw.get("topics", {})
        except:
            pass

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
            
        content = text 
        
        # Enrich with metadata
        title = rec.get("title", "Untitled")
        topic_meta = metadata.get(title, {})

        scored.append({
            "title": title,
            "note_path": note_path,
            "score": score,
            "content": content,
            "mastery": topic_meta.get("mastery", 0.0),
            "confidence": topic_meta.get("confidence", 0.0)
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
