# io_utils.py
import requests
from bs4 import BeautifulSoup
import re

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