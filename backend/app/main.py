from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.api import api_router
from app.config.config import settings

from app.config.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Curalink AI API",
    description="Backend API for Curalink Medical Research Assistant",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_db_client():
    try:
        # Non-blocking startup to prevent HF 503 timeouts
        import asyncio
        asyncio.create_task(connect_to_mongo())
        print("MongoDB connection initiated in background.")
    except Exception as e:
        print(f"Startup DB Error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        await close_mongo_connection()
    except Exception as e:
        print(f"Shutdown DB Error: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# --- Production SPA File Serving ---
static_dir = os.path.join(os.getcwd(), "static")

print(f"Checking for static files in: {static_dir}")

# 1. Mount the explicit 'assets' folder where Vite compiles JS/CSS
assets_dir = os.path.join(static_dir, "assets")
if os.path.exists(assets_dir):
    print("Assets directory found. Mounting...")
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 2. SPA Catch-All Route
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # If a specific file is requested (like favicon.ico or vite.svg)
    file_path = os.path.join(static_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, return the React application base
    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
        
    return {"error": "Frontend not found", "static_dir": static_dir}
