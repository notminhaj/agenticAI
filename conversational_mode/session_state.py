"""
Session State - Manages conversation state and KB metadata caching.

This module provides:
1. SessionState class that caches KB metadata at session start
2. Tracks current topic and topics already read/written
3. Prevents duplicate KB reads within the same topic

Usage:
    state = SessionState()  # Loads KB metadata
    state.set_current_topic("Agentic AI")
    state.mark_topic_read("Agentic AI")
"""

import json
from pathlib import Path
from typing import Dict, Any, Set, Optional
from datetime import datetime

# Constants
ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "knowledge_base" / "kb_metadata.json"


class SessionState:
    """
    Manages conversation session state including KB metadata caching.
    
    SESSION INITIALIZATION POLICY:
    - KB metadata is loaded once at session start
    - The metadata (topics, mastery, confidence) is cached in memory
    - This avoids repeated KB reads just to know what topics exist
    
    KB READ POLICY:
    - Only read full topic details when user shows interest in a specific topic
    - Track which topics have been read to avoid re-reading
    
    KB WRITE POLICY:
    - Track which topics have been written to avoid duplicate writes
    - The agent decides absolute mastery/confidence values (educated guess)
    """
    
    def __init__(self):
        """Initialize session and load KB metadata."""
        self.kb_metadata: Dict[str, Any] = {}
        self.current_topic: Optional[str] = None
        self.topics_read: Set[str] = set()
        self.topics_written: Set[str] = set()
        self.session_start: datetime = datetime.now()
        
        # Load KB metadata at session start
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load KB metadata from disk (called once at session start)."""
        if not METADATA_PATH.exists():
            self.kb_metadata = {"updated_at": None, "topics": {}}
            return
        
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                self.kb_metadata = json.load(f)
        except Exception as e:
            print(f"[SessionState] Error loading KB metadata: {e}")
            self.kb_metadata = {"updated_at": None, "topics": {}}
    
    def reload_metadata(self) -> None:
        """Force reload KB metadata (e.g., after a write)."""
        self._load_metadata()
    
    def get_topic_summary(self) -> str:
        """
        Get a formatted summary of all topics for injection into system prompt.
        Returns a concise string with topic names and mastery levels.
        """
        topics = self.kb_metadata.get("topics", {})
        if not topics:
            return "No topics in knowledge base yet."
        
        lines = []
        for topic, data in topics.items():
            mastery = data.get("mastery", 0)
            confidence = data.get("confidence", 0)
            last_reviewed = data.get("last_reviewed", "never")
            lines.append(f"- {topic}: mastery={mastery}/10, confidence={confidence}/10, last_reviewed={last_reviewed}")
        
        return "\n".join(lines)
    
    def get_topic_info(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get cached info for a specific topic (without calling KB read)."""
        topics = self.kb_metadata.get("topics", {})
        # Case-insensitive lookup
        for t, data in topics.items():
            if t.lower() == topic.lower():
                return {"name": t, **data}
        return None
    
    def get_all_topic_names(self) -> list:
        """Get list of all topic names in KB."""
        return list(self.kb_metadata.get("topics", {}).keys())
    
    def set_current_topic(self, topic: str) -> None:
        """Set the current topic being discussed."""
        self.current_topic = topic
    
    def get_current_topic(self) -> Optional[str]:
        """Get the current topic being discussed."""
        return self.current_topic
    
    def should_read_topic(self, topic: str) -> bool:
        """
        Check if we should call KB read for this topic.
        Returns True if topic hasn't been read this session.
        """
        return topic.lower() not in {t.lower() for t in self.topics_read}
    
    def mark_topic_read(self, topic: str) -> None:
        """Mark a topic as having been read this session."""
        self.topics_read.add(topic)
    
    def mark_topic_written(self, topic: str) -> None:
        """Mark a topic as having been written this session."""
        self.topics_written.add(topic)
    
    def has_written_topic(self, topic: str) -> bool:
        """Check if we've already written to this topic this session."""
        return topic.lower() in {t.lower() for t in self.topics_written}


def create_session() -> SessionState:
    """Factory function to create a new session."""
    return SessionState()


if __name__ == "__main__":
    # Quick test
    print("Session State Test")
    print("=" * 60)
    
    state = SessionState()
    print(f"Session started at: {state.session_start}")
    print(f"Topics loaded: {len(state.get_all_topic_names())}")
    print()
    print("Topic Summary (for system prompt):")
    print(state.get_topic_summary())
