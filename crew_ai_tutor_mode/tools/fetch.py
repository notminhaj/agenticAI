import requests
import re
from bs4 import BeautifulSoup
from crewai.tools import tool

@tool
def fetch(url: str, timeout: int = 10) -> dict:
    """
    Fetch and extract text content from a web URL.
    
    Downloads HTML content from the given URL, extracts clean text,
    and returns metadata about the document. Handles PDF links by
    automatically redirecting to the abstract page.
    
    Args:
        url (str): URL of the page to fetch
        timeout (int): Request timeout in seconds. Default: 10
        
    Returns:
        dict: Document data containing:
            - title (str): Extracted or guessed title
            - url (str): Original URL
            - raw_text (str): Cleaned text content
            - kind (str): Document type ("html", "arxiv_abs", or "error")
            - error (str): Error message (only present if kind="error")
            
    Note:
        PDF URLs are automatically converted to abstract page URLs.
        Scripts, styles, and navigation elements are stripped from HTML.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; workflow-bot)'}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception as e:
        return {"title": "Error", "url": url, "raw_text": "", "kind": "error", "error": str(e)}
    if url.endswith('.pdf') or 'pdf' in response.headers.get('Content-Type', ''):
        abs_url = url.replace('/pdf/', '/abs/').replace('.pdf', '')
        return fetch(abs_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    raw_text = soup.get_text(separator=' ')
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()
    title_tag = soup.find('title')
    title = title_tag.get_text().strip() if title_tag else "No title"
    kind = "html"
    if 'arxiv.org/abs/' in url:
        kind = "arxiv_abs"
    return {"title": title.split('|')[0].strip(), "url": url, "raw_text": raw_text, "kind": kind}

