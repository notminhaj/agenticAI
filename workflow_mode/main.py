# main.py
from search import search
from io_utils import fetch, persist
from summarize import summarize
import json

def main():
    print("Starting AI Paper Pipeline...\n")
    
    # 1. Search for trending AI papers
    print("1. Searching for papers...")
    candidates = search(topic="trending AI papers 2025 site:arxiv.org/abs/")
    
    if not candidates or "error" in candidates[0]:
        print("No results found. Check internet or search.py")
        return
    
    print(f"   Found {len(candidates)} candidates\n")
    
    # 2. Fetch content
    print("2. Fetching content...")
    docs = []
    for c in candidates:
        print(f"   → {c['title'][:160]}...")
        doc = fetch(c["url"])
        if doc.get("kind") == "error":
            print(f"      Failed: {doc.get('error', 'Unknown')}")
            continue
        if len(doc["raw_text"]) < 600:
            print(f"      Skipped: too short ({len(doc['raw_text'])} chars)")
            continue
        docs.append(doc)
    
    print(f"   {len(docs)} valid documents\n")
    
    # 3. Summarize (limit to 3)
    print("3. Summarizing with LLM...")
    results = []
    for i, d in enumerate(docs[:3], 1):
        print(f"   [{i}/3] {d['title'][:50]}...")
        s = summarize(d["raw_text"], title_guess=d["title"])
        result = {
            "title": d["title"],
            "url": d["url"],
            "summary": s["summary"],
            "tokens_in": s["tokens_in"],
            "tokens_out": s["tokens_out"]
        }
        results.append(result)
    
    # 4. Save
    print(f"\n4. Saving report...")
    persist(results)
    print("\nDone! Check your folder for:")
    print("   • report_YYYY-MM-DD.md")
    print("   • runs_YYYY-MM-DD.jsonl")

if __name__ == "__main__":
    main()