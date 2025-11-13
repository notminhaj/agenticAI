# Import required libraries
import requests                           # For making HTTP requests to arXiv API
import json                               # JSON handling (though this file primarily uses XML)
import xml.etree.ElementTree as ET        # For parsing arXiv's XML response format
from datetime import datetime, timedelta  # Date utilities (currently not used but available for future features)
from bs4 import BeautifulSoup             # HTML parsing and text extraction
import re                                 # Regular expressions for text processing
from openai import OpenAI                 # OpenAI Python SDK for LLM API calls
import os                                 # Environment variable access and file operations
from pathlib import Path                  # Path manipulation
from dotenv import load_dotenv            # Load .env file for configuration
import inspect                            # For detecting caller's file location

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


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
        if doc.get("kind") == "error":
            continue
        
        # Check if text exists and is not empty/whitespace
        text = doc.get(text_key, "")
        if not text or not text.strip():
            continue
        
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
    
    # Add unranked error documents at the end (with debug info)
    # Only include documents that weren't already processed
    processed_urls = {doc.get("url") for doc in valid_docs}
    error_docs = []
    for doc in documents:
        # Skip if already processed
        if doc.get("url") in processed_urls:
            continue
            
        # Check if this document should have been processed but wasn't
        text = doc.get(text_key, "")
        has_text = text and text.strip()
        
        if doc.get("kind") == "error":
            # Error documents get score of 0.0
            doc["score"] = 0.0
            doc["_debug"] = "Error fetching document"
            error_docs.append(doc)
        elif not has_text:
            # Document has no text - assign score of 0 and add debug info
            doc["score"] = 0.0
            doc["_debug"] = "No text content available for ranking"
            error_docs.append(doc)
    
    ranked_docs.extend(error_docs)
    
    if error_docs:
        print(f"[INFO] {len(error_docs)} documents could not be ranked (no text content or errors)")
    print(f"[OK] Ranked {len(ranked_docs)} documents by relevance to '{query}'")
    return ranked_docs


def summarize(raw_text: str, title_guess: str = "Untitled") -> dict:
    """
    Generate an AI-powered summary of an academic paper.
    
    Uses OpenAI's GPT-4o-mini model to create a structured, concise summary
    formatted for busy AI practitioners. The summary follows a specific template
    with sections for Problem, Approach, Results, and Significance.
    
    Args:
        raw_text (str): Full text content of the paper to summarize
        title_guess (str): Estimated or extracted title of the paper. Default: "Untitled"
        
    Returns:
        dict: Summary result containing:
            - title (str): Paper title
            - summary (str): LLM-generated structured summary in markdown format
            - tokens_in (int): Number of input tokens used (for cost tracking)
            - tokens_out (int): Number of output tokens used (for cost tracking)
            
    Raises:
        ValueError: If OPENAI_API_KEY is not found in environment variables
        
    Note:
        The function truncates input text to 6000 characters to manage token costs.
        It automatically retries once on API failures before giving up.
    """
    # Retrieve API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Validate that API key exists
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    
    # Initialize OpenAI client with the API key
    client = OpenAI(api_key=api_key)
    
    # Construct a detailed prompt that instructs the LLM on:
    # - Target audience (busy Junior AI Intern)
    # - Required structure (specific headers)
    # - Format requirements (markdown with bold headers)
    # - Length constraints (30-50 words per section, 120-180 total)
    prompt = (
        f"Summarize the following AI paper for a busy Junior AI Intern. "
        f"Use EXACTLY this structure with these exact headers:\n\n"
        f"**Problem:** [description]\n"        # What problem does the paper address?
        f"**Approach:** [description]\n"        # How did they solve it?
        f"**Key Results:** [description]\n"     # What did they find?
        f"**Why It Matters:** [description]\n\n"  # Why is this important?
        f"Keep each section to 30-50 words. Total 120–180 words.\n\n"
        f"Title: {title_guess}\n\n{raw_text[:6000]}"  # Truncate to 6000 chars for token efficiency
    )

    # Attempt 1: Primary API call
    try:
        # Make API request to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",              # Fast and cost-effective model
            messages=[{"role": "user", "content": prompt}],  # Single user message
            temperature=0.7,                  # Balance between creativity and consistency
            max_tokens=300                    # Limit output length to control costs
        )
        
        # Extract the summary text from the response
        summary = response.choices[0].message.content.strip()
        
        # Extract token usage for cost tracking and monitoring
        tokens_in = response.usage.prompt_tokens   # Tokens in the prompt (input)
        tokens_out = response.usage.completion_tokens  # Tokens in the completion (output)
        
        # Return the result dictionary
        return {
            "title": title_guess,
            "summary": summary,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out
        }
        
    except Exception as e:
        # Attempt 2: Retry on failure
        # Network issues and rate limits are common - retry once before giving up
        try:
            # Make the same request again
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            # Extract results
            summary = response.choices[0].message.content.strip()
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            
            # Return successful result
            return {
                "title": title_guess,
                "summary": summary,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out
            }
        except:
            # Final fallback: Return error message
            # Both attempts failed - return an error result rather than crashing
            return {
                "title": title_guess,
                "summary": "Error summarizing: " + str(e),
                "tokens_in": 0,
                "tokens_out": 0
            }


def persist(results: list, folder: str = None):
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
    # If no folder specified, use the directory of the calling script
    if folder is None:
        # Get the caller's frame to find where the script is running from
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        folder = str(Path(caller_file).parent)
    
    # Generate timestamp for filename (YYYY-MM-DD format)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # Create output directory if needed
    os.makedirs(folder, exist_ok=True)
    
    # Write markdown report
    md_path = os.path.join(folder, f"report_{timestamp}.md")
    
    with open(md_path, "w", encoding="utf-8") as f:
        # Write header
        f.write(f"# Weekly AI Paper Brief – {timestamp}\n\n")
        
        # Write each paper summary
        for i, r in enumerate(results, 1):
            # Paper header with index and title
            f.write(f"### {i}) {r['title']}\n")
            
            # URL link
            f.write(f"{r['url']}\n\n")
            
            # Summary content (already formatted by LLM)
            f.write(f"{r['summary']}\n\n")
            
            # Separator line
            f.write("---\n\n")
    
    # Write JSONL data file
    # JSONL (JSON Lines) format: one JSON object per line
    jsonl_path = os.path.join(folder, f"runs_{timestamp}.jsonl")
    
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in results:
            # Write each result as a separate line of JSON
            # ensure_ascii=False allows UTF-8 characters to be written as-is
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    # Print confirmation
    print(f"Saved report: {md_path}")
    print(f"Saved raw data: {jsonl_path}")