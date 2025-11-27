import json
from pathlib import Path
from datetime import datetime, timezone
from crewai.tools import tool

@tool
def kb_update(topic: str,
                       mastery: float = None,
                       confidence: float = None,
                       reason: str = "",
                       source: str = "agent"):
    """
    Updates ONLY the knowledge metadata for a topic.
    Does NOT handle notes — notes must be written using kb_write_note.
    You MUST consider using this tool after presenting any piece of information to the user.
    Use this ESPECIALLY when you detect learning, correct a misconception,
    provide the user with any information, or the user tells you something new.

    Args:
        topic (str): Name of the topic (e.g., 'biology')
        mastery (float): Optional new mastery level
        confidence (float): Optional new confidence level
        reason (str): Reason for update (logged to timeline)
        source (str): 'agent' or 'user'

    Returns:
        dict: Status information
    """

    # Paths
    base_dir = Path(__file__).parent.parent
    knowledge_dir = base_dir / "knowledge"
    profile_path = knowledge_dir / "profile.json"
    timeline_path = knowledge_dir / "timeline.json"

    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Load or create profile
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except:
            profile = {"updated_at": None, "topics": {}}
    else:
        profile = {"updated_at": None, "topics": {}}

    if "topics" not in profile:
        profile["topics"] = {}

    # Topic entry
    topic_entry = profile["topics"].get(topic, {})

    changes = []

    if mastery is not None:
        mastery = float(max(0, min(10, mastery)))
        old = topic_entry.get("mastery")
        if old != mastery:
            topic_entry["mastery"] = mastery
            changes.append(("mastery", old, mastery))

    if confidence is not None:
        confidence = float(max(0, min(10, confidence)))
        old = topic_entry.get("confidence")
        if old != confidence:
            topic_entry["confidence"] = confidence
            changes.append(("confidence", old, confidence))

    if changes:
        topic_entry["last_reviewed"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        profile["topics"][topic] = topic_entry
        profile["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    # Timeline logging
    if changes:
        if timeline_path.exists():
            try:
                timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            except:
                timeline = []
        else:
            timeline = []

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for (field, old, new) in changes:
            timeline.append({
                "timestamp": ts,
                "event": "metadata_update",
                "topic": topic,
                "field": field,
                "old_value": old,
                "new_value": new,
                "reason": reason,
                "source": source
            })

        timeline_path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "topic": topic,
        "message": "Updated fields: " + ", ".join([c[0] for c in changes]) if changes else "No changes"
    }
