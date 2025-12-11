"""
Tutor Agent - Policy-Enforced Conversational AI Tutor

This module implements a tutor agent with CODE-LEVEL policy enforcement.
The agent CANNOT produce a final response until all triggered policies are satisfied.

ARCHITECTURE:
1. PolicyTracker: Detects and tracks policy obligations
2. Arbitration Loop: Forces tool calls until policies are satisfied
3. LLM: Generates responses and tool calls, guided by pending policy list
"""

import re
import json
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from crewai import LLM
from unified_tool import execute_tool
from config import TESTING
from session_state import SessionState
from topic_normalizer import normalize_topic, load_existing_topics


def debug_log(message: str) -> None:
    """Print debug message if TESTING is enabled."""
    if TESTING:
        print(f"[DEBUG] {message}")


@dataclass
class PolicyState:
    """Tracks which policies are triggered and satisfied."""
    kb_read_required: bool = False
    kb_read_satisfied: bool = False
    kb_read_topic: str = ""
    
    kb_write_required: bool = False
    kb_write_satisfied: bool = False
    
    search_required: bool = False
    search_satisfied: bool = False
    
    fetch_required: bool = False
    fetch_satisfied: bool = False
    fetch_urls: List[str] = field(default_factory=list)
    
    def get_pending_policies(self) -> List[str]:
        """Return list of unsatisfied policies in execution order."""
        pending = []
        
        # FETCH first (if URL provided, get content first)
        if self.fetch_required and not self.fetch_satisfied:
            pending.append(f"FETCH (urls: {self.fetch_urls})")
        
        # KB_READ second (understand user's current knowledge)
        if self.kb_read_required and not self.kb_read_satisfied:
            pending.append(f"KB_READ (topic: {self.kb_read_topic})")
        
        # SEARCH third (get new information)
        if self.search_required and not self.search_satisfied:
            pending.append("SEARCH")
        
        # KB_WRITE last (record new content BEFORE presenting to user)
        if self.kb_write_required and not self.kb_write_satisfied:
            pending.append("KB_WRITE")
        
        return pending
    
    def all_satisfied(self) -> bool:
        """Check if all triggered policies are satisfied."""
        if self.kb_read_required and not self.kb_read_satisfied:
            return False
        if self.kb_write_required and not self.kb_write_satisfied:
            return False
        if self.search_required and not self.search_satisfied:
            return False
        if self.fetch_required and not self.fetch_satisfied:
            return False
        return True
    
    def mark_satisfied(self, tool_code: str) -> None:
        """Mark policies as satisfied based on tool code executed."""
        if "knowledge_base_read" in tool_code:
            self.kb_read_satisfied = True
        if "knowledge_base_write" in tool_code:
            self.kb_write_satisfied = True
        if "federated_search" in tool_code:
            self.search_satisfied = True
        if "fetch" in tool_code and "fetch.func" in tool_code:
            self.fetch_satisfied = True


class PolicyDetector:
    """Detects which policies are triggered by user input."""
    
    SEARCH_TRIGGERS = ['recent', 'new', 'latest', 'current', 'today', '2024', '2025', 
                       'update', 'news', 'happening', 'trend']
    
    TOPIC_TRIGGERS = ['tell me about', 'explain', 'what is', 'what are', 'how does',
                      'i want to learn', 'teach me', 'let\'s discuss', 'talk about',
                      'interested in', 'curious about']
    
    SKILL_TRIGGERS = ['i built', 'i made', 'i created', 'i implemented', 'i developed',
                      'i learned', 'i understand', 'i know', 'i figured out', 'i completed']
    
    @staticmethod
    def detect_urls(text: str) -> List[str]:
        """Detect URLs in text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def detect_search_need(text: str) -> bool:
        """Check if user is asking for recent/new information."""
        text_lower = text.lower()
        return any(trigger in text_lower for trigger in PolicyDetector.SEARCH_TRIGGERS)
    
    @staticmethod
    def detect_topic_interest(text: str) -> Optional[str]:
        """Detect if user is expressing interest in a topic."""
        text_lower = text.lower()
        
        # Check for topic trigger phrases
        for trigger in PolicyDetector.TOPIC_TRIGGERS:
            if trigger in text_lower:
                # Extract the topic after the trigger phrase
                idx = text_lower.find(trigger) + len(trigger)
                topic_part = text[idx:].strip()
                # Take first few words as topic
                words = topic_part.split()[:5]
                if words:
                    return ' '.join(words).strip('.,?!')
        
        # Check for confusion indicators (e.g., "X doesn't make sense", "confused about X")
        confusion_triggers = ["doesn't make sense", "don't understand", "confused about", "struggling with", "help with"]
        for trigger in confusion_triggers:
            if trigger in text_lower:
                # If trigger is "doesn't make sense", look BEFORE it
                if trigger == "doesn't make sense":
                    # Look for "something about X" or just X
                    if "something about" in text_lower:
                        start = text_lower.find("something about") + len("something about")
                        end = text_lower.find(trigger)
                        return text_lower[start:end].strip()
                    else:
                        # Fallback: take previous 5 words
                        end = text_lower.find(trigger)
                        words = text_lower[:end].split()[-5:]
                        return ' '.join(words).strip()
                else:
                    # Look AFTER trigger
                    idx = text_lower.find(trigger) + len(trigger)
                    words = text[idx:].split()[:5]
                    return ' '.join(words).strip('.,?!')

        # Check for role/context context (e.g. "I am a X student")
        if "i am a" in text_lower and "student" in text_lower:
             start = text_lower.find("i am a") + len("i am a")
             end = text_lower.find("student")
             if start < end:
                 return text_lower[start:end].strip()

        # Check for topic shift indicators
        if text_lower.startswith('now ') or 'switch to' in text_lower or 'change topic' in text_lower:
            # Extract topic from rest of message
            words = text.split()[1:6]  # Skip "now" and take next words
            if words:
                return ' '.join(words).strip('.,?!')
        
        return None
    
    @staticmethod
    def detect_skill_demonstration(text: str) -> bool:
        """Check if user is demonstrating an applied skill."""
        text_lower = text.lower()
        return any(trigger in text_lower for trigger in PolicyDetector.SKILL_TRIGGERS)
    
    @classmethod
    def analyze(cls, text: str, current_topic: Optional[str] = None) -> PolicyState:
        """Analyze user input and return triggered policies."""
        state = PolicyState()
        
        # FETCH policy
        urls = cls.detect_urls(text)
        if urls:
            state.fetch_required = True
            state.fetch_urls = urls
        
        # SEARCH policy
        if cls.detect_search_need(text):
            state.search_required = True
        
        # KB_READ policy - topic interest or topic shift
        detected_topic = cls.detect_topic_interest(text)
        if detected_topic:
            state.kb_read_required = True
            state.kb_read_topic = detected_topic
        
        # KB_WRITE policy - multiple triggers:
        # 1. User demonstrates a skill
        # 2. Search is required (search results = new content to teach = must record)
        # 3. User asks about a topic (agent will teach something)
        if cls.detect_skill_demonstration(text):
            state.kb_write_required = True
        
        if state.search_required:
            # If we're searching, we'll be teaching new content -> must write to KB
            state.kb_write_required = True
        
        if detected_topic:
            # If user asks about a topic, we'll likely teach -> must write to KB
            state.kb_write_required = True
        
        return state


# System prompt - now shorter, policies enforced by code
SYSTEM_PROMPT_TEMPLATE = '''You are an advanced AI Tutor.

=== PERSONA: THE AMBITIOUS FRIEND ===
- **TONE**: Concise, conversational, direct. NO lecture mode. NO academic fluff.
- **ROLE**: You are a "Friendly Peer" on the surface, but a "Relentless Coach" underneath.
- **AGENDA**: You have a HIDDEN AGENDA to desperately and relentlessly elevate the user's skills. Every interaction, even small talk, must push them slightly higher.
- **THE MASK**: You hide this agenda behind a mask of casual friendship. You don't say "I will teach you". You say "Check this out" or "Here's the trick".
- **CONCISENESS**: Get to the point. Respect the user's time.

=== TOOL EXECUTION ===
You can execute tools by outputting a Python code block. The system will run it and return results.

**Available Tools:**
- `knowledge_base_read`: Read user's notes on a topic
- `knowledge_base_write`: Record learning in user's KB
- `federated_search`: Search for current information
- `fetch`: Fetch content from a URL

**Code Format:**
```python
from tools.tool_name import tool_name
result = tool_name.func(...)
print(result)
```

=== PENDING POLICIES ===
{pending_policies}

**INSTRUCTIONS FOR PENDING POLICIES:**
1. **KB_READ / SEARCH / FETCH**: Execute these *immediately* (before answering).
2. **KB_WRITE**: 
    - First, write your full, helpful explanation to the user.
    - Then, AT THE END of your response, output the `knowledge_base_write` code block.
    - **CRITICAL MASTERY RULE**: When calling `knowledge_base_write`, set `mastery` and `confidence` assuming the user *just read and understood* your explanation.
    - If you are introducing a new topic, do NOT set mastery to 0.0. Set it to **1.0 - 2.0** to reflect that they now have introductory knowledge from you.

**Example of Teaching & Recording:**
"Agentic AI is... [full explanation] ...
```python
from tools.knowledge_base_write import knowledge_base_write
# Mastery set to 1.5 because user just learned the basics from me
result = knowledge_base_write.func(topic="Agentic AI", mastery=1.5, confidence=3.0, note="Taught definition of...")
print(result)
```"


=== TOPIC NAMING CONVENTION ===
- **ALWAYS use broad, high-level topics** (e.g., "Chess", "Python", "Physics").
- Avoid narrow sub-topics (e.g., use "Chess" instead of "Endgame Theory").
- Check the "USER'S KNOWLEDGE BASE" list below. If a broad topic exists, USE IT.

=== RESPONSE STYLE ===
- **STIMULATING SIGN-OFF**: Always end your response with a follow-up question, a challenge, or a suggestion for what to explore next.
- **SILENT KB UPDATES**: DO NOT say "I will update your knowledge base" or "I've recorded this". Just do it silently. The user knows you are learning.

=== USER'S KNOWLEDGE BASE ===
{kb_summary}

=== CURRENT TOPIC ===
{current_topic}

=== TOOL EXAMPLES ===

KB Read:
```python
from tools.knowledge_base_read import knowledge_base_read
result = knowledge_base_read.func(query="topic name")
print(result)
```

KB Write:
```python
from tools.knowledge_base_write import knowledge_base_write
result = knowledge_base_write.func(
    topic="Topic Name",
    mastery=5.0,
    confidence=6.0,
    reason="Why updating",
    source="agent",
    note="What was learned",
    mode="append"
)
print(result)
```

Search:
```python
from tools.federated_search import federated_search
result = federated_search.func("query", limit=5)
print(result)
```

Fetch:
```python
from tools.fetch import fetch
result = fetch.func("https://example.com")
print(result)
```
'''


class TutorAgent:
    """
    Policy-enforced conversational tutor.
    
    The agent CANNOT produce a final response until all triggered
    policies are satisfied. This is enforced by code, not prompts.
    """
    
    def __init__(self):
        debug_log("Initializing TutorAgent (Policy-Enforced Mode)...")
        
        self.session = SessionState()
        self.existing_topics = self.session.get_all_topic_names()
        self.llm = LLM(model="gpt-4o-mini")
        self.history: List[Dict[str, str]] = []
        self.max_tool_turns = 10
        
        debug_log(f"Loaded {len(self.existing_topics)} topics. Ready.")
    
    def _get_system_prompt(self, pending_policies: List[str]) -> str:
        """Generate system prompt with pending policies."""
        kb_summary = self.session.get_topic_summary()
        current_topic = self.session.get_current_topic() or "None"
        
        if pending_policies:
            pending_str = "**YOU MUST SATISFY THESE BEFORE RESPONDING:**\n"
            for p in pending_policies:
                pending_str += f"- {p}\n"
        else:
            pending_str = "All policies satisfied. You may provide your final response."
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            pending_policies=pending_str,
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

    def chat(self, user_input: str) -> str:
        """
        Main chat loop with code-level policy enforcement.
        """
        debug_log(f"User Input: {user_input[:100]}")
        
        # Add user message to history
        self.history.append({"role": "user", "content": user_input})
        
        # Detect policies triggered by this input
        policy_state = PolicyDetector.analyze(user_input, self.session.get_current_topic())
        
        # Log detected policies
        pending = policy_state.get_pending_policies()
        if pending:
            debug_log(f"Policies triggered: {pending}")
        else:
            debug_log("No policies triggered")
        
        tool_turn_count = 0
        tools_used = []
        
        while tool_turn_count < self.max_tool_turns:
            # Get current pending policies
            pending = policy_state.get_pending_policies()
            
            # Build prompt with pending policies
            system_prompt = self._get_system_prompt(pending)
            history_text = self._format_history()
            full_prompt = f"{system_prompt}\n\nCONVERSATION:\n{history_text}\n\nASSISTANT:"
            
            # Call LLM
            debug_log(f"Turn {tool_turn_count + 1}: Pending={pending}")
            response = self.llm.call(messages=[{"role": "user", "content": full_prompt}])
            
            # Check for tool usage
            code = self._extract_code(response)
            
            if code:
                # Identify tool
                tool_name = "UNKNOWN"
                if "knowledge_base_read" in code:
                    tool_name = "KB_READ"
                elif "knowledge_base_write" in code:
                    tool_name = "KB_WRITE"
                elif "federated_search" in code:
                    tool_name = "SEARCH"
                elif "fetch" in code:
                    tool_name = "FETCH"
                
                debug_log(f"Tool Call: {tool_name}")
                tools_used.append(tool_name)
                
                if TESTING:
                    print(f"\n[TOOL: {tool_name}]\n{code}\n[/TOOL]\n")
                
                # Execute
                exec_result = execute_tool(code)
                
                stdout = exec_result.get('stdout', '')
                result = exec_result.get('result', '')
                error = exec_result.get('error', '')
                
                debug_log(f"Result: {str(result)[:200]}...")
                if error:
                    debug_log(f"Error: {error}")
                
                # Mark policy as satisfied
                policy_state.mark_satisfied(code)
                
                # Add to history
                tool_msg = f"TOOL_RESULT ({tool_name}):\n{stdout}\n{result}"
                if error:
                    tool_msg += f"\nError: {error}"
                
                self.history.append({"role": "assistant", "content": response})
                self.history.append({"role": "system", "content": tool_msg})
                
                # Reload KB if write occurred
                if tool_name == "KB_WRITE":
                    self.session.reload_metadata()
                    self.existing_topics = self.session.get_all_topic_names()
                    
                    # SPECIAL CASE: Post-Response KB Write
                    # If this was a KB_WRITE and there is substantial text BEFORE the code block,
                    # it means the agent answered AND updated the KB in one turn.
                    # We should return the text part to the user.
                    code_start_idx = response.find("```python")
                    if code_start_idx > 50: # Arbitrary threshold for "substantial text"
                        text_part = response[:code_start_idx].strip()
                        debug_log("Post-Response KB Write detected. Returning text to user.")
                        # Ensure we mark it as assistant response
                        # (Already added to history above)
                        return text_part
                
                tool_turn_count += 1
                
            else:
                # No code block - agent wants to give final response
                
                # CHECK: Are there still pending policies?
                remaining = policy_state.get_pending_policies()
                
                if remaining:
                    # FORCE another iteration - inject reminder
                    debug_log(f"Agent tried to respond but policies still pending: {remaining}")
                    reminder = f"SYSTEM: You cannot respond yet. Pending policies: {remaining}. Output a code block."
                    self.history.append({"role": "system", "content": reminder})
                    tool_turn_count += 1
                    continue
                
                # All policies satisfied - accept response
                debug_log(f"Final response after {len(tools_used)} tool(s): {tools_used}")
                self.history.append({"role": "assistant", "content": response})
                return response
        
        return "I apologize, I got stuck. Let's try again."

    def set_topic(self, topic: str) -> None:
        """Set current topic via normalizer."""
        canonical, _, _ = normalize_topic(topic, self.existing_topics)
        self.session.set_current_topic(canonical)


def create_tutor() -> TutorAgent:
    return TutorAgent()
