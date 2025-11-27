from crewai.tools import tool

@tool
def read_note(note_path: str) -> str:
    """
    Read the full content of a markdown note from the knowledge base.
    Args:
        note_path (str): Relative path, as returned by semantic_note_search.
    """
    path = ROOT / note_path
    if not path.exists():
        return f"Note not found: {note_path}"
    return path.read_text(encoding="utf-8")
