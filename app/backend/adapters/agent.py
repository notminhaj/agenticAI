"""
Agent Mode Adapter (Stub).

This is a placeholder adapter for agent_mode (CrewAI).
The agent mode runs autonomous tasks rather than interactive chat,
so this adapter provides a minimal chat interface.

Future enhancement: Could accept task descriptions and stream
agent reasoning/actions back to the UI.
"""

from .base import BaseAdapter, ChatRequest, ChatResponse


class AgentAdapter(BaseAdapter):
    """
    Adapter for agent mode (CrewAI autonomous agents).
    
    Currently a stub - agent mode runs predefined tasks rather
    than responding to chat messages. This provides helpful
    messaging about its capabilities.
    """
    
    @property
    def mode_name(self) -> str:
        return "agent_mode"
    
    def handle(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a chat request in agent mode.
        
        Since agent mode runs autonomous tasks, this returns
        information about capabilities.
        """
        message = request.message.lower().strip()
        
        if "run" in message or "start" in message or "task" in message:
            response = """## Agent Mode

I'm configured in **agent mode**, which uses CrewAI for autonomous task execution.

To run the agent, use the command line:
```bash
python agent_mode/main.py
```

The agent will autonomously:
1. 🤖 Plan the task execution
2. 🔧 Use tools (search, summarize, fetch, persist)
3. 📊 Generate results based on the configured task

*Interactive chat is better suited for **conversational_mode**.*"""
        else:
            response = """## Agent Mode Active

I'm currently configured in **agent mode**, which runs autonomous CrewAI agents rather than interactive chat.

**Capabilities:**
- Run predefined autonomous tasks with tool usage
- Execute multi-step reasoning workflows

**To switch to interactive tutoring:**
Set `ACTIVE_MODE=conversational_mode` in your `.env` file and restart the server.

*Type "run task" for more info about running the agent.*"""
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            metadata={"mode": self.mode_name}
        )
