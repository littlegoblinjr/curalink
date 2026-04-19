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

async def save_chat_message(session_id: str, role: str, content: str):
    if db_instance.db is not None:
        await db_instance.db.chats.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
    else:
        # Fallback to Memory
        if session_id not in MEMORY_DB:
            MEMORY_DB[session_id] = []
        MEMORY_DB[session_id].append({"role": role, "content": content})

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
        return messages[::-1]
    return MEMORY_DB.get(session_id, [])
