"""
Tutor Agent - Stateful Conversational AI Tutor

This module implements a deterministic, stateful tutoring agent.
It enforces strict rules for tool usage, knowledge management, and evaluation.

KEY FEATURES:
1. Full Tool Exposure: fetch, search, kb_read, kb_write, rank, summarize.
2. Mandatory Evaluation Phase: Agent determines tool needs before responding.
3. Strict KB Rules: Mandatory writes for new info/skills.
4. URL Handling: Automatic fetch for user-provided URLs.
5. Observability: Detailed debug logs when TESTING=True.
"""

import re
import json
from typing import List, Dict, Any, Optional
from crewai import LLM
from unified_tool import execute_tool
from config import TESTING
from session_state import SessionState
from topic_normalizer import normalize_topic, load_existing_topics


def debug_log(message: str) -> None:
    """Print debug message if TESTING is enabled."""
    if TESTING:
        print(f"[DEBUG] {message}")


# System prompt with strict policies
SYSTEM_PROMPT_TEMPLATE = '''You are an advanced AI Tutor. Your goal is to teach the user effectively, adapting to their knowledge level.

You have access to a SINGLE tool called `execute_tool` which can execute Python code.
You can use this tool to import and run other tools available in the `tools/` directory.

=== CRITICAL: HOW TO USE TOOLS ===

**YOU MUST OUTPUT A PYTHON CODE BLOCK TO EXECUTE ANY TOOL.**

DO NOT say "I will update" or "I'll fetch" without including the actual code block.
If you need to take an action, you MUST include the code in your response like this:

```python
from tools.knowledge_base_write import knowledge_base_write
result = knowledge_base_write.func(topic="...", mastery=5.0, confidence=5.0, reason="...", source="agent", note="...", mode="append")
print(result)
```

The system will execute your code and return the result. Only AFTER seeing the result should you provide your final answer.

=== AVAILABLE TOOLS ===

1. **fetch** - Fetch content from a URL (REQUIRED when user provides a link)
   ```python
   from tools.fetch import fetch
   result = fetch.func("https://example.com")
   print(result)
   ```

2. **federated_search** - Search web/academic/social for info
   ```python
   from tools.federated_search import federated_search
   result = federated_search.func("topic name", limit=5)
   print(result)
   ```

3. **knowledge_base_read** - Read user's existing knowledge
   ```python
   from tools.knowledge_base_read import knowledge_base_read
   result = knowledge_base_read.func(query="Agentic AI")
   print(result)
   ```

4. **knowledge_base_write** - Update user's knowledge base (REQUIRED when teaching new info or user shows skill)
   ```python
   from tools.knowledge_base_write import knowledge_base_write
   result = knowledge_base_write.func(
       topic="Agentic AI",
       mastery=5.0,
       confidence=6.0,
       reason="User learned about agent workflows",
       source="agent",
       note="Learned about structured workflows for AI coding assistants.",
       mode="append"
   )
   print(result)
   ```

5. **summarize** - Summarize text content
   ```python
   from tools.summarize import summarize
   result = summarize.func(raw_text="long text here...")
   print(result)
   ```

6. **rank_documents** - Rank documents by relevance
   ```python
   from tools.rank_documents import rank_documents
   result = rank_documents.func(query="topic", documents=[...])
   print(result)
   ```

=== MANDATORY ACTIONS ===

**KB WRITE (when user learns or shows skill):**
- You MUST output a `knowledge_base_write` code block IMMEDIATELY.
- Do NOT just say "I'll update your KB" - actually include the code block.
- Triggers: "I just learned about X", "I built my own Y", "I now understand Z"

**KB READ (when user changes topic or asks about a topic):**
- You MUST output a `knowledge_base_read` code block IMMEDIATELY when the user:
  - Switches to a new topic (e.g., "Now I want to talk about neurology")
  - Asks about a topic (e.g., "Tell me about X", "What do I know about Y")
  - Mentions a topic they want to explore (e.g., "Let's discuss physics")
- This gives you access to the user's NOTES, not just the metadata summary.
- Do NOT respond about a topic without first reading the user's notes on it.

**FETCH (when user provides a URL):**
- You MUST output a `fetch` code block IMMEDIATELY.
- Do NOT respond until you have fetched the content.

=== TOPIC NORMALIZATION ===
- Use existing topics from the KB summary below.
- Map specific phrases to broad topics (e.g., "AI workflows" -> "Agentic AI").

=== MASTERY/CONFIDENCE GUIDELINES ===
- 0-2: Beginner
- 3-5: Intermediate
- 6-8: Advanced
- 9-10: Expert

=== USER'S KNOWLEDGE BASE SUMMARY ===
{kb_summary}

=== CURRENT TOPIC ===
{current_topic}
'''



class TutorAgent:
    """
    Stateful conversational tutor with strict rule enforcement.
    """
    
    def __init__(self):
        debug_log("Initializing TutorAgent (Stateful Mode)...")
        
        # Session state for KB metadata
        self.session = SessionState()
        self.existing_topics = self.session.get_all_topic_names()
        
        # LLM
        self.llm = LLM(model="gpt-4o-mini")
        
        # Conversation history - Internal use only
        self.history: List[Dict[str, str]] = []
        
        # Loop safety
        self.max_tool_turns = 8
        
        debug_log(f"Loaded {len(self.existing_topics)} topics. Ready.")
    
    def _get_system_prompt(self) -> str:
        """Generate system prompt with current KB state."""
        kb_summary = self.session.get_topic_summary()
        current_topic = self.session.get_current_topic() or "None"
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            kb_summary=kb_summary,
            current_topic=current_topic
        )
    
    def _format_history(self) -> str:
        """Format history for LLM context."""
        formatted = ""
        for msg in self.history:
            role = msg["role"].upper()
            content = msg["content"]
            formatted += f"{role}: {content}\n"
        return formatted
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extract Python code from markdown blocks."""
        match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1)
        return None
    
    def _detect_urls(self, text: str) -> List[str]:
        """Simple regex to detect URLs in user input."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)

    def chat(self, user_input: str) -> str:
        """
        Main stateful chat loop.
        """
        debug_log(f"User Input: {user_input[:100]}")
        
        # 1. Add user message to history
        self.history.append({"role": "user", "content": user_input})
        
        # 2. Strict URL Rule Injection
        urls = self._detect_urls(user_input)
        if urls:
            debug_log(f"Detected URLs: {urls}")
            # Inject a system instruction to force fetch
            # This ensures the "Evaluation Phase" respects the strict rule
            url_instruction = f"SYSTEM_INSTRUCTION: User provided URLs: {urls}. You MUST call `tools.fetch` on these URLs immediately."
            self.history.append({"role": "system", "content": url_instruction})
        
        tool_turn_count = 0
        final_response = ""
        
        while tool_turn_count < self.max_tool_turns:
            # Prepare Prompt
            system_prompt = self._get_system_prompt()
            history_text = self._format_history()
            full_prompt = f"{system_prompt}\n\nCONVERSATION HISTORY:\n{history_text}\n\nASSISTANT:"
            
            # Call LLM
            debug_log(f"Turn {tool_turn_count + 1}: Calling LLM...")
            response = self.llm.call(messages=[{"role": "user", "content": full_prompt}])
            
            # Check for tool usage
            code = self._extract_code(response)
            
            if code:
                debug_log("Tool Call Detected.")
                if TESTING:
                    print(f"\n[CODE]\n{code}\n[/CODE]\n")
                
                # Execute
                exec_result = execute_tool(code)
                
                # Log execution
                stdout = exec_result.get('stdout', '')
                result = exec_result.get('result', '')
                error = exec_result.get('error', '')
                
                debug_log(f"Stdout: {stdout[:100]}...")
                debug_log(f"Result: {str(result)[:100]}...")
                if error:
                    debug_log(f"Error: {error}")
                
                # Create tool output message
                tool_msg = f"TOOL_OUTPUT:\nStdout: {stdout}\nResult: {result}\nError: {error}"
                
                # Add to history (Assistant thought + Tool result)
                self.history.append({"role": "assistant", "content": response})
                self.history.append({"role": "system", "content": tool_msg})
                
                # Reload KB if write occurred
                if "knowledge_base_write" in code:
                    debug_log("KB Write detected. Reloading metadata.")
                    self.session.reload_metadata()
                    self.existing_topics = self.session.get_all_topic_names()
                
                tool_turn_count += 1
            else:
                # No tool call -> Final Response
                debug_log("No tool call. Final response generated.")
                final_response = response
                
                # Add final response to history
                self.history.append({"role": "assistant", "content": final_response})
                return final_response
        
        return "I apologize, I'm stuck in a loop. Let's try again."

    def set_topic(self, topic: str) -> None:
        """Set current topic via normalizer."""
        canonical, _, _ = normalize_topic(topic, self.existing_topics)
        self.session.set_current_topic(canonical)


def create_tutor() -> TutorAgent:
    return TutorAgent()
