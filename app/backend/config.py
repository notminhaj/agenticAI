"""
Configuration loader for the backend adapter layer.

Loads environment variables and provides typed configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (wrapped in try/except for corrupted files)
PROJECT_ROOT = Path(__file__).parent.parent.parent
try:
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass  # Use defaults if .env is corrupted


class Config:
    """Application configuration loaded from environment."""
    
    # Active mode: conversational_mode, workflow_mode, or agent_mode
    ACTIVE_MODE: str = os.getenv("ACTIVE_MODE", "conversational_mode")
    
    # Server settings
    HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # CORS settings for frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


config = Config()
