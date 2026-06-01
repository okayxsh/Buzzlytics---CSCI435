"""Buzzlytics API - FastAPI application entry point.

Computer Vision Hive Health Dashboard API that provides video upload/processing
endpoints and WebSocket-based live webcam streaming for bee hive monitoring.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to sys.path so cv_pipeline can be imported
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.routes import video_routes, websocket_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events.

    Creates required directories on startup and performs cleanup on shutdown.
    """
    # Startup: create required directories
    uploads_dir = BACKEND_DIR / "uploads"
    results_dir = BACKEND_DIR / "results"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Buzzlytics] Uploads directory: {uploads_dir}")
    print(f"[Buzzlytics] Results directory: {results_dir}")
    print("[Buzzlytics] API started successfully.")

    yield

    # Shutdown
    print("[Buzzlytics] API shutting down.")


# Create the FastAPI application
app = FastAPI(
    title="Buzzlytics API",
    description="Computer Vision Hive Health Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount CORS middleware - allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route routers
app.include_router(video_routes.router)
app.include_router(websocket_routes.router)


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns a JSON object indicating the service is running and healthy.
    """
    return {"status": "healthy", "service": "buzzlytics"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
