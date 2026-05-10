import asyncio
import threading
import httpx
from typing import List, Optional

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.config import settings

from google import genai
from app.config.config import settings

# Initialize Gemini Client
_genai_client = None
if settings.GEMINI_API_KEY:
    _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

def _get_genai_client():
    global _genai_client
    if _genai_client is None and settings.GEMINI_API_KEY:
        _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _genai_client

def preload_local_embedding_model() -> None:
    """No-op for Gemini as it is a cloud API."""
    pass

async def get_embeddings(text_list: List[str]) -> List[List[float]]:
    """Fetches embeddings using Gemini API."""
    client = _get_genai_client()
    if not client:
        print("Gemini API Key missing. Falling back to empty embeddings.")
        return []

    try:
        # Gemini embedding-004 is the state of the art for medical retrieval
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text_list
        )
        # Handle both single and batch results
        if hasattr(result.embeddings, '__iter__'):
            return [e.values for e in result.embeddings]
        return [result.embeddings.values]
    except Exception as e:
        print(f"Gemini Embedding failed: {e}")
        return []


def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


async def get_top_chunks(query: str, full_text: str, top_k: int = 5) -> str:
    """Chunks a long text and returns the most semantically relevant parts."""
    if not full_text:
        return ""

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)

    if len(chunks) <= top_k:
        return "\n---\n".join(chunks)

    all_texts = [query] + chunks
    embeddings = await get_embeddings(all_texts)

    if not embeddings:
        print("Falling back to keyword-based chunking...")
        query_words = set(query.lower().split())
        scored_chunks = []
        for c in chunks:
            score = len(query_words.intersection(set(c.lower().split())))
            scored_chunks.append((score, c))
        ranked = sorted(scored_chunks, key=lambda x: x[0], reverse=True)
        return "\n---\n".join([c[1] for c in ranked[:top_k]])

    query_vec = embeddings[0]
    chunk_vecs = embeddings[1:]

    scored_chunks = []
    for i, vec in enumerate(chunk_vecs):
        score = cosine_similarity(query_vec, vec)
        scored_chunks.append((score, chunks[i]))

    ranked = sorted(scored_chunks, key=lambda x: x[0], reverse=True)
    return "\n---\n".join([c[1] for c in ranked[:top_k]])
