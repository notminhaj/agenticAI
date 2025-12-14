# test_kb_read.py
import json
from tools.knowledge_base_read import knowledge_base_read

print("=== TESTING knowledge_base_read ===\n")

# Test read_profile (always returned)
print("--- Testing read_profile ---")
result = knowledge_base_read.func()
print("PROFILE KEYS:", list(result.get("profile", {}).keys()))
print("RECENT EVENTS COUNT:", len(result.get("profile", {}).get("recent_events", [])))

# Test search_notes
print("\n--- Testing search_notes ---")
search_result = knowledge_base_read.func(query="python")
if "search_results" in search_result:
    notes = search_result["search_results"]
    print(f"Found {len(notes)} notes for 'python'")
    if notes:
        print("Top note:", notes[0].get("title"))
else:
    print("No search results returned")

# Test read_note removed as note_path argument is deprecated
# The content is now returned in search_results
if "search_results" in search_result and search_result["search_results"]:
    print("Top note content length:", len(search_result["search_results"][0].get("content", "")))

print("\n=== TEST COMPLETE ===")
