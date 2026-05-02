import asyncio
import threading
import httpx
from typing import List, Optional

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.config import settings

_st_lock = threading.Lock()
_st_model: Optional[object] = None


def _get_sentence_transformer():
    """Lazy-load once; same 768-d output as nomic-embed-text-v1.5 in LM Studio."""
    global _st_model
    if _st_model is not None:
        return _st_model
    with _st_lock:
        if _st_model is not None:
            return _st_model
        from sentence_transformers import SentenceTransformer

        _st_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            trust_remote_code=True,
        )
    return _st_model


def preload_local_embedding_model() -> None:
    """Warm the embedding model at startup (skipped when using HTTP embeddings)."""
    if settings.EMBEDDING_HTTP_URL.strip():
        return
    _get_sentence_transformer()


def _encode_local_sync(text_list: List[str]) -> List[List[float]]:
    model = _get_sentence_transformer()
    vecs = model.encode(
        text_list,
        batch_size=min(32, max(1, len(text_list))),
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return [row.tolist() for row in vecs]


async def get_embeddings(text_list: List[str]) -> List[List[float]]:
    """OpenAI-compatible HTTP endpoint, or local SentenceTransformer if URL unset."""
    url = settings.EMBEDDING_HTTP_URL.strip()
    if url:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url,
                    json={
                        "input": text_list,
                        "model": settings.EMBEDDING_HTTP_MODEL,
                    },
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return [e["embedding"] for e in data["data"]]
            except Exception as e:
                print(f"Embedding HTTP failed: {e}")
                return []

    try:
        return await asyncio.to_thread(_encode_local_sync, text_list)
    except Exception as e:
        print(f"Embedding local model failed: {e}")
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
