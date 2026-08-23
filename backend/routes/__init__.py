"""HealthAI Routes Package."""
from backend.routes.chat import router as chat_router
from backend.routes.auth import router as auth_router
from backend.routes.conversations import router as conversations_router

__all__ = ["chat_router", "auth_router", "conversations_router"]
