import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.models.prescription_models import (
    DiagnosisInfo,
    MedicineInfo,
    PrescriptionExplanationOutput,
    PrescriptionSummary,
    TestInfo,
    UnclearItem,
)
from backend.services.auth_service import get_optional_current_user
from backend.services.prescription_service import prescription_service

logger = logging.getLogger("healthai.routes.prescription")

router = APIRouter(prefix="/api/prescription", tags=["Prescription Explainer"])

# Maximum allowed upload file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post(
    "/explain",
    response_model=PrescriptionExplanationOutput,
    status_code=status.HTTP_200_OK,
    summary="Upload and explain a doctor's prescription",
    description="Upload a prescription image (JPG, PNG, WEBP) or PDF file to receive a simple, structured explanation of diagnosis, tests, medicines, dosage abbreviations, doctor instructions, and unclear handwriting warnings."
)
async def explain_prescription(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(default=None),
    current_user: Optional[dict] = Depends(get_optional_current_user)
) -> PrescriptionExplanationOutput:
    """Process uploaded prescription image/PDF and return structured breakdown."""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded. Please select a prescription image or PDF file."
        )

    filename = file.filename or "uploaded_file"
    content_type = file.content_type or ""

    # Infer content-type if missing based on extension
    if not content_type or content_type == "application/octet-stream":
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            content_type = "application/pdf"
        elif lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif lower_name.endswith(".png"):
            content_type = "image/png"
        elif lower_name.endswith(".webp"):
            content_type = "image/webp"

    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/heic", "application/pdf"]
    if content_type.lower() not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{content_type}'. Supported formats are JPG, PNG, WEBP, and PDF."
        )

    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty. Please select a valid file."
            )

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum limit of 10MB."
            )

        explanation = await prescription_service.analyze_prescription(
            file_bytes=file_bytes,
            mime_type=content_type,
            user_notes=notes
        )
        return explanation

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
        logger.error(f"Error handling prescription upload: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the prescription. Please ensure the file is clear and try again."
        )


@router.get(
    "/sample",
    response_model=PrescriptionExplanationOutput,
    status_code=status.HTTP_200_OK,
    summary="Get sample prescription explanation for testing",
    description="Returns an interactive sample prescription explanation demonstrating all sections, medicines, test explanations, abbreviation breakdowns, and unclear handwriting warnings."
)
async def get_sample_prescription() -> PrescriptionExplanationOutput:
    """Return pre-populated sample prescription explanation for instant demonstration."""
    return PrescriptionExplanationOutput(
        diagnosis=DiagnosisInfo(
            problem="Acute Bronchitis & Respiratory Tract Infection",
            explanation="An inflammation of the main airways (bronchial tubes) carrying air to your lungs, causing cough and congestion.",
            is_present=True,
            note="Explicitly written on prescription: 'Dx: Acute Bronchitis'."
        ),
        tests=[
            TestInfo(
                test_name="Chest X-Ray (PA View)",
                what_it_is="An imaging test that takes a picture of the lungs and chest cavity.",
                what_it_checks="Checks for lung infection, fluid accumulation, or pneumonia.",
                why_recommended="The doctor recommended this to rule out pneumonia or lower respiratory complications due to persistent cough."
            ),
            TestInfo(
                test_name="Complete Blood Count (CBC)",
                what_it_is="A blood test that measures red blood cells, white blood cells, and platelets.",
                what_it_checks="Checks white blood cell count (WBC) for signs of bacterial or viral infection.",
                why_recommended="To determine if the infection is bacterial and monitor systemic inflammation."
            )
        ],
        medicines=[
            MedicineInfo(
                medicine_name="Amoxicillin-Clavulanate 625 mg",
                general_use="An antibiotic used to treat bacterial infections of the chest and airways.",
                strength_dosage="625 mg",
                frequency="BD",
                abbreviation_explained="BD means Twice Daily — take 1 tablet in the morning and 1 tablet at night (approx 12 hours apart).",
                duration="5 days",
                timing_food="Take AFTER food (PC)",
                other_instructions="Complete the full 5-day course even if feeling better.",
                is_clear=True
            ),
            MedicineInfo(
                medicine_name="Paracetamol 500 mg",
                general_use="A mild pain reliever and fever reducer.",
                strength_dosage="500 mg",
                frequency="1-0-1",
                abbreviation_explained="1-0-1 means 1 tablet in the morning, 0 in the afternoon, and 1 tablet at night (Twice daily).",
                duration="3 days / SOS",
                timing_food="Take AFTER food (PC)",
                other_instructions="Take only when fever or body aches are present.",
                is_clear=True
            ),
            MedicineInfo(
                medicine_name="Levosalbutamol Cough Syrup 10ml",
                general_use="A bronchodilator cough syrup that relaxes airway muscles to ease breathing.",
                strength_dosage="10 ml",
                frequency="TDS",
                abbreviation_explained="TDS means Thrice Daily — take 10ml in morning, 10ml in afternoon, and 10ml at night.",
                duration="5 days",
                timing_food="After food",
                other_instructions="Shake bottle well before use.",
                is_clear=True
            ),
            MedicineInfo(
                medicine_name="Pantoprazole 40 mg",
                general_use="A proton pump inhibitor (PPI) that reduces stomach acid and protects stomach lining.",
                strength_dosage="40 mg",
                frequency="OD",
                abbreviation_explained="OD means Once Daily — take 1 tablet in the morning.",
                duration="5 days",
                timing_food="Take BEFORE food (AC) / Empty stomach 30 mins before breakfast",
                other_instructions="Take with a full glass of water.",
                is_clear=True
            )
        ],
        doctors_instructions=[
            "Drink at least 2.5 to 3 liters of warm water daily to stay hydrated and loosen mucus.",
            "Avoid cold drinks, fried foods, and direct exposure to cold air.",
            "Get plenty of rest and avoid strenuous physical exertion.",
            "Follow up with the doctor after 5 days or sooner if high fever persists or breathing difficulty worsens."
        ],
        unclear_items=[
            UnclearItem(
                category="Medicine Name / Anti-allergy",
                item_text="Tab C-______ 10mg HS",
                reason="Cursive handwriting for the anti-allergy tablet brand name is smudged after the letter C.",
                action_advice="DO NOT GUESS. Please bring your prescription sheet to your pharmacist or contact your doctor's office to confirm the exact tablet name before purchasing."
            )
        ],
        summary=PrescriptionSummary(
            problem_summary="Acute Bronchitis & Respiratory Tract Infection causing airway inflammation and cough.",
            tests_summary="Chest X-Ray to check lung clarity and CBC blood test to measure infection markers.",
            medicines_summary="Antibiotic (Amoxicillin-Clav 625mg BD after food), Fever/Pain reducer (Paracetamol 500mg 1-0-1), Cough syrup (Levosalbutamol TDS), and Acid reducer (Pantoprazole 40mg OD empty stomach).",
            instructions_summary="Drink warm water, take rest, complete antibiotic course, and follow up in 5 days."
        ),
        safety_disclaimer="This explanation is provided for educational and informational purposes only to help you understand your doctor's written prescription. It is NOT a medical diagnosis or prescription. Do not change dosages or start/stop medications without consulting your physician or pharmacist."
    )
