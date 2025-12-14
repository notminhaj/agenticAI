# brave_test.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env from current folder

API_KEY = os.getenv("BRAVE_API_KEY")

if not API_KEY:
    print("ERROR: BRAVE_API_KEY not found in .env")
    exit()

headers = {"X-Subscription-Token": API_KEY}

query = "trending agentic RAG 2025"

print(f"Searching Brave for: '{query}'\n")
print("="*80)

# Web search
print("WEB RESULTS:")
r = requests.get(
    "https://api.search.brave.com/res/v1/web/search",
    headers=headers,
    params={"q": query, "count": 6},
    timeout=10
)
if r.status_code == 200:
    for i, item in enumerate(r.json().get("web", {}).get("results", []), 1):
        print(f"{i}. {item['title']}")
        print(f"   {item['url']}")
        print(f"   Age: {item.get('age', 'N/A')}")
        print(f"   → {item.get('description', 'No snippet')[:140]}...\n")
else:
    print("Web failed:", r.status_code, r.text[:200])

print("-"*80)

# News search
print("NEWS RESULTS:")
r = requests.get(
    "https://api.search.brave.com/res/v1/news/search",
    headers=headers,
    params={"q": query, "count": 4},
    timeout=10
)
if r.status_code == 200:
    for i, item in enumerate(r.json().get("news", {}).get("results", []), 1):
        print(f"{i}. {item['title']}")
        print(f"   {item['url']}")
        print(f"   Age: {item.get('age', 'N/A')}")
        print(f"   → {item.get('description', 'No snippet')[:140]}...\n")
else:
    print("News failed:", r.status_code, r.text[:200])

print("="*80)
print("Done. If you see real titles + URLs → Brave is 100% working.")