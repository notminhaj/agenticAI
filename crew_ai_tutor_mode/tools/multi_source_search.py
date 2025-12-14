# tools/multi_source_search.py
import os
import requests
from typing import List, Dict
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

@tool("multi_source_search")
def multi_source_search(query: str, num_results: int = 10, sources: List[str] = None) -> str:
    """Search arXiv + Brave web + Brave news for latest content. Returns formatted results."""
    if sources is None:
        sources = ['arxiv', 'brave_web', 'brave_news']
    
    results = []
    
    # === arXiv ===
    if 'arxiv' in sources:
        try:
            from .search import search  # your existing arXiv tool
            for r in search(query, limit=max(1, num_results // 3)):
                results.append(f"[arXiv] {r['title']}\n{r['url']}\n{r.get('abstract', '')[:200]}...\n")
        except Exception as e:
            results.append(f"[arXiv] Error: {e}\n")
    
    # === Brave Web ===
    if 'brave_web' in sources and BRAVE_API_KEY:
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": BRAVE_API_KEY},
                params={"q": query, "count": max(1, num_results // 3)},
                timeout=10
            )
            if resp.status_code == 200:
                for r in resp.json().get("web", {}).get("results", []):
                    results.append(f"[Web] {r['title']}\n{r['url']}\nAge: {r.get('age','N/A')}\n{r.get('description','')[:200]}...\n")
        except Exception as e:
            results.append(f"[Web] Error: {e}\n")
    
    # === Brave News ===
    if 'brave_news' in sources and BRAVE_API_KEY:
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/news/search",
                headers={"X-Subscription-Token": BRAVE_API_KEY},
                params={"q": query, "count": max(1, num_results // 3)},
                timeout=10
            )
            if resp.status_code == 200:
                for r in resp.json().get("news", {}).get("results", []):
                    results.append(f"[News] {r['title']}\n{r['url']}\nAge: {r.get('age','N/A')}\n{r.get('description','')[:200]}...\n")
        except Exception as e:
            results.append(f"[News] Error: {e}\n")
    
    if not results:
        return "No results found from any source."
    
    final_output = f"Found {len(results)} results for '{query}':\n\n"
    final_output += "\n\n".join(results)
    return final_output