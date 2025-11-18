# agents/tutor_agent.py
import os
from crewai import Agent, LLM
from tools.knowledge_base_read import kb_read
from tools.knowledge_base_update import kb_update
from tools.search import search
from tools.fetch import fetch
from tools.rank_documents import rank_documents  # your e5-base-v2 ranker
from tools.summarize import summarize
from tools.persist import persist

# ——— LLMs ———
# Fast & free for reasoning + tool use
GROQ_LLM = LLM(
    model="llama-3.2-90b-vision-preview",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

# High-quality for final summaries (optional — you can swap to Groq too)
GPT_LLM = LLM(model="gpt-4.1-mini")


def create_tutor_agent():
    """
    Creates and returns the personal AI Tutor agent.
    This agent knows you, adapts to you, and grows with you.
    """
    return Agent(
        role="Ehsan's Personal AI Tutor",
        goal="""Accelerate Ehsan's mastery of Agentic AI and related fields
                by delivering perfectly targeted, sarcastic, high-signal learning
                experiences — every single week.""",
        backstory="""You have been Ehsan's invisible co-pilot for months.
        You know his strengths (tool calling = god-tier), his blind spots (advanced RAG = ouch),
        and his learning style (sarcastic, hates fluff, loves deep rabbit holes).
        You never waste his time with basics he already knows.
        You roast bad papers. You celebrate his wins. You are brutally effective.""",
        
        tools=[
            kb_read,          # ← reads his brain
            kb_update,        # ← writes to his brain
            search,
            fetch,
            rank_documents,   # ← e5-base-v2 relevance ranking
            summarize,
            persist
        ],
        
        llm=GPT_LLM,        # Fast + tool-calling reliable
        verbose=True,
        allow_delegation=False,
        memory=True,         # CrewAI built-in short-term memory
        step_callback=None   # we can add logging later
    )