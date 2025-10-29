# io_utils.py
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json
import os

# Load .env file from parent directory (project root)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def fetch(url: str, timeout: int = 10) -> dict:
    """
    Fetch content from URL.
    - If PDF → go to /abs/ page
    - Return cleaned text + metadata
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; workflow-bot)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception as e:
        return {
            "title": "Error",
            "url": url,
            "raw_text": "",
            "kind": "error",
            "error": str(e)
        }

    # --- PDF → redirect to abstract ---
    if url.endswith('.pdf') or 'pdf' in response.headers.get('Content-Type', ''):
        abs_url = url.replace('/pdf/', '/abs/').replace('.pdf', '')
        return fetch(abs_url)  # Recursive call

    # --- It's HTML ---
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove scripts, styles, nav, footer
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    
    raw_text = soup.get_text(separator=' ')
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()

    # Heuristic: guess title
    title_tag = soup.find('title')
    title = title_tag.get_text().strip() if title_tag else "No title"

    kind = "html"
    if 'arxiv.org/abs/' in url:
        kind = "arxiv_abs"

    return {
        "title": title.split('|')[0].strip(),
        "url": url,
        "raw_text": raw_text,
        "kind": kind
    }


def persist(results: list, folder: str = "."):
    """
    Save summaries to markdown + JSONL.
    """
    # 1. Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # 2. Ensure folder exists
    os.makedirs(folder, exist_ok=True)
    
    # 3. Markdown report
    md_path = os.path.join(folder, f"report_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Weekly AI Paper Brief – {timestamp}\n\n")
        for i, r in enumerate(results, 1):
            f.write(f"### {i}) {r['title']}\n")
            f.write(f"{r['url']}\n\n")
            f.write(f"**Summary:** {r['summary']}\n\n")
            f.write("---\n\n")
    
    # 4. JSONL (one line per result)
    jsonl_path = os.path.join(folder, f"runs_{timestamp}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    print(f"Saved report: {md_path}")
    print(f"Saved raw data: {jsonl_path}")