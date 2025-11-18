import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from crewai.tools import tool

@tool
def persist(results: list, folder: Optional[str] = None):
    """
    Save summary results to both markdown and JSONL formats.
    
    Creates two output files:
    1. Markdown report (human-readable) - report_YYYY-MM-DD.md
    2. JSONL data (machine-readable) - runs_YYYY-MM-DD.jsonl
    
    The markdown file is formatted for easy reading by humans.
    The JSONL file contains one JSON object per line for programmatic processing.
    
    Args:
        results (list): List of summary dictionaries, each containing:
            - title (str): Paper title
            - url (str): Paper URL
            - summary (str): LLM-generated summary
            - tokens_in (int): Input tokens used
            - tokens_out (int): Output tokens used
        folder (str): Directory to save files in. Default: None (auto-detects script directory)
        
    Returns:
        None (files are written to disk)
        
    Note:
        The timestamp is generated using the current date (YYYY-MM-DD format).
        Files are overwritten if they already exist for the same date.
        If folder is None, files are saved in the same directory as the calling script.
    """
    # If no folder specified, use the directory where this tools.py file is located
    if folder is None:
        folder = str(Path(__file__).parent.parent)
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(folder, exist_ok=True)
    
    md_path = os.path.join(folder, f"report_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Weekly AI Paper Brief – {timestamp}\n\n")
        for i, r in enumerate(results, 1):
            f.write(f"### {i}) {r['title']}\n")
            f.write(f"{r['url']}\n\n")
            f.write(f"{r['summary']}\n\n")
            f.write("---\n\n")
    
    jsonl_path = os.path.join(folder, f"runs_{timestamp}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved report: {md_path}")
    print(f"Saved raw data: {jsonl_path}")

