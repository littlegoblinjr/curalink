from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.services.research_agent import run_research
import json

from app.config.database import save_chat_message

router = APIRouter()

# 1. Define the Expected Input from the Frontend
class ResearchRequest(BaseModel):
    disease: str
    query: str
    session_id: str
    email: Optional[str] = None
    location: Optional[str] = None

@router.post("/query")
async def perform_research_stream(request: ResearchRequest):
    # Save User Query to History
    await save_chat_message(request.session_id, "user", request.query, email=request.email, topic=request.disease)

    async def event_generator():
        full_answer = ""
        thoughts = ""
        sources = []
        try:
            async for chunk in run_research(
                query=request.query,
                disease=request.disease,
                session_id=request.session_id,
                location=request.location
            ):
                data = json.loads(chunk)
                if data["type"] == "done":
                    full_answer = data.get("full_text", "")
                    thoughts = data.get("thoughts", "")
                    sources = data.get("sources", [])
                yield chunk
            
            # Save Assistant Response
            if full_answer:
                await save_chat_message(
                    request.session_id, 
                    "assistant", 
                    full_answer, 
                    email=request.email, 
                    topic=request.disease,
                    thoughts=thoughts,
                    sources=sources
                )
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@router.get("/sessions")
async def list_sessions(email: str):
    from app.config.database import get_user_sessions
    sessions = await get_user_sessions(email)
    return {"sessions": [{ "id": s["session_id"], "topic": s["topic"], "date": s["last_active"] } for s in sessions]}

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    from app.config.database import get_chat_history
    messages = await get_chat_history(session_id, limit=50)
    return {"messages": messages}

@router.delete("/history/{session_id}")
async def delete_history(session_id: str):
    from app.config.database import delete_session
    await delete_session(session_id)
    return {"status": "success"}
