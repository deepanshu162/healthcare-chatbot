from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ResponseType(str, Enum):
    """Response classification types for HealthAI."""
    FOLLOW_UP = "follow_up"
    GUIDANCE = "guidance"
    EMERGENCY = "emergency"


class RiskHint(str, Enum):
    """Risk severity hints."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class FollowUpQuestion(BaseModel):
    """A single MCQ follow-up question with selectable answer options."""
    question: str = Field(..., description="The follow-up question text.")
    options: List[str] = Field(
        default_factory=list,
        description="3–4 selectable multiple-choice answer options for this question."
    )

    @field_validator("options")
    @classmethod
    def limit_options(cls, v: List[str]) -> List[str]:
        cleaned = [o.strip() for o in v if o.strip()]
        return cleaned[:4]


class ClinicalNoteSchema(BaseModel):
    """Structured clinical notepad summary representation."""
    chief_complaint: Optional[str] = Field(default=None, description="Primary symptom or stated health concern.")
    duration: Optional[str] = Field(default=None, description="Duration or onset timeline if known.")
    severity: Optional[str] = Field(default=None, description="Severity assessment (e.g. Mild 2/10, Moderate 6/10, Severe).")
    key_findings: List[str] = Field(default_factory=list, description="Extracted clinical details, location, and associated symptoms.")
    red_flags: List[str] = Field(default_factory=list, description="Identified red-flag symptoms or safety alerts.")
    doctor_questions: List[str] = Field(default_factory=list, description="Recommended questions to ask during a doctor's visit.")
    supportive_care: List[str] = Field(default_factory=list, description="Safe home supportive and self-care measures.")


class StructuredAiOutput(BaseModel):
    """Pydantic model representing structured JSON output from Gemini AI."""
    response_type: ResponseType = Field(
        ...,
        description="The type of response: follow_up, guidance, or emergency."
    )
    message: str = Field(
        ...,
        description="The core empathetic educational message or explanation."
    )
    questions: List[FollowUpQuestion] = Field(
        default_factory=list,
        description="List of MCQ follow-up questions (0 to 5 maximum)."
    )
    risk_hint: str = Field(
        default="unknown",
        description="Estimated risk level: low, moderate, high, emergency, or unknown."
    )
    clinical_note: Optional[ClinicalNoteSchema] = Field(
        default=None,
        description="Structured clinical symptom note for the live notepad panel."
    )

    @field_validator("questions", mode="before")
    @classmethod
    def coerce_questions(cls, v: Any) -> List[Dict]:
        """Accept either list-of-strings (legacy) or list-of-dicts (MCQ)."""
        if not isinstance(v, list):
            return []
        result = []
        for item in v[:5]:
            if isinstance(item, str):
                result.append({"question": item.strip(), "options": []})
            elif isinstance(item, dict):
                result.append(item)
            elif isinstance(item, FollowUpQuestion):
                result.append(item.model_dump())
        return result


class ChatRequest(BaseModel):
    """Client request payload for POST /api/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User health inquiry or symptom assessment response.",
        examples=["I have stomach pain on my lower right side."]
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional session ID to retain multi-turn assessment context.",
        examples=["conv_a1b2c3d4"]
    )

    @field_validator("message")
    @classmethod
    def validate_non_empty_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message cannot be blank or contain only whitespace.")
        return stripped


class ChatResponse(BaseModel):
    """Server response payload for POST /api/chat."""
    conversation_id: str = Field(
        ...,
        description="Unique conversation identifier maintaining session context."
    )
    response_type: ResponseType = Field(
        ...,
        description="Categorization of the AI response."
    )
    message: str = Field(
        ...,
        description="The AI healthcare assessment message or summary."
    )
    questions: List[FollowUpQuestion] = Field(
        default_factory=list,
        description="MCQ follow-up questions if response_type is follow_up."
    )
    risk_hint: str = Field(
        default="unknown",
        description="Risk guidance hint."
    )
    clinical_note: Optional[ClinicalNoteSchema] = Field(
        default=None,
        description="Structured clinical symptom note for the live notepad panel."
    )
