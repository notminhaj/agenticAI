import json
import math
import os
from pathlib import Path
from typing import List

from openai import OpenAI
from crewai.tools import tool

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "knowledge_base" / "embeddings" / "kb_index.json"

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
def semantic_note_search(query: str, top_k: int = 5) -> List[dict]:
    """
    Find the most relevant knowledge-base notes for a given query.

    Uses a precomputed embedding index over markdown note files and
    returns the top_k matching notes with similarity scores and previews.

    Args:
        query (str): Natural language query or topic description.
        top_k (int): Number of top notes to return. Default: 5.

    Returns:
        list of dicts, each with:
            - title (str)
            - note_path (str)
            - score (float)
            - preview (str): first 200 chars of the note

    Note:
        After using this tool, highly recommended you use the read_note tool for a better understanding of the user's knowledge.
    """
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


@tool
def read_note(note_path: str) -> str:
    """
    Read the full content of a markdown note from the knowledge base.
    Use this tool right after using the semantic_note_search tool
    Args:
        note_path (str): Relative path, as returned by semantic_note_search.
    """
    path = ROOT / note_path
    if not path.exists():
        return f"Note not found: {note_path}"
    return path.read_text(encoding="utf-8")
