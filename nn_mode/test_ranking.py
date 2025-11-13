"""
Test script to verify the ranking functionality works with fetch().
"""
from tools import search, fetch, rank_documents, summarize, persist

# Test the workflow
if __name__ == "__main__":
    query = "Quantum Mechanics"
    limit = 6  # Number of papers to summarize (top N after ranking)
    
    print("=" * 60)
    print("Step 1: Searching for papers...")
    papers = search(query, limit=limit)
    
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
        # Format score - handle both numeric and string values
        # Note: 0.0 is a valid score, so we need to check if score exists, not if it's truthy
        if 'score' in doc and isinstance(score, (int, float)):
            score_str = f"{score:.4f}"
        else:
            score_str = str(score)
        print(f"{i}. Score: {score_str} | {title}")
    
    print("\n" + "=" * 60)
    print(f"Step 4: Summarizing top {limit} papers...")
    summaries = []
    count = 0
    for doc in ranked:
        if count >= limit:
            break
        if doc.get('kind') != 'error' and doc.get('raw_text'):
            print(f"Summarizing: {doc['title'][:50]}...")
            summary_result = summarize(doc['raw_text'], doc['title'])
            summary_result['url'] = doc.get('url', '')
            summary_result['score'] = doc.get('score', 0)
            summaries.append(summary_result)
            count += 1
    
    print("\n" + "=" * 60)
    print("Step 5: Saving results...")
    persist(summaries)
    
    print("\n" + "=" * 60)
    print("Workflow complete!")

