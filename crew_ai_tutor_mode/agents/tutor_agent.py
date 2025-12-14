# agents/tutor_agent.py
import os
from crewai import Agent, LLM
from tools.knowledge_base_read import knowledge_base_read
from tools.knowledge_base_write import knowledge_base_write
from tools.federated_search import federated_search


from tools.rank_documents import rank_documents  # your e5-base-v2 ranker
from tools.summarize import summarize
from tools.persist import persist
from prompts import TUTOR_ROLE, TUTOR_GOAL, TUTOR_BACKSTORY

# ——— LLMs ———
# High-quality for final summaries (optional — you can swap to Groq too)
GPT_LLM = LLM(model="gpt-4.1-mini")


def create_tutor_agent():
    """
    Creates and returns the personal AI Tutor agent.
    This agent knows you, adapts to you, and grows with you.
    """
    # One-time knowledge injection at session start
    print("Tutor: Booting up... downloading your entire life mistakes...")
    # Use .func to call the tool function directly
    knowledge = knowledge_base_read.func().get("profile", {})
    
    topics_summary = "\n".join(
        f"• {topic}: {data['mastery']}/10 (confidence {data['confidence']}) — {data.get('notes','')}"
        for topic, data in knowledge.get("topics", {}).items()
    ) or "• (nothing yet — you’re a blank slate, scary)"

    final_backstory = f"""{TUTOR_BACKSTORY}

CURRENT BRAIN SNAPSHOT:
{topics_summary}
"""

    agent = Agent(
        role=TUTOR_ROLE,
        goal=TUTOR_GOAL,
        backstory=final_backstory,
        
        tools=[
            knowledge_base_read,  # Unified knowledge base read tool
            knowledge_base_write, # Unified knowledge base write tool
            federated_search,

            rank_documents,   # ← e5-base-v2 relevance ranking
            summarize,
            persist,
        ],
        
        llm=GPT_LLM,        # Fast + tool-calling reliable
        verbose=True,
        allow_delegation=False,
        memory=True,         # CrewAI built-in short-term memory
        step_callback=None   # we can add logging later
    )

    print("Tutor: Alright, I know everything. Hit me with your next obsession.")
    return agent