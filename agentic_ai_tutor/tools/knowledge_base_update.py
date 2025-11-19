import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from crewai.tools import tool

@tool
def kb_update(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates the user's knowledge profile with new mastery levels, confidence, notes, or new topics. 
    Also logs the change to timeline.json for full history.
    You MUST consider using this tool after coming up with any response you might be considering presenting to the user.
    Use this ESPECIALLY when you detect learning, correct a misconception,
    provide the user with any information, or the user tells you something new.
    
    Args:
        updates (dict): Dictionary containing at least:
            - topic (str, required): The topic name to update
            - mastery (float, optional): Mastery level (0-10)
            - confidence (float, optional): Confidence level (0-10)
            - notes (str, optional): Notes about the topic
            - reason (str, optional): Reason for the update (for timeline)
            - source (str, optional): "agent" or "user" (default: "agent")
    
    Returns:
        dict: Update result containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - updated_topic (str): The topic that was updated
            
    Note:
        If topic doesn't exist, it will be created with default values.
        Only provided fields will be updated (others remain unchanged).
        Never crashes - always returns a valid dictionary.
    """
    # Get the base directory (agentic_ai_tutor folder)
    base_dir = Path(__file__).parent.parent
    knowledge_dir = base_dir / "knowledge"
    profile_path = knowledge_dir / "profile.json"
    timeline_path = knowledge_dir / "timeline.json"
    
    # Validate required fields
    if not isinstance(updates, dict):
        return {
            "status": "error",
            "message": "Updates must be a dictionary",
            "updated_topic": None
        }
    
    topic = updates.get("topic")
    if not topic or not isinstance(topic, str):
        return {
            "status": "error",
            "message": "Topic is required and must be a string",
            "updated_topic": None
        }
    
    # Ensure knowledge directory exists
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # Load current profile
    if profile_path.exists():
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        except json.JSONDecodeError:
            # If JSON is corrupted, start fresh
            profile_data = {"updated_at": None, "topics": {}}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error reading profile: {str(e)}",
                "updated_topic": topic
            }
    else:
        profile_data = {"updated_at": None, "topics": {}}
    
    # Ensure topics dict exists
    if "topics" not in profile_data:
        profile_data["topics"] = {}
    
    # Get or create topic entry (preserve original topic name as key)
    topic_entry = profile_data["topics"].get(topic, {})
    
    # Track which fields changed
    changes = []
    
    # Update mastery if provided
    if "mastery" in updates:
        new_mastery = updates["mastery"]
        if isinstance(new_mastery, (int, float)):
            new_mastery = float(new_mastery)
            # Clamp to 0-10 range
            new_mastery = max(0.0, min(10.0, new_mastery))
            old_mastery = topic_entry.get("mastery")
            if old_mastery != new_mastery:
                topic_entry["mastery"] = new_mastery
                changes.append({
                    "field": "mastery",
                    "old_value": old_mastery,
                    "new_value": new_mastery
                })
    
    # Update confidence if provided
    if "confidence" in updates:
        new_confidence = updates["confidence"]
        if isinstance(new_confidence, (int, float)):
            new_confidence = float(new_confidence)
            # Clamp to 0-10 range
            new_confidence = max(0.0, min(10.0, new_confidence))
            old_confidence = topic_entry.get("confidence")
            if old_confidence != new_confidence:
                topic_entry["confidence"] = new_confidence
                changes.append({
                    "field": "confidence",
                    "old_value": old_confidence,
                    "new_value": new_confidence
                })
    
    # Update notes if provided
    if "notes" in updates:
        new_notes = updates.get("notes")
        if isinstance(new_notes, str):
            old_notes = topic_entry.get("notes")
            if old_notes != new_notes:
                topic_entry["notes"] = new_notes
                changes.append({
                    "field": "notes",
                    "old_value": old_notes,
                    "new_value": new_notes
                })
    
    # Update last_reviewed to today if any field changed
    if changes:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        topic_entry["last_reviewed"] = today
    
    # Save updated topic back to profile
    profile_data["topics"][topic] = topic_entry
    
    # Update profile timestamp
    profile_data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Save profile.json
    try:
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error saving profile: {str(e)}",
            "updated_topic": topic
        }
    
    # Load timeline for logging
    if timeline_path.exists():
        try:
            with open(timeline_path, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
            if not isinstance(timeline_data, list):
                timeline_data = []
        except (json.JSONDecodeError, Exception):
            timeline_data = []
    else:
        timeline_data = []
    
    # Append timeline events for each change
    reason = updates.get("reason", "Knowledge profile updated")
    source = updates.get("source", "agent")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    for change in changes:
        event = {
            "timestamp": timestamp,
            "event": "knowledge_update",
            "topic": topic,
            "field": change["field"],
            "old_value": change["old_value"],
            "new_value": change["new_value"],
            "reason": reason,
            "source": source
        }
        timeline_data.append(event)
    
    # Save timeline.json
    if changes:
        try:
            with open(timeline_path, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Profile was saved, but timeline failed - still return success with warning
            return {
                "status": "success",
                "message": f"Profile updated, but timeline logging failed: {str(e)}",
                "updated_topic": topic
            }
    
    # Return success
    if changes:
        fields_updated = [c["field"] for c in changes]
        message = f"Updated {topic}: {', '.join(fields_updated)}"
    else:
        message = f"No changes made to {topic} (values unchanged or invalid)"
    
    return {
        "status": "success",
        "message": message,
        "updated_topic": topic
    }

