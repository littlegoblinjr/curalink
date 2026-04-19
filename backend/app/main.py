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

# --- Production Static File Serving ---
static_dir = os.path.join(os.getcwd(), "static")

# Debug print to help you in the Logs if it fails
print(f"Checking for static files in: {static_dir}")

if os.path.exists(static_dir):
    print("Static directory found. Mounting...")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    print("WARNING: Static directory NOT found. Frontend may be missing.")

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Curalink Station Active", "static_found": os.path.exists(static_dir)}
