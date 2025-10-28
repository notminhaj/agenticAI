# search.py
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Set to False to use mock data for offline testing
USE_REAL_SEARCH = True  # Change to False to use mock data

def search(topic: str = "machine learning", limit: int = 5):
    """
    Real search using arXiv API directly (free and reliable).
    Returns list of paper-like links.
    
    Args:
        topic: Search query (default: "machine learning")
        limit: Maximum number of results (default: 5)
    
    Set USE_REAL_SEARCH = False to use mock data for testing.
    """
    # Mock mode for offline testing
    if not USE_REAL_SEARCH:
        return [
            {
                "title": "LLM Fine-Tuning with LoRA: A Survey",
                "url": "https://arxiv.org/abs/2405.12345",
                "source": "mock"
            },
            {
                "title": "Scaling Laws for Vision-Language Models",
                "url": "https://arxiv.org/abs/2406.67890",
                "source": "mock"
            },
            {
                "title": "Agentic AI: From Tools to Autonomous Systems",
                "url": "https://arxiv.org/abs/2407.11111",
                "source": "mock"
            }
        ]
    
    try:
        # Use arXiv API directly - it's free and reliable!
        arxiv_url = "http://export.arxiv.org/api/query"
        
        params = {
            "search_query": f"all:{topic}",
            "start": 0,
            "max_results": limit
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; workflow-bot)'
        }
        
        print(f"Searching arXiv for: {topic}")
        response = requests.get(arxiv_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        
        # Namespace for arXiv XML
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        results = []
        for entry in root.findall('atom:entry', ns):
            # Extract paper information
            title = entry.find('atom:title', ns).text.strip()
            paper_id = entry.find('atom:id', ns).text.split('/')[-1]
            url = f"https://arxiv.org/abs/{paper_id}"
            
            # Try to get abstract
            abstract = entry.find('atom:summary', ns)
            abstract_text = abstract.text.strip() if abstract is not None else "No abstract available"
            
            results.append({
                "title": title,
                "url": url,
                "source": "arxiv",
                "id": paper_id
            })
        
        if results:
            print(f"[OK] Found {len(results)} papers from arXiv")
            return results
        else:
            return [{"title": "No arXiv results found", "url": "", "source": "arxiv"}]
            
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] arXiv API error: {error_msg}")
        return [{"title": "Search Error", "url": "", "source": "error", "error": error_msg}]


if __name__ == "__main__":
    # Test the function
    print("Testing search() function...\n")
    results = search("neural networks deep learning")
    print(f"\n" + "="*70)
    print(f"Found {len(results)} results:")
    print("="*70 + "\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        if result.get('url'):
            print(f"   URL: {result['url']}")
        print(f"   Source: {result['source']}")
        if 'id' in result:
            print(f"   ID: {result['id']}")
        if 'error' in result:
            print(f"   ERROR: {result['error']}")
        print()