import sys
import os
import uvicorn
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_ROOT / "venv"
VENV_SCRIPTS = VENV_DIR / "Scripts"
VENV_PYTHON = VENV_SCRIPTS / "python.exe"

# Force venv Python in PATH (CRITICAL for uvicorn --reload subprocess)
os.environ["VIRTUAL_ENV"] = str(VENV_DIR)
os.environ["PATH"] = f"{VENV_SCRIPTS};{os.environ.get('PATH', '')}"

sys.path.insert(0, str(PROJECT_ROOT))

# Set active mode
os.environ["ACTIVE_MODE"] = "conversational_mode"

print("="*60)
print("Starting AI Tutor Backend")
print(f"Python: {sys.executable}")
print(f"Venv: {VENV_DIR}")
print(f"Root: {PROJECT_ROOT}")
print("="*60)

# Import verification
try:
    print("Verifying imports...")
    import crewai
    print(f"✅ crewai {crewai.__version__} found at {crewai.__file__}")
    import fastapi
    print(f"✅ fastapi {fastapi.__version__} found at {fastapi.__file__}")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please install missing dependencies: pip install requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    print("\nStarting Uvicorn server (reload disabled to use venv Python)...")
    print("NOTE: Restart manually after code changes.\n")
    uvicorn.run(
        "app.backend.server:app",
        host="127.0.0.1",
        port=8001,
        reload=False,  # Disabled to prevent subprocess using system Python
    )
