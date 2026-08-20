import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse

from backend.config import settings
from backend.routes.chat import router as chat_router

# Initialize FastAPI application
app = FastAPI(
    title="HealthAI — AI Healthcare Guidance Assistant",
    description="Backend API for HealthAI v0.2 healthcare guidance chatbot.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(chat_router)

# Mount static frontend directory
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend_app")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root URL to the frontend web app."""
    return RedirectResponse(url="/app/")


@app.get(
    "/health",
    summary="Health check endpoint",
    description="Confirms that the HealthAI backend is running and Gemini is configured."
)
async def health_check():
    """GET /health endpoint confirming backend operational status."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "running",
            "service": "HealthAI Backend API",
            "version": "0.2.0",
            "message": "HealthAI backend is online and operational.",
            "gemini_configured": settings.is_gemini_configured(),
            "model": settings.GEMINI_MODEL,
            "endpoints": {
                "chat": "POST /api/chat",
                "health": "GET /health",
                "docs": "GET /docs",
                "web_app": "GET /app/"
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
