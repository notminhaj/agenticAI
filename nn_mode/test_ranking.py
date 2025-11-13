"""
Test script to verify the ranking functionality works with fetch().
"""
from tools import search, fetch, rank_documents
from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json
import inspect

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


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

# Test the workflow
if __name__ == "__main__":
    query = "Agentic AI"
    
    print("=" * 60)
    print("Step 1: Searching for papers...")
    papers = search(query, limit=3)
    
    print("\n" + "=" * 60)
    print("Step 2: Fetching content from papers...")
    fetched = []
    for paper in papers:
        print(f"Fetching: {paper['title'][:50]}...")
        doc = fetch(paper['url'])
        doc['title'] = paper['title']  # Preserve original title
        doc['id'] = paper.get('id', '')
        fetched.append(doc)
    
    print("\n" + "=" * 60)
    print("Step 3: Ranking documents by relevance...")
    ranked = rank_documents(query, fetched)
    
    print("\n" + "=" * 60)
    print("Results (sorted by relevance):")
    print("=" * 60)
    for i, doc in enumerate(ranked, 1):
        score = doc.get('score', 'N/A')
        title = doc.get('title', 'No title')[:60]
        print(f"{i}. Score: {score:.4f} | {title}")
    
    print("\n" + "=" * 60)
    print("Step 4: Summarizing top papers...")
    summaries = []
    for doc in ranked[:3]:  # Summarize top 3 papers
        if doc.get('kind') != 'error' and doc.get('raw_text'):
            print(f"Summarizing: {doc['title'][:50]}...")
            summary_result = summarize(doc['raw_text'], doc['title'])
            summary_result['url'] = doc.get('url', '')
            summary_result['score'] = doc.get('score', 0)
            summaries.append(summary_result)
    
    print("\n" + "=" * 60)
    print("Step 5: Saving results...")
    persist(summaries)
    
    print("\n" + "=" * 60)
    print("Workflow complete!")

