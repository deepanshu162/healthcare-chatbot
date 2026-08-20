from fastapi import APIRouter, HTTPException, status
from backend.models.chat_models import ChatRequest, ChatResponse
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
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Handle POST /api/chat requests with multi-turn conversation support."""
    try:
        # Retrieve or initialize conversation session
        cid = conversation_service.get_or_create_id(request.conversation_id)
        history = conversation_service.get_history(cid)

        # Generate structured assessment via Gemini
        ai_output = await gemini_service.generate_assessment(
            user_message=request.message,
            history=history
        )

        # Record conversation turns in memory
        conversation_service.add_turn(cid, role="user", content=request.message)

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

        conversation_service.add_turn(cid, role="assistant", content=assistant_content)

        return ChatResponse(
            conversation_id=cid,
            response_type=ai_output.response_type,
            message=ai_output.message,
            questions=ai_output.questions,
            risk_hint=ai_output.risk_hint,
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
