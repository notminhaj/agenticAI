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

# Test read_note
if "search_results" in search_result and search_result["search_results"]:
    note_path = search_result["search_results"][0].get("note_path")
    print(f"\n--- Testing read_note for {note_path} ---")
    note_result = knowledge_base_read.func(note_path=note_path)
    if "note_content" in note_result:
        print(f"Note content length: {len(note_result['note_content'])}")
    else:
        print("Note content not returned")
else:
    print("\nSkipping read_note test as no note was found.")

print("\n=== TEST COMPLETE ===")
