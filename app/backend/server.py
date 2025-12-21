"""
FastAPI Server for AI Tutor.

This is the main entry point for the backend adapter layer.
It exposes a unified chat API that routes to the active mode.
"""

import sys
import os
import pkg_resources
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.backend.config import config
from app.backend.router import get_adapter, get_available_modes, get_active_mode
from .adapters import ChatRequest, ChatResponse


# Create FastAPI app
app = FastAPI(
    title="AI Tutor API",
    description="Mode-agnostic chat API for the AI Tutor system",
    version="1.0.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health & Info Endpoints
# ============================================================

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AI Tutor API",
        "version": "1.0.0",
        "active_mode": get_active_mode(),
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "mode": get_active_mode()}


@app.get("/api/modes")
async def list_modes():
    """List available modes and which is active."""
    return {
        "active": get_active_mode(),
        "available": get_available_modes(),
    }


# ============================================================
# Debug Endpoint
# ============================================================

@app.get("/api/debug")
async def debug_env():
    """Debug endpoint to check server environment."""
    try:
        import crewai
        crewai_info = {
            "version": crewai.__version__,
            "file": crewai.__file__,
            "imported": True
        }
    except ImportError as e:
        crewai_info = {
            "imported": False,
            "error": str(e)
        }
    
    return {
        "python_executable": sys.executable,
        "cwd": os.getcwd(),
        "sys_path": sys.path,
        "crewai": crewai_info,
        "packages": [f"{p.project_name}=={p.version}" for p in pkg_resources.working_set]
    }


# ============================================================
# Chat Endpoints
# ============================================================

class ChatRequestBody(BaseModel):
    """Request body for chat endpoint."""
    message: str
    session_id: str
    context: Optional[dict] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequestBody):
    """
    Send a message and receive a response from the AI tutor.
    
    The request is routed to the active mode adapter configured
    by the ACTIVE_MODE environment variable.
    """
    try:
        adapter = get_adapter()
        
        request = ChatRequest(
            message=body.message,
            session_id=body.session_id,
            context=body.context,
        )
        
        response = adapter.handle(request)
        return response
        
    except Exception as e:
        if config.DEBUG:
            import traceback
            traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/api/chat/new")
async def new_chat():
    """
    Start a new chat session.
    
    Returns a new session ID for the frontend to use.
    """
    import uuid
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


# ============================================================
# Run with: uvicorn app.backend.server:app --reload
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
