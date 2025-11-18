# main.py
import os
from datetime import datetime
from crewai import Task, Crew
from agents.tutor_agent import create_tutor_agent
from config import (
    MAIN_TOPIC,
    PAPERS_TO_FETCH,
    TOP_K_TO_SUMMARIZE,
    INCLUDE_QUIZ,
    INCLUDE_RECOMMENDATIONS
)

# ————————————————————————————————
# 1. Create the Tutor Agent (with memory of YOU)
# ————————————————————————————————
tutor = create_tutor_agent()

# ————————————————————————————————
# 2. The Master Task — This is where the magic happens
# ————————————————————————————————
task = Task(
    description=f"""
You are running Ehsan's weekly AI tutor session on: {MAIN_TOPIC}

STRICT INSTRUCTIONS — FOLLOW THIS FLOW EXACTLY:

1. Call `kb_read()` IMMEDIATELY → understand current mastery, gaps, and learning history.
2. Identify 1–3 topics where mastery < 7.0 (or confidence is dropping).
3. Search arXiv for the most relevant, recent papers on those topics + the main topic.
   → Fetch up to {PAPERS_TO_FETCH} papers.
4. Use `rank_documents` with e5-base-v2 to rank by relevance to Ehsan's gaps.
5. Take only the top {TOP_K_TO_SUMMARIZE} papers.
6. Summarize each one in <200 words:
   - Skip basics he already knows
   - Use analogies he loves
   - Be sarcastic about bad papers
   - Highlight connections to his existing knowledge
7. Generate a weekly brief in markdown.
8. If {INCLUDE_QUIZ}: Add 3–5 quiz questions (multiple choice + one open-ended).
9. If {INCLUDE_RECOMMENDATIONS}: Suggest next actions, papers, or micro-projects.
10. Use `kb_update()` for every topic where understanding improved.
11. Save everything with `persist()` → filename: weekly_brief_{datetime.now():%Y-%m-%d}.md

DO NOT hallucinate. DO NOT skip kb_read(). DO NOT explain basics he knows.
You are his mentor, not a textbook.
""",

    expected_output=f"""
A complete markdown file saved via persist() containing:

# Weekly AI Brief — {MAIN_TOPIC} — {datetime.now().strftime("%B %d, %Y")}

## Mastery Update
- Topic X: 3.0 → 6.5 (reason)

## Top {TOP_K_TO_SUMMARIZE} Papers This Week
1. [Title](url) → savage summary

## Key Insights

## Quiz (if enabled)

## Next Actions (if enabled)

File saved to output/ with timestamp.
Knowledge base automatically updated.
""",

    agent=tutor,
    async_execution=False,
    output_file=None  # persist() tool handles saving
)

# ————————————————————————————————
# 3. Launch the Crew — Your tutor wakes up
# ————————————————————————————————
crew = Crew(
    agents=[tutor],
    tasks=[task],
    verbose=True,  # See every tool call + reasoning
    memory=True,
    embedder=None  # Optional - set to None to use defaults
)

print(f"Launching Ehsan's AI Tutor — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"Focus topic: {MAIN_TOPIC}")
print(f"Fetching up to {PAPERS_TO_FETCH} papers → ranking → top {TOP_K_TO_SUMMARIZE} summarized\n")

result = crew.kickoff()

print("\n" + "="*60)
print("TUTOR SESSION COMPLETE")
print("="*60)
print(result)