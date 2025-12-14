import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime
from crewai.tools import tool
from dotenv import load_dotenv
from crewai import LLM
from .fetch import fetch
from .rank_documents import rank_documents

# Load environment variables
load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Initialize LLM for keyword expansion
# Using a smaller model for speed if available, or the main one
llm = None

def get_llm():
    global llm
    if llm is None:
        llm = LLM(model="gpt-4.1-mini")
    return llm

def expand_keywords(topic: str) -> Dict[str, List[str]]:
    """
    Uses LLM to expand the topic into semantic keywords for different sources.
    """
    prompt = f"""
    You are a search expert. Given the topic "{topic}", generate a JSON object with specific search keywords for each of these sources:
    - "academic": 3-5 keywords for finding papers (technical, formal)
    - "general": 3-5 keywords for web/news (broad, current events)
    - "social": 3-5 keywords for social media discussions (hashtags, colloquial)
    
    Return ONLY the JSON object. Example:
    {{
        "academic": ["agentic ai architecture", "large language model agents"],
        "general": ["latest agentic ai news", "autonomous ai agents trends"],
        "social": ["#agenticai", "ai agents discussion"]
    }}
    """
    try:
        response = get_llm().call(messages=[{"role": "user", "content": prompt}])
        # clean up response if it has markdown code blocks
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        import json
        return json.loads(content)
    except Exception as e:
        print(f"[WARN] Keyword expansion failed: {e}. Using topic as default.")
        return {
            "academic": [topic],
            "general": [topic],
            "social": [topic]
        }

def normalize_result(title: str, url: str, source: str, snippet: str, timestamp: Optional[str] = None) -> Dict:
    return {
        "title": title.strip(),
        "url": url.strip(),
        "source": source,
        "snippet": snippet.strip() if snippet else "",
        "timestamp": timestamp
    }

def search_arxiv(keywords: List[str], limit: int) -> List[Dict]:
    results = []
    try:
        # Join keywords with OR for broader recall, or take the first few
        query = " OR ".join([f"all:{k}" for k in keywords[:2]])
        url = "http://export.arxiv.org/api/query"
        params = {"search_query": query, "start": 0, "max_results": limit}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text
                paper_id = entry.find('atom:id', ns).text
                summary = entry.find('atom:summary', ns).text
                published = entry.find('atom:published', ns).text
                results.append(normalize_result(
                    title=title,
                    url=paper_id,
                    source="arxiv",
                    snippet=summary[:300] + "...",
                    timestamp=published
                ))
    except Exception as e:
        print(f"[ERROR] arXiv search failed: {e}")
    return results

def search_brave(keywords: List[str], limit: int, source_type: str = "web") -> List[Dict]:
    results = []
    if not BRAVE_API_KEY:
        return results
    
    endpoint = "https://api.search.brave.com/res/v1/web/search" if source_type != "news" else "https://api.search.brave.com/res/v1/news/search"
    
    # Use the first keyword as the primary query
    q = keywords[0]
    
    try:
        resp = requests.get(
            endpoint,
            headers={"X-Subscription-Token": BRAVE_API_KEY},
            params={"q": q, "count": limit},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            key = "web" if source_type == "web" else "news"
            items = data.get(key, {}).get("results", [])
            for item in items:
                results.append(normalize_result(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    source=f"brave_{source_type}",
                    snippet=item.get('description', ''),
                    timestamp=item.get('age') or item.get('page_age')
                ))
    except Exception as e:
        print(f"[ERROR] Brave {source_type} search failed: {e}")
    return results

def search_hackernews(keywords: List[str], limit: int) -> List[Dict]:
    results = []
    try:
        # HN Algolia API
        q = keywords[0]
        resp = requests.get(
            "http://hn.algolia.com/api/v1/search",
            params={"query": q, "tags": "story", "hitsPerPage": limit},
            timeout=10
        )
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                if hit.get("url"): # Only keep if it has a URL
                    results.append(normalize_result(
                        title=hit.get("title", ""),
                        url=hit.get("url", ""),
                        source="hackernews",
                        snippet=f"Points: {hit.get('points')} | Comments: {hit.get('num_comments')}",
                        timestamp=hit.get("created_at")
                    ))
    except Exception as e:
        print(f"[ERROR] HN search failed: {e}")
    return results

def search_twitter_via_brave(keywords: List[str], limit: int) -> List[Dict]:
    # Fallback to Brave search with site:twitter.com and site:x.com
    results = []
    if not BRAVE_API_KEY:
        return results
    
    q = f"{keywords[0]} (site:twitter.com OR site:x.com)"
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY},
            params={"q": q, "count": limit},
            timeout=10
        )
        if resp.status_code == 200:
            items = resp.json().get("web", {}).get("results", [])
            for item in items:
                results.append(normalize_result(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    source="twitter_web",
                    snippet=item.get('description', ''),
                    timestamp=item.get('age')
                ))
    except Exception as e:
        print(f"[ERROR] Twitter search failed: {e}")
    return results

def search_substack_via_brave(keywords: List[str], limit: int) -> List[Dict]:
    results = []
    if not BRAVE_API_KEY:
        return results
    
    q = f"{keywords[0]} site:substack.com"
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY},
            params={"q": q, "count": limit},
            timeout=10
        )
        if resp.status_code == 200:
            items = resp.json().get("web", {}).get("results", [])
            for item in items:
                results.append(normalize_result(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    source="substack",
                    snippet=item.get('description', ''),
                    timestamp=item.get('age')
                ))
    except Exception as e:
        print(f"[ERROR] Substack search failed: {e}")
    return results


@tool("federated_search")
def federated_search(topic: str, limit: int = 5) -> str:
    """
    Performs a federated search across multiple sources (arXiv, Web, News, HN, Twitter, Substack)
    for the given topic. Returns a ranked, normalized list of results.
    
    Args:
        topic (str): The search topic.
        limit (int): Max results per source to fetch initially (default 5).
        
    Returns:
        str: A formatted string of the top results.
    """
    print(f"[Federated Search] Expanding keywords for: {topic}")
    keywords_map = expand_keywords(topic)
    
    all_results = []
    
    # 1. arXiv
    print("[Federated Search] Querying arXiv...")
    all_results.extend(search_arxiv(keywords_map.get("academic", [topic]), limit))
    
    # 2. Brave Web & News
    print("[Federated Search] Querying Brave Web & News...")
    all_results.extend(search_brave(keywords_map.get("general", [topic]), limit, "web"))
    all_results.extend(search_brave(keywords_map.get("general", [topic]), limit, "news"))
    
    # 3. HackerNews
    print("[Federated Search] Querying HackerNews...")
    all_results.extend(search_hackernews(keywords_map.get("social", [topic]), limit))
    
    # 4. Twitter (via Brave)
    print("[Federated Search] Querying Twitter...")
    all_results.extend(search_twitter_via_brave(keywords_map.get("social", [topic]), limit))
    
    # 5. Substack (via Brave)
    print("[Federated Search] Querying Substack...")
    all_results.extend(search_substack_via_brave(keywords_map.get("general", [topic]), limit))
    
    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r['url'] not in seen_urls:
            seen_urls.add(r['url'])
            unique_results.append(r)
            
    print(f"[Federated Search] Found {len(unique_results)} unique results. Fetching content for top results...")
    
    # Limit to top N for fetching to save time/bandwidth
    # We prioritize results that already have good snippets or are from high-quality sources
    # For now, just take the first limit * 2
    to_fetch = unique_results[:limit * 2]
    fetched_docs = []
    
    for doc in to_fetch:
        try:
            # Use fetch tool to get full content
            # fetch returns a dict with 'raw_text', 'url', etc.
            fetched = fetch.func(doc['url'])
            if fetched and fetched.get('raw_text'):
                # Merge metadata
                doc['raw_text'] = fetched['raw_text']
                fetched_docs.append(doc)
        except Exception as e:
            print(f"[WARN] Failed to fetch {doc['url']}: {e}")
            
    print(f"[Federated Search] Fetched {len(fetched_docs)} documents. Ranking...")

    # Rank using neural ranker
    try:
        # rank_documents expects list of dicts with text_key
        # We use 'raw_text' which we just populated
        ranked = rank_documents.func(topic, fetched_docs, text_key="raw_text")
        final_results = ranked
    except Exception as e:
        print(f"[WARN] Neural ranking failed ({e}), falling back to default order.")
        final_results = fetched_docs
    
    # Format output
    output_lines = [f"Federated Search Results for '{topic}' (Ranked & Fetched):\n"]
    for i, r in enumerate(final_results[:limit], 1): # Return top N ranked results
        score_str = f" [Score: {r.get('score', 0):.2f}]" if 'score' in r else ""
        output_lines.append(f"{i}. [{r['source'].upper()}] {r['title']}{score_str}")
        output_lines.append(f"   URL: {r['url']}")
        if r['timestamp']:
            output_lines.append(f"   Time: {r['timestamp']}")
        
        # Show a generous snippet of the FULL content now
        content_preview = r.get('raw_text', r.get('snippet', ''))[:500]
        output_lines.append(f"   Content: {content_preview}...\n")
        
    return "\n".join(output_lines)
