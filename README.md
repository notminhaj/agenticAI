# 🧠 AI Research Tutor — Autonomous Multi-Tool Agent (V1)

An AI-native autonomous system that discovers, filters, ranks, and summarizes the latest AI content — **personalized to the user's evolving knowledge**.  
This project explores workflow orchestration, agentic behavior, MCP integration, neural ranking models, and adaptive knowledge bases.

Built over a 3-week deep dive into agent systems, with a strong focus on learning through experimentation, debugging, and pushing tools past their comfort zones.

---

# 🚀 Overview

The AI Research Tutor is an **end-to-end agentic pipeline** that:

1. **Searches multiple sources**  
   - arXiv API  
   - Brave Search MCP (web + news)  
   - Extendable to other sources (blogs, posts, articles)  

2. **Fetches & cleans content**  
   - HTML extraction  
   - PDF → abstract auto-redirect  
   - Script/style stripping  
   - Fallback parsing logic  

3. **Ranks relevance using a neural model**  
   - Uses `intfloat/e5-base-v2` embeddings  
   - Scores content against a target topic  
   - Provides reliable multi-document ranking  

4. **Summarizes top results with LLMs**  
   - GPT-4.1-mini (configurable)  
   - Structure-aware summaries  
   - Error handling + retry logic  

5. **Personalizes output using a Knowledge Base**  
   - Agent can **read** and **write** to the KB  
   - Tracks user expertise, gaps, and learning history  
   - Summaries adapt to the user’s level  

6. **Logs a full learning timeline**  
   - Every run is stored as Markdown + JSON  
   - Includes metadata, rankings, summaries, and KB updates  

---

# 🧩 System Architecture


### **Workflow Mode**
Deterministic pipeline for reliability and cost control.  
Good for batch processing or scheduled runs.

### **Agent Mode**
CrewAI agent decides:
- how many papers to fetch  
- which search source to use  
- when to call tools  
- how to update the knowledge base  

### **NN Mode**
Neural network scoring ensures:
- low-quality papers are filtered  
- the agent only summarizes the most relevant content  
- token usage stays efficient  

### **Knowledge Base Mode**
A JSON-based persistent profile storing:
- current skill level  
- known topics  
- knowledge gaps  
- learning history  
- agent updates after every run  

This allows the agent to **adapt explanations, simplify content, or get more technical depending on the user.**

---

# 🛠️ Key Technologies

- **CrewAI** — Agent framework + tool routing  
- **OpenAI API** — LLM reasoning + summarization  
- **Brave Search MCP** — Multi-source content discovery  
- **BeautifulSoup4** — HTML parsing & text cleaning  
- **E5 Neural Embeddings** — Semantic ranking of documents  
- **Python 3.12** — Main runtime  
- **Cursor** — AI-assisted development and iteration  
- **JSON + Markdown** — Persistent logs + human-readable summaries  

---

# ⚡ Highlights & Learnings

Building this system required navigating real-world difficulties, including:

- Knowledge-base synchronization  
- Tool hallucination  
- Prompt inheritance issues  
- Model inconsistency across tasks  
- Ranking failures with BART-based classifiers  
- HTML extraction edge cases  
- Agents ignoring tools / losing goals  
- CrewAI task-structure quirks  
- Handling empty or low-quality fetches  
- PDF → HTML redirect logic  

Each pain point drove a new iteration:
- **Workflow Mode** to stabilize execution  
- **NN Mode** to improve ranking  
- **Knowledge Base Mode** to personalize learning  
- **Brave MCP integration** to expand content sources  
- **Agent Mode** to explore tool orchestration  

This project grew naturally from friction — not planning — and that shaping-by-constraint is part of its design philosophy.

---


