"""
Abstract base adapter interface.

All mode adapters must implement this interface to ensure
consistent behavior regardless of which mode is active.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Incoming chat request from frontend."""
    message: str
    session_id: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response sent back to frontend."""
    response: str
    session_id: str
    metadata: Optional[dict] = None


class BaseAdapter(ABC):
    """
    Abstract base class for mode adapters.
    
    Each mode (conversational, workflow, agent) must implement
    this interface so the router can treat them uniformly.
    """
    
    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the name of this mode."""
        pass
    
    @abstractmethod
    def handle(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a chat request and return a response.
        
        Args:
            request: The incoming chat request with message and session_id
            
        Returns:
            ChatResponse with the tutor's response
        """
        pass
    
    def get_info(self) -> dict:
        """Return information about this adapter."""
        return {
            "mode": self.mode_name,
            "status": "active"
        }
