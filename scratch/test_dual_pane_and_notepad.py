import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.mongodb import db_manager
from backend.services.gemini_service import gemini_service
from backend.services.conversation_service import conversation_service
from backend.models.chat_models import StructuredAiOutput, ClinicalNoteSchema

async def main():
    print("=== Testing Clinical Note Extraction & MongoDB Persistence ===")
    
    await db_manager.connect()
    
    test_query = "I have a sharp lower right abdominal pain that started 6 hours ago, severity is 7/10, with slight nausea."
    print(f"\n1. Sending query to Gemini AI: {test_query}")
    
    ai_output = await gemini_service.generate_assessment(user_message=test_query, history=[])
    
    print(f"Response Type: {ai_output.response_type}")
    print(f"Risk Hint: {ai_output.risk_hint}")
    print(f"Message: {ai_output.message[:100]}...")
    print(f"Questions Count: {len(ai_output.questions)}")
    print(f"Clinical Note: {ai_output.clinical_note}")
    
    assert ai_output.clinical_note is not None, "Clinical note was not generated!"
    print(f"  [OK] Chief Complaint: {ai_output.clinical_note.chief_complaint}")
    print(f"  [OK] Duration: {ai_output.clinical_note.duration}")
    print(f"  [OK] Severity: {ai_output.clinical_note.severity}")
    print(f"  [OK] Key Findings: {ai_output.clinical_note.key_findings}")
    print(f"  [OK] Red Flags: {ai_output.clinical_note.red_flags}")
    print(f"  [OK] Doctor Questions: {ai_output.clinical_note.doctor_questions}")
    print(f"  [OK] Supportive Care: {ai_output.clinical_note.supportive_care}")
    
    cid = f"test_dual_pane_{os.urandom(4).hex()}"
    print(f"\n2. Persisting conversation turn with Clinical Note: {cid}")
    
    await conversation_service.add_turn(
        conversation_id=cid,
        role="user",
        content=test_query,
        user_id=None
    )
    
    await conversation_service.add_turn(
        conversation_id=cid,
        role="assistant",
        content=ai_output.message,
        response_type=ai_output.response_type.value,
        questions=ai_output.questions,
        risk_hint=ai_output.risk_hint,
        clinical_note=ai_output.clinical_note,
        user_id=None
    )
    
    print("\n3. Retrieving conversation details from MongoDB...")
    detail = await conversation_service.get_conversation_detail(cid)
    assert detail is not None, "Conversation detail not found!"
    assert len(detail.messages) == 2, f"Expected 2 messages, got {len(detail.messages)}"
    assert detail.last_clinical_note is not None, "Last clinical note not found on conversation!"
    print(f"  [OK] Retrieved last_clinical_note: {detail.last_clinical_note.chief_complaint}")
    
    print("\n4. Cleaning up test record...")
    await conversation_service.delete_conversation(cid)
    print("  [OK] Cleanup complete.")
    
    await db_manager.close()
    print("\n🎉 ALL DUAL-PANE & CLINICAL NOTEPAD BACKEND TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
