from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from backend.models.chat_models import ChatRequest, ChatResponse
from backend.services.auth_service import get_optional_current_user
from backend.services.conversation_service import conversation_service
from backend.services.gemini_service import gemini_service

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send health inquiry for intelligent symptom assessment",
    description="Processes health inquiries with context-aware follow-up question analysis and emergency prioritization."
)
async def chat_endpoint(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
) -> ChatResponse:
    """Handle POST /api/chat requests with multi-turn conversation support and MongoDB persistence."""
    try:
        user_id = current_user["id"] if current_user else None

        # Retrieve or initialize conversation session
        cid = await conversation_service.get_or_create_id(
            request.conversation_id,
            user_id=user_id
        )
        history = await conversation_service.get_history(cid)

        # Generate structured assessment via Gemini
        ai_output = await gemini_service.generate_assessment(
            user_message=request.message,
            history=history
        )

        # Record user turn in MongoDB
        await conversation_service.add_turn(
            conversation_id=cid,
            role="user",
            content=request.message,
            user_id=user_id
        )

        # Prepare formatted assistant response for context history
        if ai_output.questions:
            q_lines = []
            for i, q in enumerate(ai_output.questions):
                q_lines.append(f"{i+1}. {q.question}")
                for opt in q.options:
                    q_lines.append(f"   - {opt}")
            assistant_content = f"{ai_output.message}\n" + "\n".join(q_lines)
        else:
            assistant_content = ai_output.message

        # Record assistant turn in MongoDB with structured fields and clinical note
        await conversation_service.add_turn(
            conversation_id=cid,
            role="assistant",
            content=assistant_content,
            response_type=ai_output.response_type.value if hasattr(ai_output.response_type, "value") else str(ai_output.response_type),
            questions=ai_output.questions,
            risk_hint=ai_output.risk_hint,
            clinical_note=ai_output.clinical_note,
            user_id=user_id
        )

        return ChatResponse(
            conversation_id=cid,
            response_type=ai_output.response_type,
            message=ai_output.message,
            questions=ai_output.questions,
            risk_hint=ai_output.risk_hint,
            clinical_note=ai_output.clinical_note,
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while assessing symptoms. Please try again later."
        )
