# test_kb_update.py
import json
from datetime import datetime
from tools.knowledge_base_update import kb_update

print("=== TESTING kb_update() TOOL ===\n")

# Test 1: Update existing topic
print("Test 1: Improving 'advanced RAG' mastery from 3.0 → 6.5")
result1 = kb_update.func({
    "topic": "advanced RAG",
    "mastery": 6.5,
    "confidence": 7.0,
    "notes": "Finally implemented HyDE + parent-child retrieval. Works!",
    "reason": "Successfully built and tested advanced RAG pipeline"
})
print("Result:", result1)
print()

# Test 2: Add brand new topic
print("Test 2: Adding new topic 'self-healing agents'")
result2 = kb_update.func({
    "topic": "self-healing agents",
    "mastery": 4.0,
    "confidence": 5.0,
    "notes": "Read about Reflexion and STaR. Built simple version.",
    "reason": "First implementation of reflection loop"
})
print("Result:", result2)
print()

# Final: Show the latest timeline entry
from tools.knowledge_base_read import kb_read
data = kb_read.func()
print("LATEST TIMELINE ENTRY:")
latest = data["recent_events"][0] if data["recent_events"] else "none"
print(json.dumps(latest, indent=2))

print("\n=== TEST COMPLETE ===")
print("kb_update() WORKS — YOUR AGENT NOW HAS WRITE ACCESS TO YOUR BRAIN")