import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import load_dotenv
from crewai.tools import tool

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

USE_REAL_SEARCH = True

@tool
def search(topic: str, limit: int):
    """
    Search arXiv for academic papers.
    
    Uses the arXiv API to find papers matching the given topic. Returns a list
    of paper dictionaries with title, URL, source, and paper ID.
    
    Args:
        topic (str): Search query keywords.
        limit (int): Maximum number of results to return.
        
    Returns:
        list: List of dictionaries, each containing:
            - title (str): Paper title
            - url (str): Link to paper abstract page
            - source (str): "arxiv" for real searches, "mock" for test data
            - id (str): arXiv paper ID (e.g., "2405.12345")
            
    Note:
        Set USE_REAL_SEARCH = False to use mock data for testing without internet.
        The arXiv API is free and public - no API key required!
    """
    if not USE_REAL_SEARCH:
        return [
            {"title": "LLM Fine-Tuning with LoRA: A Survey", "url": "https://arxiv.org/abs/2405.12345", "source": "mock"},
            {"title": "Scaling Laws for Vision-Language Models", "url": "https://arxiv.org/abs/2406.67890", "source": "mock"},
            {"title": "Agentic AI: From Tools to Autonomous Systems", "url": "https://arxiv.org/abs/2407.11111", "source": "mock"}
        ]
    try:
        arxiv_url = "http://export.arxiv.org/api/query"
        params = {"search_query": f"all:{topic}", "start": 0, "max_results": limit}
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; workflow-bot)'}
        print(f"Searching arXiv for: {topic}")
        response = requests.get(arxiv_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip()
            paper_id = entry.find('atom:id', ns).text.split('/')[-1]
            url = f"https://arxiv.org/abs/{paper_id}"
            results.append({"title": title, "url": url, "source": "arxiv", "id": paper_id})
        if results:
            print(f"[OK] Found {len(results)} papers from arXiv")
            return results
        else:
            return [{"title": "No arXiv results found", "url": "", "source": "arxiv"}]
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] arXiv API error: {error_msg}")
        return [{"title": "Search Error", "url": "", "source": "error", "error": error_msg}]

