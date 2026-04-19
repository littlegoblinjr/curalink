from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.research_agent import run_research

from app.config.database import save_chat_message

router = APIRouter()

# 1. Define the Expected Input from the Frontend
class ResearchRequest(BaseModel):
    patient_name: str
    disease: str
    query: str
    session_id: str # Required for multi-turn history
    location: Optional[str] = None

@router.post("/query")
async def perform_research(request: ResearchRequest):
    """
    This endpoint triggers the entire 5-step pipeline with session state.
    """
    try:
        # Save User Query to History
        await save_chat_message(request.session_id, "user", request.query)

        # Call the Pipeline (Now accepting session_id)
        result = await run_research(
            query=request.query,
            disease=request.disease,
            session_id=request.session_id,
            location=request.location
        )

        # Save Assistant Response to History
        await save_chat_message(request.session_id, "assistant", result["answer"])
        
        return {
            "status": "success",
            "patient": request.patient_name,
            "data": result
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR IN RESEARCH ENDPOINT: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
