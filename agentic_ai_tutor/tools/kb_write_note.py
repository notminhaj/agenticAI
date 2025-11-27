import json
from pathlib import Path
from datetime import datetime, timezone
from crewai.tools import tool
from sentence_transformers import SentenceTransformer
import numpy as np
import re

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

@tool
def kb_write_note(topic: str,
                  note: str,
                  mode: str = "append"):
    """
    Writes human-readable notes to a topic's markdown file AND updates embeddings.
    You MUST consider using this tool after presenting any piece of information to the user.
    Use this ESPECIALLY when you detect learning, correct a misconception,
    provide the user with any information, or the user tells you something new.

    Args:
        topic (str): Topic name.
        note (str): Content to write.
        mode (str): "append" or "replace".

    Returns:
        dict: Status + updated embedding information
    """

    base_dir = Path(__file__).parent.parent
    knowledge_dir = base_dir / "knowledge_base" / "notes"
    md_path = knowledge_dir / f"{slugify(topic)}.md"
    print(knowledge_dir)
    print(md_path)
    embeddings_path = base_dir / "knowledge_base" / "embeddings" / "kb_index.json"

    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Write or append markdown file
    if mode == "replace" or not md_path.exists():
        md_path.write_text(f"# {topic}\n\n{note}\n", encoding="utf-8")
    else:
        with open(md_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + note + "\n")

    # Load embedding index
    if embeddings_path.exists():
        try:
            index = json.loads(embeddings_path.read_text(encoding="utf-8"))
        except:
            index = {}
    else:
        index = {}

    # Generate embedding
    model = SentenceTransformer("intfloat/e5-base-v2")
    vec = model.encode([md_path.read_text(encoding="utf-8")])[0]
    index[topic] = vec.tolist()

    embeddings_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "slugified-topic": slugify(topic),
        "message": "Note written and embeddings updated.",
        "embedding_dim": len(vec)
    }
