"""
Workflow Mode Adapter (Stub).

This is a placeholder adapter for workflow_mode.
The workflow mode is designed for batch processing (paper pipelines)
rather than interactive chat, so this adapter provides a minimal
chat interface that explains its purpose.

Future enhancement: Could accept "run pipeline" commands and
stream status updates back to the UI.
"""

from .base import BaseAdapter, ChatRequest, ChatResponse


class WorkflowAdapter(BaseAdapter):
    """
    Adapter for workflow mode (paper pipeline).
    
    Currently a stub - workflow mode doesn't naturally support
    interactive chat. This provides helpful messaging about
    its capabilities.
    """
    
    @property
    def mode_name(self) -> str:
        return "workflow_mode"
    
    def handle(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a chat request in workflow mode.
        
        Since workflow mode is batch-oriented, this returns
        information about capabilities.
        """
        message = request.message.lower().strip()
        
        if "run" in message or "start" in message or "pipeline" in message:
            response = """## Workflow Mode

I'm configured in **workflow mode**, which runs the AI Paper Pipeline.

To run the pipeline, use the command line:
```bash
python workflow_mode/main.py
```

This will:
1. 🔍 Search for trending AI papers on arXiv
2. 📥 Fetch and filter paper content
3. 🤖 Summarize papers using AI
4. 💾 Save results to markdown and JSONL files

*Interactive chat is better suited for **conversational_mode**.*"""
        else:
            response = """## Workflow Mode Active

I'm currently configured in **workflow mode**, which is designed for batch processing rather than interactive chat.

**Capabilities:**
- Run the AI Paper Pipeline to discover and summarize trending papers
- Generate markdown reports and JSONL data files

**To switch to interactive tutoring:**
Set `ACTIVE_MODE=conversational_mode` in your `.env` file and restart the server.

*Type "run pipeline" for more info about running the workflow.*"""
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            metadata={"mode": self.mode_name}
        )
