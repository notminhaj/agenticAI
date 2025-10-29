"""
I/O utilities for fetching and persisting paper content.

This module handles:
1. Fetching web content from URLs (HTML parsing, PDF detection)
2. Cleaning and extracting text from web pages
3. Saving summarized results to markdown and JSONL formats

Features:
- BeautifulSoup for HTML parsing and text extraction
- Automatic PDF-to-abstract page redirection
- Text cleaning and whitespace normalization
- Dual format output (human-readable markdown + machine-readable JSONL)
"""

# Import required libraries
import requests           # For HTTP requests to fetch web content
from bs4 import BeautifulSoup  # HTML parsing and text extraction
import re                # Regular expressions for text processing
from pathlib import Path         # Path manipulation utilities
from dotenv import load_dotenv   # Environment variable loading
from datetime import datetime    # Date/time formatting for filenames
import json             # JSON serialization for data export
import os               # File system operations

# Load .env file from parent directory (project root)
# This allows access to environment variables like API keys
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

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


def persist(results: list, folder: str = "."):
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
        folder (str): Directory to save files in. Default: current directory "."
        
    Returns:
        None (files are written to disk)
        
    Note:
        The timestamp is generated using the current date (YYYY-MM-DD format).
        Files are overwritten if they already exist for the same date.
    """
    # ================================================
    # Step 1: Generate timestamp for filename
    # ================================================
    # Create date string in YYYY-MM-DD format
    # Example: "2025-10-29"
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # ================================================
    # Step 2: Create output directory if needed
    # ================================================
    # os.makedirs creates the directory structure if it doesn't exist
    # exist_ok=True prevents error if directory already exists
    os.makedirs(folder, exist_ok=True)
    
    # ================================================
    # Step 3: Write markdown report
    # ================================================
    # Construct filename with timestamp
    md_path = os.path.join(folder, f"report_{timestamp}.md")
    
    # Open file in write mode with UTF-8 encoding (supports international characters)
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
    
    # ================================================
    # Step 4: Write JSONL data file
    # ================================================
    # JSONL (JSON Lines) format: one JSON object per line
    # This format is common in data science and ML pipelines
    jsonl_path = os.path.join(folder, f"runs_{timestamp}.jsonl")
    
    # Open file in write mode with UTF-8 encoding
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in results:
            # Write each result as a separate line of JSON
            # ensure_ascii=False allows UTF-8 characters to be written as-is
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    # ================================================
    # Step 5: Print confirmation
    # ================================================
    print(f"Saved report: {md_path}")
    print(f"Saved raw data: {jsonl_path}")