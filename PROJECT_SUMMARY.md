# Curalink: Premium Agentic Medical Research Workstation 🏥🔬🛡️

## 1. Executive Summary
Curalink is a professional-grade clinical research platform that transforms a basic LLM into a **Grounded Medical Director**. Unlike standard RAG systems, Curalink utilizes a **Multi-Stage Neural Pipeline** to ensure that every clinical briefing is backed by validated, full-text research while maintaining a persistent session-wide knowledge archive.

---

## 2. Core Architectural Pillars

### A. The Neural Pivot (Intelligent Routing)
The brain of Curalink is its **Stage 0 Intent Classifier**.
- **The Librarian (Deep Dive)**: For follow-up questions, the agent scans its **Local Archive** (MongoDB) to find answers in papers already "read" during the session.
- **The Scout (New Search)**: If the local archive has a "Data Gap" or if the user introduces a novel clinical term (e.g., a specific acronym like **FMT**), the system **automatically pivots** to a global internet search to ensure no data is missed.

### B. Two-Stage Retrieval Engine
- **Stage 1 (High Recall)**: Rapidly scans **PubMed**, **OpenAlex**, and **ClinicalTrials.gov** purely for titles and dates to build a candidate list.
- **Stage 2 (High Precision)**: Selective fetch of abstracts and **Full-Text PMC Articles** for the most relevant matches.

### C. JIT-RAG (Just-In-Time RAG)
Traditional RAG is static; Curalink is dynamic.
- **Nomic-Embed-Text-v1.5**: Our embedding layer performs real-time semantic ranking of paper chunks.
- **Semantic Chunking**: Long clinical reports are broken down, and only the most relevant "Gold Passages" are fed into the LLM's context window.

### D. Cumulative Knowledge Archive
Every unique paper found during the session is stored in **MongoDB Atlas**. This turns the session into a "Compiling Textbook" where the AI becomes increasingly knowledgeable as the conversation progresses.

---

## 3. Clinical Ranking & Heuristics (The Scoring Method)
The workstation uses a deterministic weighted scoring system to prioritize research. Every paper starts with a score of 0, and keywords are applied with the following weights:

### A. The Disease Shield (Condition Matching)
- **Primary Match (Title)**: **+50 Points**. If the disease name (or its fuzzy root like 'Parkinson') appears in the title.
- **Secondary Match (Abstract)**: **+20 Points**. If mentioned in the summary text.
- **Pollution Penalty**: **-50 Points**. If the disease is missing entirely (effectively burying unrelated research).

### B. Dynamic Keyword Overlap
Matches between your specific query (e.g., 'deep brain stimulation') and the paper are weighted by location:
- **Title Overlap**: **3x Multiplier**.
- **Abstract Overlap**: **1x Multiplier**.
This ensures that papers with the specific topic in their name rise to the top of the "Evidence" list.

### C. Recency Boost
Medical research evolves rapidly. Curalink applies a "Decay Bonus":
- **Current Year**: **+5 Points**.
- **Last 2 Years**: **+3 Points**.
- **Last 5 Years**: **+1 Point**.

### D. The Pivot Threshold
For follow-up questions (**Deep Dives**), the system requires at least one paper to have a total score of **15+**. If no local paper hits this threshold, it triggers an **Auto-Search Pivot** to find fresh data.

---

## 4. Safety & Grounding Protocols
To ensure clinical safety, the system implements **Nuclear Grounding**:
1. **Fuzzy Disease Shield**: A regex-based filter that blocks "Conditions Pollution" (e.g., preventing accounting or climate papers from appearing in a Parkinson's workspace).
2. **Zero-Hallucination Mandate**: If no valid papers are found, the AI is strictly forbidden from giving tips. It will prioritize an honest "Search Gap Detected" message over a hallucinated answer.
3. **Token Hardening**: Aggressive character-to-token budgeting ensures complex clinical data never exceeds the hardware's context limits (Error 400 prevention).

---

## 4. User Experience Design
- **Agent Reasoning Sidebar**: A real-time log of the agent's internal technical decisions (Routing, Ranking, Scaling).
- **Validated Evidence Panel**: A "Reference Library" where users can click to open original source DOIs.
- **Glassmorphic UI**: A premium, high-contrast dark mode designed for focused medical analysis.

---

## 5. Technical Stack
- **AI Core**: LangChain + LM Studio (Qwen 2.5 3B / Nomic Embeddings).
- **Backend**: FastAPI (Python) + MongoDB Atlas.
- **Frontend**: React (Vite) + Framer Motion + Lucide Icons.

---
**Status**: Production Hardened 🏥🚀🛡️
