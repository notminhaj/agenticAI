# 🧠 AI Research Tutor — Agentic Learning System

An evolving AI system designed to discover, filter, learn, and teach complex topics. This repository represents a journey from deterministic workflows to fully autonomous, conversational agents with long-term memory.

Current State: **Conversational Agent (V3)** is the active flagship implementation.

---

## 🚀 Quick Start
See [SETUP.md](SETUP.md) for installation and usage instructions.

---

## 🛠️ Key Technologies & Concepts

### 🧠 Knowledge Base (Long-term Memory)
The agent maintains a `knowledge_base.json` (and associated metadata) to track:
- **Topics Covered**: What concepts have been discussed.
- **Mastery Level**: The user's estimated understanding (Beginner, Intermediate, Advanced).
- **Refinement Policies**: The agent enforces a "Read-first, Write-later" policy to ensure memory consistency.

### 🔍 Federated Search
Instead of relying on a single search index, the `federated_search` tool:
1.  **Broadcasts** queries to multiple providers (Brave, Arxiv, Twitter/X).
2.  **Fetches** the full content of top results.
3.  **Ranks** them using a Neural or LLM-based reranker locally.
4.  **Synthesizes** a coherent context for the agent.

### 🤖 Agentic Patterns
- **Tool-use Enforcement**: Strict policies on when to use tools (e.g., "Don't guess; Search.").
- **Reflection**: The agent validates its own outputs against the Knowledge Base.

---

## 📂 Project Structure & Modes

This repository documents the evolution of the system through different "modes" of operation.

### 🔹 1. Conversational Mode (`/conversational_mode`)
**Subject:** *The Current State of the Art*
A fully interactive AI Tutor that maintains a persistent context of what you know.
- **Features**: 
  - **Federated Search**: Aggregates results from Brave, Arxiv, and other sources seamlessly.
  - **Knowledge Base Policies**: The agent checks what you *already know* before explaining, and *updates* its records after teaching you.
  - **Adaptive Conversation**: Detects topic shifts and deeper inquiries automatically.
- **Key Files**:
  - `tutor_agent.py`: The core agent logic and tool routing.
  - `tools/federated_search.py`: Advanced search-fetch-rank pipeline.
  - `knowledge_base/`: JSON-based memory of user mastery and covered topics.

### 🔹 2. Agent Mode (`/agent_mode`)
**Subject:** *Autonomous Task Execution*
An earlier iteration focused on autonomous task completion using the CrewAI framework.
- Uses independent agents to plan, search, and summarize.
- Good for "fire and forget" research tasks.

### 🔹 3. NN Mode (`/nn_mode`)
**Subject:** *Neural Information Retrieval*
Experiments in using Neural Networks (Embeddings, Cross-Encoders) to rank search results.
- Used to filter high-volume search noise before LLM processing.
- Implements `e5-base-v2` and other models for relevance scoring.

### 🔹 4. Workflow Mode (`/workflow_mode`)
**Subject:** *Deterministic Pipelines*
A linear, script-based approach to research.
- **Reliable**: No "agentic" decision making; just Step A -> Step B -> Step C.
- Useful for batch processing or when strict control is required.

---

## 📜 History & Philosophy

This project initially started as a simple script to summarize Arxiv papers. It grew into a study of **Agentic AI**:
1.  **Workflow Mode**: Solved the reliability problem using code.
2.  **Agent Mode**: solved the flexibility problem using CrewAI.
3.  **NN Mode**: Solved the "garbage-in/garbage-out" problem using Neural Retrieval.
4.  **Conversational Mode**: Solves the "User Alignment" problem by maintaining shared state/memory.
