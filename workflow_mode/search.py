"""
arXiv API search module.

This module provides functions to search for academic papers on arXiv.
It uses the official arXiv API which is free, reliable, and doesn't require authentication.

Features:
- Real-time paper search via arXiv API
- Mock mode for offline testing
- XML parsing to extract paper metadata
- Error handling and graceful degradation
"""

# Import required libraries
import requests                           # For making HTTP requests to arXiv API
import json                               # JSON handling (though this file primarily uses XML)
import xml.etree.ElementTree as ET        # For parsing arXiv's XML response format
from datetime import datetime, timedelta  # Date utilities (currently not used but available for future features)

# Configuration flag for switching between real and mock search
# Set to False to use hardcoded test data when offline or testing
USE_REAL_SEARCH = False  # Change to False to use mock data

def search(topic: str = "Agentic AI", limit: int = 5):
    """
    Search arXiv for academic papers.
    
    Uses the arXiv API to find papers matching the given topic. Returns a list
    of paper dictionaries with title, URL, source, and paper ID.
    
    Args:
        topic (str): Search query keywords. Default: "Agentic AI"
        limit (int): Maximum number of results to return. Default: 5
        
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
    # ================================================
    # MOCK MODE: Return hardcoded test data
    # ================================================
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
    
    # ================================================
    # REAL MODE: Query arXiv API
    # ================================================
    try:
        # arXiv's export API endpoint - free, public, no auth required
        arxiv_url = "http://export.arxiv.org/api/query"
        
        # Build query parameters
        # "all:" prefix searches in all fields (title, abstract, full text)
        params = {
            "search_query": f"all:{topic}",  # Search all fields for the topic
            "start": 0,                       # Start from first result (offset for pagination)
            "max_results": limit              # Maximum number of results to return
        }
        
        # Set User-Agent header to identify our bot (courtesy to arXiv servers)
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; workflow-bot)'
        }
        
        # Log what we're searching for
        print(f"Searching arXiv for: {topic}")
        
        # Make the API request with 10 second timeout
        response = requests.get(arxiv_url, params=params, headers=headers, timeout=10)
        
        # Raise an exception if HTTP status code indicates an error
        response.raise_for_status()
        
        # ================================================
        # Parse XML response from arXiv
        # ================================================
        # arXiv returns data in XML/Atom format
        root = ET.fromstring(response.content)
        
        # Define the Atom namespace used by arXiv XML
        # This is needed to properly extract elements from the XML tree
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        results = []
        
        # Iterate through each paper entry in the XML
        for entry in root.findall('atom:entry', ns):
            # Extract title: remove whitespace and formatting
            title = entry.find('atom:title', ns).text.strip()
            
            # Extract arXiv paper ID from the URL
            # Example: "http://arxiv.org/abs/2405.12345" -> "2405.12345"
            paper_id = entry.find('atom:id', ns).text.split('/')[-1]
            
            # Construct the abstract page URL
            url = f"https://arxiv.org/abs/{paper_id}"
            
            # Try to extract abstract if available
            abstract = entry.find('atom:summary', ns)
            abstract_text = abstract.text.strip() if abstract is not None else "No abstract available"
            
            # Build result dictionary
            results.append({
                "title": title,      # Paper title
                "url": url,          # Link to paper's abstract page on arXiv
                "source": "arxiv",   # Indicates this came from arXiv API
                "id": paper_id       # arXiv paper ID (e.g., "2405.12345v1")
            })
        
        # ================================================
        # Return results or handle empty response
        # ================================================
        if results:
            print(f"[OK] Found {len(results)} papers from arXiv")
            return results
        else:
            # No results found - return an error indicator
            return [{"title": "No arXiv results found", "url": "", "source": "arxiv"}]
            
    except Exception as e:
        # Handle any errors (network issues, parsing errors, etc.)
        error_msg = str(e)
        print(f"[ERROR] arXiv API error: {error_msg}")
        
        # Return error indicator rather than crashing
        return [{"title": "Search Error", "url": "", "source": "error", "error": error_msg}]