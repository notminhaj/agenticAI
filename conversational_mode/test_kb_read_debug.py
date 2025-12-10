import sys
import os
import json

# Add conversational_mode to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from tools.knowledge_base_read import knowledge_base_read

def test_kb_read():
    query = "model context protocol"
    print(f"Testing knowledge_base_read with query: '{query}'")
    
    try:
        result = knowledge_base_read.func(query)
        print("\nResult keys:", result.keys())
        
        search_results = result.get("search_results", [])
        print(f"\nFound {len(search_results)} search results.")
        
        for i, res in enumerate(search_results):
            print(f"\nResult {i+1}:")
            print(f"  Title: {res.get('title')}")
            print(f"  Path: {res.get('note_path')}")
            print(f"  Score: {res.get('score')}")
            print(f"  Content Preview: {res.get('content')[:100]}...")
            
    except Exception as e:
        print(f"Error executing tool: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kb_read()
