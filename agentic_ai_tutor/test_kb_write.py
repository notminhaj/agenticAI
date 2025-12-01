# test_kb_write.py
import json
from tools.knowledge_base_write import knowledge_base_write

print("=== TESTING knowledge_base_write ===\n")

# Test update_metadata
print("--- Testing update_metadata ---")
result = knowledge_base_write.func(
    topic="test_topic",
    mastery=6.0,
    confidence=9.0,
    reason="Testing sequential update",
    source="test_script"
)
print("METADATA UPDATE:", result.get("metadata_update"))

# Test write_note (and metadata update implicitly)
print("\n--- Testing write_note ---")
result = knowledge_base_write.func(
    topic="test_topic",
    note="This is a test note to verify the sequential write_note command.",
    mode="replace"
)
print("METADATA UPDATE:", result.get("metadata_update"))
print("NOTE WRITE:", result.get("note_write"))

print("\n=== TEST COMPLETE ===")
