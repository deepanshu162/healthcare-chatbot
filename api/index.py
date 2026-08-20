"""
Vercel serverless entry point for HealthAI FastAPI backend.
Vercel discovers the `app` object from this file automatically.
"""
from backend.main import app  # noqa: F401 — re-exported for Vercel
