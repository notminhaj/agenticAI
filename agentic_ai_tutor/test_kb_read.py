# test_kb_read.py
import json
from tools.knowledge_base_read import kb_read

print("=== TESTING kb_read() TOOL ===\n")

# Access the underlying function via .func attribute
result = kb_read.func()

print("STATUS:", result.get("status"))
print("MESSAGE:", result.get("message"))
print("\n--- KNOWLEDGE PROFILE ---")
print(json.dumps(result["profile"], indent=2))

print("\n--- RECENT EVENTS (last 10, most recent first) ---")
for i, event in enumerate(result["recent_events"], 1):
    ts = event.get("timestamp", "no timestamp")
    event_type = event.get("event", "unknown")
    print(f"{i}. [{ts}] {event_type.upper()}: {event.get('notes', event.get('reason', 'no details'))}")

print("\n=== TEST COMPLETE ===")
if result["status"] == "success":
    print("kb_read() WORKS PERFECTLY — your agent now has MEMORY")
else:
    print("Fix needed — check paths or JSON syntax")