"""
Test script to verify the ranking functionality works with fetch().
"""
from tools import search, fetch, rank_documents

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

