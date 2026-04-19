import httpx
from typing import List
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBED_URL = "http://localhost:1234/v1/embeddings"
MODEL_NAME = "nomic-embed-text-v1.5"

async def get_embeddings(text_list: List[str]) -> List[List[float]]:
    """Calls LM Studio's embedding endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                EMBED_URL,
                json={"input": text_list, "model": MODEL_NAME},
                timeout=30.0
            )
            data = resp.json()
            return [e["embedding"] for e in data["data"]]
        except Exception as e:
            print(f"Embedding failed: {e}")
            return []

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

async def get_top_chunks(query: str, full_text: str, top_k: int = 5) -> str:
    """Chunks a long text and returns the most semantically relevant parts."""
    if not full_text: return ""
    
    # 1. Semantic Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    
    if len(chunks) <= top_k:
        return "\n---\n".join(chunks)

    # 2. Get Embeddings (Batch call)
    all_texts = [query] + chunks
    embeddings = await get_embeddings(all_texts)
    
    if not embeddings:
        # Fallback to simple keyword search if embeddings fail
        print("Falling back to keyword-based chunking...")
        query_words = set(query.lower().split())
        scored_chunks = []
        for c in chunks:
            score = len(query_words.intersection(set(c.lower().split())))
            scored_chunks.append((score, c))
        ranked = sorted(scored_chunks, key=lambda x: x[0], reverse=True)
        return "\n---\n".join([c[1] for c in ranked[:top_k]])

    # 3. Calculate Similarity
    query_vec = embeddings[0]
    chunk_vecs = embeddings[1:]
    
    scored_chunks = []
    for i, vec in enumerate(chunk_vecs):
        score = cosine_similarity(query_vec, vec)
        scored_chunks.append((score, chunks[i]))
    
    # 4. Rank and return
    ranked = sorted(scored_chunks, key=lambda x: x[0], reverse=True)
    return "\n---\n".join([c[1] for c in ranked[:top_k]])
