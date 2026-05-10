import os
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.config import settings
from datetime import datetime
import certifi

# --- IN-MEMORY FALLBACK ---
MEMORY_DB = {}

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    """Initializes the MongoDB connection with a graceful fallback."""
    global db_instance
    try:
        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        # Verify connection
        await db_instance.client.admin.command('ping')
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        print(f"Connected to MongoDB Atlas: {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"!!! MONGODB FAILED: {e} !!!")
        print(">>> SLIPPING INTO DEMO MODE (IN-MEMORY) <<<")
        db_instance.client = None
        db_instance.db = None

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()

async def save_chat_message(session_id: str, role: str, content: str, email: str = None, topic: str = "New Research", thoughts: str = None, sources: list = None):
    if db_instance.db is not None:
        # Save the message
        doc = {
            "session_id": session_id,
            "email": email,
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        if thoughts: doc["thoughts"] = thoughts
        if sources: doc["sources"] = sources
        
        await db_instance.db.chats.insert_one(doc)
        # Track/Update session metadata for listing
        if email:
            await db_instance.db.sessions.update_one(
                {"session_id": session_id, "email": email},
                {"$set": {"topic": topic, "last_active": datetime.now()}},
                upsert=True
            )
    else:
        # Fallback to Memory
        if session_id not in MEMORY_DB:
            MEMORY_DB[session_id] = []
        MEMORY_DB[session_id].append({"role": role, "content": content})

async def get_user_sessions(email: str):
    if db_instance.db is not None:
        cursor = db_instance.db.sessions.find({"email": email}).sort("last_active", -1)
        sessions = await cursor.to_list(length=50)
        for session in sessions:
            session.pop("_id", None)
        return sessions
    return []

async def save_session_results(session_id: str, results: List[Dict[str, Any]]):
    """Appends unique research results to the session-wide library."""
    # 1. Load existing results
    existing = await get_session_results(session_id)
    existing_urls = {res.get('url') for res in existing if res.get('url')}
    
    # 2. Filter for unique new results
    new_results = []
    for res in results:
        url = res.get('url')
        if url and url not in existing_urls:
            new_results.append(res)
            existing_urls.add(url)
    
    combined = existing + new_results
    
    # 3. Save back to MongoDB or Memory
    if db_instance.db is not None:
        await db_instance.db.research_archives.update_one(
            {"session_id": session_id},
            {"$set": {"results": combined, "last_updated": datetime.now()}},
            upsert=True
        )
    else:
        MEMORY_DB[f"arch_{session_id}"] = combined

async def get_session_results(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves cached research for deep-dive analysis."""
    if db_instance.db is not None:
        doc = await db_instance.db.research_archives.find_one({"session_id": session_id})
        return doc.get("results", []) if doc else []
    return MEMORY_DB.get(f"arch_{session_id}", [])

async def get_chat_history(session_id: str, limit: int = 5):
    if db_instance.db is not None:
        cursor = db_instance.db.chats.find({"session_id": session_id}).sort("timestamp", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        for msg in messages:
            msg.pop("_id", None)
        return messages[::-1]
    return MEMORY_DB.get(session_id, [])

async def delete_session(session_id: str):
    """Purges a session and its associated chat history completely."""
    if db_instance.db is not None:
        await db_instance.db.sessions.delete_one({"session_id": session_id})
        await db_instance.db.chats.delete_many({"session_id": session_id})
        await db_instance.db.research_archives.delete_one({"session_id": session_id})
    else:
        MEMORY_DB.pop(session_id, None)
        MEMORY_DB.pop(f"arch_{session_id}", None)


async def save_user(email: str, name: str, hashed_password: str = None):
    if db_instance.db is not None:
        data = {"name": name, "last_login": datetime.now()}
        if hashed_password:
            data["hashed_password"] = hashed_password
            
        await db_instance.db.users.update_one(
            {"email": email},
            {"$set": data},
            upsert=True
        )

async def get_user(email: str):
    if db_instance.db is not None:
        return await db_instance.db.users.find_one({"email": email})
    return None

# ============================================================
# GLOBAL KNOWLEDGE GRAPH — Cross-session paper memory
# ============================================================
KNOWLEDGE_GRAPH_MEMORY: Dict[str, List] = {}  # In-memory fallback keyed by disease

async def save_to_knowledge_graph(disease: str, papers: List[Dict[str, Any]]):
    """
    Persists all newly discovered papers into the global knowledge graph.
    Papers are deduplicated by URL — same paper is never stored twice.
    """
    disease_key = disease.lower().strip()
    if db_instance.db is not None:
        for paper in papers:
            url = paper.get("url")
            if not url:
                continue
            # Ensure we don't accidentally pass disease_tags explicitly in $set if it's in **paper
            paper_data = {k: v for k, v in paper.items() if k != "disease_tags"}
            await db_instance.db.knowledge_graph.update_one(
                {"url": url},
                {
                    "$set": {
                        **paper_data,
                        "last_seen": datetime.now()
                    },
                    "$addToSet": {"disease_tags": disease_key}
                },
                upsert=True
            )
    else:
        existing_urls = {p.get("url") for p in KNOWLEDGE_GRAPH_MEMORY.get(disease_key, [])}
        for paper in papers:
            if paper.get("url") not in existing_urls:
                KNOWLEDGE_GRAPH_MEMORY.setdefault(disease_key, []).append(paper)

async def query_knowledge_graph(disease: str, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Retrieves previously indexed papers relevant to this disease from the global graph.
    Returns the most recently seen papers first.
    """
    disease_key = disease.lower().strip()
    if db_instance.db is not None:
        cursor = db_instance.db.knowledge_graph.find(
            {"disease_tags": disease_key}
        ).sort("last_seen", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        # Strip MongoDB _id and serialize datetime before returning
        for d in docs:
            d.pop("_id", None)
            if "last_seen" in d and isinstance(d["last_seen"], datetime):
                d["last_seen"] = d["last_seen"].isoformat()
        return docs
    return KNOWLEDGE_GRAPH_MEMORY.get(disease_key, [])[:limit]

# ============================================================
# SEMANTIC CACHE — Prompt-to-Response persistency
# ============================================================
async def save_semantic_cache(prompt: str, response_data: Dict[str, Any]):
    """Saves a full research response indexed by a normalized prompt."""
    if db_instance.db is not None:
        await db_instance.db.semantic_cache.update_one(
            {"prompt_norm": prompt.lower().strip()},
            {
                "$set": {
                    "response": response_data,
                    "timestamp": datetime.now()
                }
            },
            upsert=True
        )

async def find_cached_response(prompt: str) -> Optional[Dict[str, Any]]:
    """Retrieves a cached response if the prompt is an exact or normalized match."""
    if db_instance.db is not None:
        doc = await db_instance.db.semantic_cache.find_one({"prompt_norm": prompt.lower().strip()})
        return doc["response"] if doc else None
    return None

