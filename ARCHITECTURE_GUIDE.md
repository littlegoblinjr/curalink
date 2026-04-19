# CuraLink Architecture: Technical Overview for Loom Demo 🎥🧠

This document provides a structured script and breakdown for your hackathon video submission.

---

## 🏗️ 1. The Core Innovation: "Neural Briefing" Loop
Explain that CuraLink isn't just a RAG system—it's an **Autonomous Medical Researcher**.
- **The Problem**: Abstracts are often too short.
- **The Solution**: **JIT-RAG** (Just-In-Time Retrieval-Augmented Generation). We fetch full-text PMC articles in real-time and semantically chunk them using **Nomic-Embed-Text-v1.5**.

## 🧠 2. The Intelligence Layer: "Neural Pivot"
Showcase how the system thinks:
- **Librarian (Deep Dive)**: If you ask a follow-up, it scans the session's **MongoDB Archive** first for instant answers.
- **Scout (Search Fallback)**: If it detects a "Search Gap" (like a new clinical term FMT), it pivots automatically to **PubMed** and **OpenAlex**.

## 🛡️ 3. Safety & Grounding
High-fidelity research requires strict rules:
- **Fuzzy Disease Shield**: Prevents "Data Pollution" from unrelated medical branches.
- **Nuclear Grounding**: The AI is strictly forbidden from hallucinating; it will report a "Search Gap" rather than giving hypothetical advice.

## ⚙️ 4. The Stack
- **Frontend**: React + Framer Motion + Lucide (Premium Glassmorphic UI).
- **Backend**: FastAPI (Python) for heavy-duty RAG processing.
- **Database**: MongoDB Atlas (Persistent Archive).
- **LLM**: Qwen 2.5 (Local via LM Studio) for sovereign data privacy.

---

## 🧪 Demo Script (Suggested Flow)
1. **Initial Search**: Ask "Latest Parkinson's treatment." Show the **Stage 1 (High Recall)** search hits.
2. **Deep Dive**: Follow up with a specific detail (e.g., "What about the gut-brain axis?"). Watch the agent choose **DEEP DIVE** mode.
3. **The Pivot**: Ask about a new term like "FMT." Explain how the agent realized the term was new and triggered a **NEW SEARCH** automatically.
4. **Source View**: Click on an Evidence Card. Show the metadata including **Authors**, **Recruiting Status**, and **Location**.

---
**Hackathon Tip**: Emphasize how we handle 300+ candidate results from 3 APIs (PubMed, OpenAlex, ClinicalTrials.gov) and distill them down to the top 8 with weighted ranking.
