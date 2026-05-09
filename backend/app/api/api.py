from fastapi import APIRouter
from app.api.endpoints import research, auth

api_router = APIRouter()
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
