# agents/tutor_agent.py
import os
from crewai import Agent, LLM
from tools.knowledge_base_read import kb_read
from tools.knowledge_base_update import kb_update
from tools.search import search
from tools.multi_source_search import multi_source_search
from tools.fetch import fetch
from tools.rank_documents import rank_documents  # your e5-base-v2 ranker
from tools.summarize import summarize
from tools.persist import persist
from tools.kb_search import semantic_note_search
from tools.kb_search import read_note
from prompts import TUTOR_ROLE, TUTOR_GOAL, TUTOR_BACKSTORY

# ——— LLMs ———
# High-quality for final summaries (optional — you can swap to Groq too)
GPT_LLM = LLM(model="gpt-4.1-mini")


def create_tutor_agent():
    """
    Creates and returns the personal AI Tutor agent.
    This agent knows you, adapts to you, and grows with you.
    """
    return Agent(
        role=TUTOR_ROLE,
        goal=TUTOR_GOAL,
        backstory=TUTOR_BACKSTORY,
        
        tools=[
            kb_read,          # ← reads his brain
            kb_update,        # ← writes to his brain
            multi_source_search,
            fetch,
            rank_documents,   # ← e5-base-v2 relevance ranking
            summarize,
            persist,
            semantic_note_search,
            read_note
        ],
        
        llm=GPT_LLM,        # Fast + tool-calling reliable
        verbose=True,
        allow_delegation=False,
        memory=True,         # CrewAI built-in short-term memory
        step_callback=None   # we can add logging later
    )

    # One-time knowledge injection at session start
    print("Tutor: Booting up... downloading your entire life mistakes...")
    knowledge = kb_read()
    topics_summary = "\n".join(
        f"• {topic}: {data['mastery']}/10 (confidence {data['confidence']}) — {data.get('notes','')}"
        for topic, data in knowledge.get("profile", {}).get("topics", {}).items()
    ) or "• (nothing yet — you’re a blank slate, scary)"

    agent.system_message = f"""{TUTOR_BACKSTORY}

CURRENT BRAIN SNAPSHOT:
{topics_summary}
"""

    print("Tutor: Alright, I know everything. Hit me with your next obsession.")
    return agent