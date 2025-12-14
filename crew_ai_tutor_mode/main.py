# main.py
# Ignore this file, it's outdated
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
from prompts import get_task_description, get_expected_output

# ————————————————————————————————
# 1. Create the Tutor Agent (with memory of YOU)
# ————————————————————————————————
tutor = create_tutor_agent()

# ————————————————————————————————
# 2. The Master Task — This is where the magic happens
# ————————————————————————————————
task = Task(
    description=get_task_description(),
    expected_output=get_expected_output(),

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