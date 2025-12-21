import sys
import os

print(f"Python: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Path:")
for p in sys.path:
    print(f"  - {p}")

try:
    import crewai
    print(f"CrewAI: {crewai.__file__}")
    print(f"CrewAI Version: {crewai.__version__}")
except ImportError as e:
    print(f"Error importing crewai: {e}")

try:
    import fastapi
    print(f"FastAPI: {fastapi.__file__}")
except ImportError as e:
    print(f"Error importing fastapi: {e}")
