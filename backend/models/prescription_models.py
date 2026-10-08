from typing import List, Optional
from pydantic import BaseModel, Field


class DiagnosisInfo(BaseModel):
    """Diagnosis or problem identification from prescription."""
    problem: Optional[str] = Field(
        default=None,
        description="The medical problem or diagnosis stated on the prescription, or None if omitted."
    )
    explanation: str = Field(
        ...,
        description="Simple language explanation of the diagnosis if present."
    )
    is_present: bool = Field(
        default=False,
        description="True if a diagnosis was explicitly written on the prescription; False otherwise."
    )
    note: str = Field(
        default="Do not create or assume a diagnosis if it is not clearly present.",
        description="Clinical safety note."
    )


class TestInfo(BaseModel):
    """Prescribed test analysis."""
    test_name: str = Field(..., description="Name of the prescribed test.")
    what_it_is: str = Field(..., description="Simple explanation of what the test is.")
    what_it_checks: str = Field(..., description="What the test measures or checks.")
    why_recommended: str = Field(..., description="Why the doctor may have recommended the test.")


class MedicineInfo(BaseModel):
    """Prescribed medicine details and abbreviation explanations."""
    medicine_name: str = Field(..., description="Brand or generic name of the medicine.")
    general_use: str = Field(..., description="What the medicine is generally used for.")
    strength_dosage: str = Field(default="As written", description="Strength or dose written.")
    frequency: str = Field(default="As written", description="Dosage frequency notation (e.g. OD, BD, 1-0-1).")
    abbreviation_explained: str = Field(..., description="Plain-language explanation of dosage abbreviation.")
    duration: str = Field(default="As specified", description="Duration for taking the medicine.")
    timing_food: str = Field(default="Not specified", description="Food timing instructions (before or after food).")
    other_instructions: str = Field(default="", description="Other doctor instructions for this medicine.")
    is_clear: bool = Field(default=True, description="True if medicine details are legibly identified.")


class UnclearItem(BaseModel):
    """Representation of ambiguous or unreadable handwriting on prescription."""
    category: str = Field(..., description="Category of unclear data (Medicine, Dosage, Frequency, Test, etc.).")
    item_text: str = Field(..., description="The unreadable or ambiguous text snippet.")
    reason: str = Field(..., description="Reason why item could not be confidently identified.")
    action_advice: str = Field(
        default="Please confirm this detail with your doctor or pharmacist.",
        description="Recommendation to consult doctor or pharmacist."
    )


class PrescriptionSummary(BaseModel):
    """Executive simple summary of the prescription."""
    problem_summary: str = Field(..., description="Summary of problem doctor appears to be treating.")
    tests_summary: str = Field(..., description="Summary of prescribed tests and rationale.")
    medicines_summary: str = Field(..., description="Summary of prescribed medicines and dosing schedule.")
    instructions_summary: str = Field(..., description="Summary of key doctor instructions.")


class PrescriptionExplanationOutput(BaseModel):
    """Structured response for prescription explanation."""
    diagnosis: DiagnosisInfo = Field(..., description="Diagnosis section.")
    tests: List[TestInfo] = Field(default_factory=list, description="Prescribed tests section.")
    medicines: List[MedicineInfo] = Field(default_factory=list, description="Prescribed medicines section.")
    doctors_instructions: List[str] = Field(default_factory=list, description="Doctor instructions section.")
    unclear_items: List[UnclearItem] = Field(default_factory=list, description="Unclear information and warnings section.")
    summary: PrescriptionSummary = Field(..., description="Simple summary section.")
    safety_disclaimer: str = Field(
        default="This explanation is for informational purposes only and does not replace professional medical advice. Always confirm details with your physician or pharmacist.",
        description="Medical safety disclaimer."
    )
