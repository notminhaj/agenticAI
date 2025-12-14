import time
start = time.time()
print("Importing federated_search...")
try:
    from tools.federated_search import federated_search
    print(f"Imported in {time.time() - start:.2f}s")
except Exception as e:
    print(f"Import failed: {e}")
