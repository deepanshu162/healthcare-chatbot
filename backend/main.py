from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.db.mongodb import db_manager
from backend.routes.chat import router as chat_router
from backend.routes.auth import router as auth_router
from backend.routes.conversations import router as conversations_router
from backend.routes.prescription import router as prescription_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup: connect to MongoDB
    await db_manager.connect()
    yield
    # Shutdown: close MongoDB client
    await db_manager.close()


# Initialize FastAPI application
app = FastAPI(
    title="HealthAI — AI Healthcare Guidance Assistant",
    description="Backend API for HealthAI v0.3 healthcare guidance chatbot with MongoDB persistence and User Auth.",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Register API routes
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(prescription_router)


# Mount static assets for frontend (CSS, JS)
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.get(
    "/",
    summary="Root web app endpoint",
    description="Serves the HealthAI frontend web application."
)
async def serve_index():
    """Serve the HealthAI web UI at http://127.0.0.1:8000/"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        status_code=200,
        content={"message": "HealthAI Backend API is running. Access /docs for Swagger UI or /health for status."}
    )


@app.get(
    "/style.css",
    include_in_schema=False
)
async def serve_css():
    """Directly serve style.css if referenced at root."""
    css_file = FRONTEND_DIR / "style.css"
    if css_file.exists():
        return FileResponse(str(css_file), media_type="text/css")
    return JSONResponse(status_code=404, content={"detail": "style.css not found"})


@app.get(
    "/script.js",
    include_in_schema=False
)
async def serve_js():
    """Directly serve script.js if referenced at root."""
    js_file = FRONTEND_DIR / "script.js"
    if js_file.exists():
        return FileResponse(str(js_file), media_type="application/javascript")
    return JSONResponse(status_code=404, content={"detail": "script.js not found"})


@app.get(
    "/health",
    summary="Health check endpoint",
    description="Confirms that the HealthAI backend is running, Gemini is configured, and MongoDB status."
)
async def health_check():
    """GET /health endpoint confirming backend and database operational status."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "running",
            "service": "HealthAI Backend API",
            "version": "0.3.0",
            "message": "HealthAI backend is online and operational.",
            "gemini_configured": settings.is_gemini_configured(),
            "database_connected": db_manager.is_connected(),
            "model": settings.GEMINI_MODEL,
            "endpoints": {
                "chat": "POST /api/chat",
                "auth_register": "POST /api/auth/register",
                "auth_login": "POST /api/auth/login",
                "auth_me": "GET /api/auth/me",
                "conversations": "GET /api/conversations",
                "health": "GET /health",
                "docs": "GET /docs"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
