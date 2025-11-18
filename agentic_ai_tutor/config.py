# config.py
# Your personal control panel — change these values before each run

# ————————————————————
# MAIN FOCUS
# ————————————————————
MAIN_TOPIC = "Agentic AI"                  # ← Change this weekly or per session
                                           # Examples: "advanced RAG", "self-healing agents", "Constitutional AI"

# ————————————————————
# PIPELINE SETTINGS
# ————————————————————
PAPERS_TO_FETCH = 5                       # How many raw papers to pull from arXiv
TOP_K_TO_SUMMARIZE = 3                     # Only the best ones go to the tutor

# ————————————————————
# OUTPUT OPTIONS
# ————————————————————
INCLUDE_QUIZ = True                        # Generate 3–5 questions to test you
INCLUDE_RECOMMENDATIONS = True             # Suggest next papers, projects, rabbit holes

# ————————————————————
# PATHS (don’t touch unless you restructure)
# ————————————————————
KNOWLEDGE_DIR = "knowledge"
OUTPUT_DIR = "output"

# ————————————————————
# MODEL PREFERENCES (optional — can override in tutor_agent.py)
# ————————————————————
USE_GROQ_FOR_SUMMARY = True                # False → uses gpt-4.1-mini for final summaries
AGENT_TEMPERATURE = 0.7                    # 0.0 = deterministic, 1.0 = creative chaos