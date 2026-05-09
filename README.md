# 🏥 CuraLink: Advanced Medical Intelligence Protocol

CuraLink is a next-generation, agentic medical research workstation built specifically for rapid, evidence-grounded clinical briefings. It intelligently queries massive medical databases and dynamically builds concise, reliable summaries evaluated strictly by LLM-as-a-Judge safeguards.

---

## ⚡ Core Architecture

* **Multi-Vector Live Retrieval**: Concurrently runs high-speed searches against **PubMed**, **OpenAlex**, and **ClinicalTrials.gov** to aggregate massive caches of peer-reviewed clinical data.
* **LLM-as-a-Judge Guardrails**: Eliminates hallucination risk. Every generated medical briefing is passed through a **Ragas Verification Pipeline** that rigorously validates algorithmic *Faithfulness* and *Answer Relevancy* against the raw source evidence before delivery.
* **Dynamic Smart Streaming**: Built-in Newline-Delimited JSON (NDJSON) engine that streams LLM tokens actively to the screen via a 60fps buffer.
* **Neo-Glassmorphism UI**: High-fidelity, ultra-premium web dashboard featuring ambient mesh layouts, seamless "Thinking" logs, smart-scrolling, and inline validated source grids.

---

## 🛠️ Tech Stack 

- **Frontend**: React, Vite, Framer Motion, Vanilla CSS (Custom Aesthetic)
- **Backend / API**: FastAPI, Python 3.10+, Uvicorn 
- **LLM Routing / RAG**: LangChain, Local Embeddings, Groq Acceleration
- **Evaluation Engine**: Ragas (faithfulness checks)
- **Database Architecture**: Motor (Async IO), MongoDB Atlas / Memory Fallbacks
- **Deployment**: Docker, Hugging Face Spaces

---

## 🚀 Quick Start & Deployment

CuraLink has been specifically structured for rapid containerized deployment.

1. Configure backend environment keys (`.env`).
2. Build the standalone Docker image.
3. Access the unified application matrix locally or deploy externally via Hugging Face.

---

### *A CuraLink Hackathon Submission* 🛰️
