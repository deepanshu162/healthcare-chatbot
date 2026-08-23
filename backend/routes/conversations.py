import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.conversation_models import (
    ConversationDetail,
    ConversationListResponse,
)
from backend.services.auth_service import get_optional_current_user
from backend.services.conversation_service import conversation_service

logger = logging.getLogger("healthai.routes.conversations")

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List past conversations",
    description="Returns a list of conversation summaries for the authenticated or current session user."
)
async def list_conversations(
    current_user: Optional[dict] = Depends(get_optional_current_user)
) -> ConversationListResponse:
    """Retrieve all conversations for the user."""
    user_id = current_user["id"] if current_user else None
    convs = await conversation_service.list_user_conversations(user_id=user_id)
    return ConversationListResponse(conversations=convs, total=len(convs))


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history details",
    description="Loads complete conversation history and all messages for a given session ID."
)
async def get_conversation(
    conversation_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
) -> ConversationDetail:
    """Retrieve full conversation details and messages."""
    user_id = current_user["id"] if current_user else None
    detail = await conversation_service.get_conversation_detail(conversation_id, user_id=user_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return detail


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a conversation",
    description="Permanently deletes a specific conversation session and all its messages."
)
async def delete_conversation(
    conversation_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Delete a conversation session."""
    user_id = current_user["id"] if current_user else None
    deleted = await conversation_service.delete_conversation(conversation_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or could not be deleted."
        )
    return {"status": "success", "message": f"Conversation {conversation_id} deleted."}


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Clear all conversations",
    description="Deletes all conversation sessions for the authenticated user."
)
async def clear_all_conversations(
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Clear all conversations for current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to clear all conversations."
        )
    count = await conversation_service.clear_all_user_conversations(current_user["id"])
    return {"status": "success", "message": f"Cleared {count} conversations."}
