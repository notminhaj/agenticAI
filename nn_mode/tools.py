# Import required libraries
import requests                           # For making HTTP requests to arXiv API
import json                               # JSON handling (though this file primarily uses XML)
import xml.etree.ElementTree as ET        # For parsing arXiv's XML response format
from datetime import datetime, timedelta  # Date utilities (currently not used but available for future features)
from bs4 import BeautifulSoup             # HTML parsing and text extraction
import re                                 # Regular expressions for text processing


def search(topic: str, limit: int):
    """
    Search arXiv for academic papers.
    
    Uses the arXiv API to find papers matching the given topic. Returns a list
    of paper dictionaries with title, URL, source, and paper ID.
    
    Args:
        topic (str): Search query keywords.
        limit (int): Maximum number of results to return, but times 2 for extra searches
        
    Returns:
        list: List of dictionaries, each containing:
            - title (str): Paper title
            - url (str): Link to paper abstract page
            - source (str): "arxiv" for real searches, "mock" for test data
            - id (str): arXiv paper ID (e.g., "2405.12345")
            
    Note:
        The arXiv API is free and public - no API key required!
    """
    
    try:
        # arXiv's export API endpoint - free, public, no auth required
        arxiv_url = "http://export.arxiv.org/api/query"
        
        # Build query parameters
        # "all:" prefix searches in all fields (title, abstract, full text)
        params = {
            "search_query": f"all:{topic}",  # Search all fields for the topic
            "start": 0,                       # Start from first result (offset for pagination)
            "max_results": limit * 2            # Maximum number of results to return, times 2
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
    # Set User-Agent header to identify our bot
    # This helps servers handle our requests appropriately
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; workflow-bot)'}
    
    # ================================================
    # Step 1: Fetch the URL with error handling
    # ================================================
    try:
        # Make GET request with timeout to prevent hanging
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # Raise exception if HTTP status code indicates error (4xx, 5xx)
        response.raise_for_status()
    except Exception as e:
        # Return error dictionary if fetch fails
        # This allows the pipeline to continue processing other papers
        return {
            "title": "Error",
            "url": url,
            "raw_text": "",
            "kind": "error",
            "error": str(e)
        }

    # ================================================
    # Step 2: Handle PDF links (redirect to abstract page)
    # ================================================
    # arXiv papers can be accessed via PDF or abstract page
    # We prefer abstract pages as they have more metadata
    if url.endswith('.pdf') or 'pdf' in response.headers.get('Content-Type', ''):
        # Convert PDF URL to abstract page URL
        # Example: https://arxiv.org/pdf/2405.12345.pdf -> https://arxiv.org/abs/2405.12345
        abs_url = url.replace('/pdf/', '/abs/').replace('.pdf', '')
        
        # Recursively call fetch with the abstract page URL
        # This ensures we get HTML content, not PDF binary data
        return fetch(abs_url)

    # ================================================
    # Step 3: Parse HTML content
    # ================================================
    # Parse the HTML with BeautifulSoup
    # 'html.parser' is a built-in parser (no external dependencies)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove non-content elements to get clean text
    # Scripts contain JavaScript (not useful for summarization)
    # Styles contain CSS (not useful for summarization)
    # Nav, footer, header contain navigation/metadata (not paper content)
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()  # Remove the tag from the DOM tree
    
    # Extract all text content, joining with spaces
    raw_text = soup.get_text(separator=' ')
    
    # Normalize whitespace using regex
    # Replace multiple spaces/tabs/newlines with single space
    # This makes the text cleaner and more concise
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()

    # ================================================
    # Step 4: Extract title
    # ================================================
    # Try to find the <title> tag in the HTML
    title_tag = soup.find('title')
    
    # Extract title text if found, otherwise use placeholder
    title = title_tag.get_text().strip() if title_tag else "No title"

    # ================================================
    # Step 5: Determine document type
    # ================================================
    kind = "html"  # Default to generic HTML
    
    # Check if this is an arXiv abstract page
    if 'arxiv.org/abs/' in url:
        kind = "arxiv_abs"  # Special handling for arXiv papers

    # ================================================
    # Step 6: Return cleaned document data
    # ================================================
    return {
        "title": title.split('|')[0].strip(),  # Remove site name suffix (e.g., "| arXiv.org")
        "url": url,                              # Original URL
        "raw_text": raw_text,                    # Cleaned text content
        "kind": kind                            # Document type identifier
    }


def rank_documents(query: str, documents: list, text_key: str = "raw_text") -> list:
    """
    Rank a list of fetched documents by their relevance to a query using neural embeddings.
    
    This function takes documents returned by fetch() and ranks them using the E5 embedding model.
    Documents are sorted by relevance score (highest first).
    
    Args:
        query (str): The search query to rank documents against
        documents (list): List of document dictionaries (from fetch() or similar)
                         Each dict should contain at least the text_key field
        text_key (str): Key in document dict that contains the text to rank. Default: "raw_text"
        
    Returns:
        list: List of document dictionaries with added "score" field, sorted by score (highest first)
              Each document dict will have:
              - All original fields from input
              - "score" (float): Relevance score (0-1, higher = more relevant)
              
    Example:
        papers = search("Agentic AI", limit=5)
        fetched = [fetch(paper["url"]) for paper in papers]
        ranked = rank_documents("Agentic AI", fetched)
        # ranked[0] is the most relevant paper
    """
    # Import rank_passages - works from both parent directory and nn_mode directory
    try:
        from .nn import rank_passages
    except ImportError:
        from nn import rank_passages
    
    # Extract text passages from documents
    passages = []
    valid_docs = []
    
    for doc in documents:
        # Skip error documents
        if doc.get("kind") == "error" or not doc.get(text_key):
            continue
        
        text = doc[text_key]
        # Truncate very long texts to avoid token limits (E5 max is 512 tokens)
        # Rough estimate: ~4 chars per token, so 512 tokens ≈ 2000 chars
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        passages.append(text)
        valid_docs.append(doc)
    
    if not passages:
        print("[WARNING] No valid documents to rank")
        return documents  # Return original if nothing to rank
    
    # Get relevance scores from neural network
    scores = rank_passages(query, passages)
    
    # Add scores to documents and sort by score
    for i, doc in enumerate(valid_docs):
        doc["score"] = scores[i]
    
    # Sort by score (highest first)
    ranked_docs = sorted(valid_docs, key=lambda x: x["score"], reverse=True)
    
    # Add unranked error documents at the end
    error_docs = [doc for doc in documents if doc.get("kind") == "error" or not doc.get(text_key)]
    ranked_docs.extend(error_docs)
    
    print(f"[OK] Ranked {len(ranked_docs)} documents by relevance to '{query}'")
    return ranked_docs