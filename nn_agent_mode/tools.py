import requests
import xml.etree.ElementTree as ET
import os
import json
import re
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from crewai.tools import tool
from typing import Optional
from prompts import role, goal, backstory, description


env_path = Path(__file__).parent.parent / '.env'
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

@tool
def summarize(raw_text: str, title_guess: str = "Untitled") -> dict:
    """
    Generate an AI-powered summary of an academic paper.
    
    Uses OpenAI's GPT-4.1-mini model to create a structured, concise summary.
    The summary follows a specific template with sections for Problem, Approach, Results, and Significance.
    
    Args:
        raw_text (str): Full text content of the paper to summarize.
        title_guess (str): Estimated or extracted title of the paper.
        
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    client = OpenAI(api_key=api_key)
    prompt = (
        f"Your role is {role}" +
        f"Your goal is {goal}" +
        f"Your backstory is {backstory}" +
        f"Your task is {description}"
        f"Use EXACTLY this structure with these exact headers:\\n\\n" +
        f"**Problem:** [description]\\n" +
        f"**Approach:** [description]\\n" +
        f"**Key Results:** [description]\\n" +
        f"**Why It Matters:** [description]\\n\\n" +
        f"Keep each section to 30-50 words. Total 120180 words.\\n\\n" +
        f"Title: {title_guess}\\n\\n{raw_text[:6000]}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        summary = response.choices[0].message.content.strip()
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens
        return {"title": title_guess, "summary": summary, "tokens_in": tokens_in, "tokens_out": tokens_out}
    except Exception as e:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            summary = response.choices[0].message.content.strip()
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            return {"title": title_guess, "summary": summary, "tokens_in": tokens_in, "tokens_out": tokens_out}
        except:
            return {"title": title_guess, "summary": "Error summarizing: " + str(e), "tokens_in": 0, "tokens_out": 0}

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
    raw_text = re.sub(r'\\s+', ' ', raw_text).strip()
    title_tag = soup.find('title')
    title = title_tag.get_text().strip() if title_tag else "No title"
    kind = "html"
    if 'arxiv.org/abs/' in url:
        kind = "arxiv_abs"
    return {"title": title.split('|')[0].strip(), "url": url, "raw_text": raw_text, "kind": kind}

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
        folder = str(Path(__file__).parent)
    
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

@tool
def rank_documents(query: str, documents: list, text_key: str = "raw_text") -> list:
    """
    This is a special tool that can rank documents based on relevance to topic.
    This enables you to search for more articles and fetch extra content so that you can present higher quality summaries.

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
