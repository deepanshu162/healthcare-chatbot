from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.models.chat_models import ClinicalNoteSchema, FollowUpQuestion, ResponseType


class MessageRecord(BaseModel):
    """A persisted message within a conversation."""
    id: Optional[str] = Field(default=None, description="Unique message ID.")
    conversation_id: str = Field(..., description="Parent conversation ID.")
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text content.")
    response_type: Optional[ResponseType] = Field(default=None, description="follow_up, guidance, or emergency.")
    questions: List[FollowUpQuestion] = Field(default_factory=list, description="Follow-up MCQ questions if applicable.")
    risk_hint: Optional[str] = Field(default=None, description="Assessed risk level.")
    clinical_note: Optional[ClinicalNoteSchema] = Field(default=None, description="Structured clinical symptom note.")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO timestamp.")


class ConversationSummary(BaseModel):
    """Condensed summary of a conversation for list/sidebar display."""
    id: str = Field(..., description="Unique conversation session ID.")
    user_id: Optional[str] = Field(default=None, description="Owner user ID if authenticated.")
    title: str = Field(..., description="Auto-generated or user-assigned conversation title.")
    message_count: int = Field(default=0, description="Total number of messages exchanged.")
    last_risk_hint: Optional[str] = Field(default="unknown", description="Most recent risk hint level.")
    created_at: str = Field(..., description="ISO creation timestamp.")
    updated_at: str = Field(..., description="ISO last modified timestamp.")


class ConversationDetail(BaseModel):
    """Full conversation history including all messages and clinical summary."""
    id: str = Field(..., description="Unique conversation session ID.")
    user_id: Optional[str] = Field(default=None, description="Owner user ID.")
    title: str = Field(..., description="Conversation title.")
    last_clinical_note: Optional[ClinicalNoteSchema] = Field(default=None, description="Latest structured clinical note.")
    created_at: str = Field(..., description="ISO creation timestamp.")
    updated_at: str = Field(..., description="ISO last modified timestamp.")
    messages: List[MessageRecord] = Field(default_factory=list, description="Ordered list of conversation messages.")


class ConversationListResponse(BaseModel):
    """Response payload for GET /api/conversations."""
    conversations: List[ConversationSummary] = Field(default_factory=list)
    total: int = Field(default=0)
