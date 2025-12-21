"""
Conversational Mode Adapter.

Wraps the conversational_mode/tutor_agent.py to conform to the
unified chat interface expected by the frontend.
"""

import sys
from pathlib import Path
from typing import Dict

from .base import BaseAdapter, ChatRequest, ChatResponse

# Add conversational_mode to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONV_MODE_PATH = PROJECT_ROOT / "conversational_mode"
if str(CONV_MODE_PATH) not in sys.path:
    sys.path.insert(0, str(CONV_MODE_PATH))


class ConversationalAdapter(BaseAdapter):
    """
    Adapter for the conversational AI tutor mode.
    
    This wraps the TutorAgent from conversational_mode/tutor_agent.py
    and provides a stateful session management layer.
    """
    
    def __init__(self):
        self._sessions: Dict[str, any] = {}
    
    @property
    def mode_name(self) -> str:
        return "conversational_mode"
    
    def _get_or_create_agent(self, session_id: str):
        """Get existing agent for session or create a new one."""
        if session_id not in self._sessions:
            # Import here to avoid loading until needed
            from tutor_agent import create_tutor
            self._sessions[session_id] = create_tutor()
        return self._sessions[session_id]
    
    def handle(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a chat request using the conversational tutor.
        
        Args:
            request: Chat request with message and session_id
            
        Returns:
            ChatResponse with tutor's response
        """
        try:
            agent = self._get_or_create_agent(request.session_id)
            
            # Call the agent's chat method
            response_text = agent.chat(request.message)
            
            return ChatResponse(
                response=response_text,
                session_id=request.session_id,
                metadata={
                    "mode": self.mode_name,
                    "tools_used": []  # Could extract from agent if needed
                }
            )
        except Exception as e:
            print(f"[ERROR] Conversational Adapter Error: {e}", file=sys.stderr)
            print(f"[DEBUG] Sys Path: {sys.path}", file=sys.stderr)
            try:
                import crewai
                print(f"[DEBUG] CrewAI importable in handler: {crewai.__file__}", file=sys.stderr)
            except ImportError:
                print(f"[DEBUG] CrewAI NOT importable in handler", file=sys.stderr)
            
            return ChatResponse(
                response=f"I encountered an error: {str(e)}. Let me try again.",
                session_id=request.session_id,
                metadata={
                    "mode": self.mode_name,
                    "error": str(e)
                }
            )
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session's agent instance."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
