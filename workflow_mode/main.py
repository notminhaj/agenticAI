"""
Main workflow orchestrator for the AI Paper Pipeline.

This script coordinates the entire pipeline:
1. Search for trending AI papers on arXiv
2. Fetch content from paper URLs
3. Summarize papers using OpenAI LLM
4. Save results to markdown and JSONL files

The pipeline processes papers to create weekly briefs for AI practitioners.
"""

# Import local modules
from search import search      # Search function for arXiv API
from io_utils import fetch, persist  # Fetch content from URLs and save results
from summarize import summarize      # Summarize paper content with LLM
import json                       # JSON handling for data serialization

def main():
    """
    Main pipeline orchestrator.
    
    Workflow:
    1. Search arXiv for papers
    2. Fetch and filter paper content
    3. Summarize papers with AI
    4. Save results to files
    """
    print("Starting AI Paper Pipeline...\n")
    
    # ========================================
    # STEP 1: Search for trending AI papers
    # ========================================
    print("1. Searching for papers...")
    
    # Query arXiv API for trending AI papers from 2025
    # The search function returns a list of candidate papers with title, URL, and metadata
    candidates = search(topic="trending AI papers 2025 site:arxiv.org/abs/")
    
    # Validate that we got results (not empty and not an error response)
    if not candidates or "error" in candidates[0]:
        print("No results found. Check internet or search.py")
        return
    
    print(f"   Found {len(candidates)} candidates\n")
    
    # ========================================
    # STEP 2: Fetch and filter paper content
    # ========================================
    print("2. Fetching content...")
    docs = []  # Will store successfully fetched documents
    
    # Iterate through each candidate paper
    for c in candidates:
        print(f"   → {c['title'][:160]}...")  # Print first 160 chars of title
        
        # Fetch the paper content from the URL
        # This downloads HTML, extracts text, and gets metadata
        doc = fetch(c["url"])
        
        # Skip if fetch failed (network error, 404, etc.)
        if doc.get("kind") == "error":
            print(f"      Failed: {doc.get('error', 'Unknown')}")
            continue
        
        # Filter out documents that are too short
        # This eliminates error pages, redirect pages, and non-paper content
        if len(doc["raw_text"]) < 600:
            print(f"      Skipped: too short ({len(doc['raw_text'])} chars)")
            continue
        
        # Document is valid, add it to our list
        docs.append(doc)
    
    print(f"   {len(docs)} valid documents\n")
    
    # ========================================
    # STEP 3: Summarize papers with LLM
    # ========================================
    print("3. Summarizing with LLM...")
    results = []  # Will store summarization results
    
    # Process each document and generate a summary
    for i, d in enumerate(docs, 1):
        print(f"   [{i}/{len(docs)}] {d['title'][:50]}...")
        
        # Generate summary using OpenAI API
        # The summary includes: Problem, Approach, Key Results, Why It Matters
        s = summarize(d["raw_text"], title_guess=d["title"])
        
        # Build the result object with all relevant information
        result = {
            "title": d["title"],                    # Paper title
            "url": d["url"],                        # Source URL
            "summary": s["summary"],                # LLM-generated summary
            "tokens_in": s["tokens_in"],            # Token usage for API call (input)
            "tokens_out": s["tokens_out"]           # Token usage for API call (output)
        }
        results.append(result)
    
    # ========================================
    # STEP 4: Save results to files
    # ========================================
    print(f"\n4. Saving report...")
    
    # Save results to both markdown (human-readable) and JSONL (machine-readable) formats
    persist(results)
    
    # Print success message with file locations
    print("\nDone! Check your folder for:")
    print("   • report_YYYY-MM-DD.md")    # Markdown report with formatted summaries
    print("   • runs_YYYY-MM-DD.jsonl")   # JSONL file with raw data (one line per result)

# Entry point: run main() when script is executed directly
if __name__ == "__main__":
    main()