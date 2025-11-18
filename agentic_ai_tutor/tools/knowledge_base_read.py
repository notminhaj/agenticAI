import json
from pathlib import Path
from typing import Dict, Any, List
from crewai.tools import tool

@tool
def kb_read() -> Dict[str, Any]:
    """
    Reads the user's current knowledge profile and recent learning timeline. 
    Use this at the start of every session to understand what the user already knows and what they need to learn.
    
    Returns:
        dict: Knowledge base data containing:
            - profile (dict): Full content of profile.json with user's knowledge topics and mastery levels
            - recent_events (list): Last 10 events from timeline.json (most recent first)
            - status (str): "success", "partial", or "error"
            - message (str): Optional human-readable note about the operation
            
    Note:
        If files don't exist or are malformed, returns empty defaults with appropriate status.
        Never crashes the agent - always returns a valid dictionary.
    """
    # Get the base directory (agentic_ai_tutor folder)
    base_dir = Path(__file__).parent.parent
    profile_path = base_dir / "knowledge" / "profile.json"
    timeline_path = base_dir / "knowledge" / "timeline.json"
    
    profile_data = {}
    timeline_data = []
    status = "success"
    messages = []
    
    # Load profile.json
    if not profile_path.exists():
        messages.append(f"Profile file not found: {profile_path}")
        status = "partial" if status == "success" else "error"
        profile_data = {"updated_at": None, "topics": {}}
    else:
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        except json.JSONDecodeError as e:
            messages.append(f"Profile JSON is malformed: {str(e)}")
            status = "error"
            profile_data = {"updated_at": None, "topics": {}}
        except Exception as e:
            messages.append(f"Error reading profile: {str(e)}")
            status = "error"
            profile_data = {"updated_at": None, "topics": {}}
    
    # Load timeline.json
    if not timeline_path.exists():
        messages.append(f"Timeline file not found: {timeline_path}")
        status = "partial" if status == "success" else "error"
        timeline_data = []
    else:
        try:
            with open(timeline_path, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
                
            # Ensure timeline_data is a list
            if not isinstance(timeline_data, list):
                messages.append("Timeline data is not a list, returning empty")
                timeline_data = []
            else:
                # Sort by timestamp (most recent first) and take last 10
                # Events are already in chronological order (oldest to newest)
                # So we take the last 10 and reverse to get most recent first
                sorted_events = sorted(
                    timeline_data,
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )
                timeline_data = sorted_events[:10]
                
        except json.JSONDecodeError as e:
            messages.append(f"Timeline JSON is malformed: {str(e)}")
            status = "error"
            timeline_data = []
        except Exception as e:
            messages.append(f"Error reading timeline: {str(e)}")
            status = "error"
            timeline_data = []
    
    # Build result dictionary
    result = {
        "profile": profile_data,
        "recent_events": timeline_data,
        "status": status,
        "message": "; ".join(messages) if messages else None
    }
    
    return result

