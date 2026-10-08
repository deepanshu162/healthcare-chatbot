import asyncio
import json
import io
import logging
import re
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError
import pypdf

from backend.config import settings
from backend.models.prescription_models import (
    DiagnosisInfo,
    PrescriptionExplanationOutput,
    PrescriptionSummary,
)
from backend.prompts.prescription_prompt import PRESCRIPTION_EXPLAINER_PROMPT

logger = logging.getLogger("healthai.prescription_service")


class PrescriptionService:
    """Service for analyzing doctor's prescriptions using Gemini Vision and Multimodal AI."""

    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._cached_api_key: Optional[str] = None

    def _get_client(self) -> genai.Client:
        """Retrieve or instantiate GenAI Client."""
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError(
                "Gemini API key is not configured. "
                "Please configure your GEMINI_API_KEY in backend environment to process prescriptions."
            )

        if self._client is None or self._cached_api_key != api_key:
            self._client = genai.Client(api_key=api_key)
            self._cached_api_key = api_key
        return self._client

    def _extract_pdf_text_fallback(self, file_bytes: bytes) -> str:
        """Extract plain text from PDF if readable text layer exists."""
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    text_pages.append(f"--- Page {i+1} ---\n{text.strip()}")
            return "\n\n".join(text_pages)
        except Exception as e:
            logger.warning(f"Could not extract plain text from PDF via pypdf: {e}")
            return ""

    def _clean_and_parse_json(self, raw_text: str) -> PrescriptionExplanationOutput:
        """Parse raw text from Gemini into validated PrescriptionExplanationOutput model."""
        if not raw_text or not raw_text.strip():
            raise ValueError("Gemini returned empty explanation output.")

        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        parsed_json = None
        try:
            parsed_json = json.loads(text)
        except Exception:
            # Fallback regex extraction for json object
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    parsed_json = json.loads(match.group(0))
                except Exception as ex:
                    logger.error(f"Regex extraction failed to parse JSON: {ex}")

        if parsed_json and isinstance(parsed_json, dict):
            try:
                return PrescriptionExplanationOutput.model_validate(parsed_json)
            except Exception as ve:
                logger.warning(f"Validation warning when coercing model: {ve}")
                # Attempt to normalize fields if missing
                if "diagnosis" not in parsed_json or not isinstance(parsed_json["diagnosis"], dict):
                    parsed_json["diagnosis"] = {
                        "problem": None,
                        "explanation": "No diagnosis identified.",
                        "is_present": False,
                        "note": "Diagnosis was not explicitly written."
                    }
                if "summary" not in parsed_json or not isinstance(parsed_json["summary"], dict):
                    parsed_json["summary"] = {
                        "problem_summary": "No clear problem stated.",
                        "tests_summary": "See test list.",
                        "medicines_summary": "See medicine list.",
                        "instructions_summary": "Follow doctor advice."
                    }
                return PrescriptionExplanationOutput.model_validate(parsed_json)

        # Fallback default response if JSON parsing completely fails
        return PrescriptionExplanationOutput(
            diagnosis=DiagnosisInfo(
                problem=None,
                explanation="The prescription analysis was generated, but structured sections could not be extracted automatically.",
                is_present=False,
                note="Please verify prescription with your doctor or pharmacist."
            ),
            tests=[],
            medicines=[],
            doctors_instructions=["Please consult your doctor or pharmacist for guidance."],
            unclear_items=[{
                "category": "Prescription Document",
                "item_text": "Complete Document",
                "reason": "Document text or handwriting could not be fully parsed into structured format.",
                "action_advice": "Please consult your doctor or pharmacist to confirm all details."
            }],
            summary=PrescriptionSummary(
                problem_summary="Unclear diagnosis or document",
                tests_summary="Consult doctor for prescribed tests",
                medicines_summary="Consult pharmacist for medicines",
                instructions_summary="Confirm instructions with doctor"
            )
        )

    def _analyze_sync(
        self,
        file_bytes: bytes,
        mime_type: str,
        user_notes: Optional[str] = None
    ) -> PrescriptionExplanationOutput:
        """Synchronous execution of prescription analysis call to Gemini API."""
        client = self._get_client()
        primary_model = settings.GEMINI_MODEL or "gemini-3.6-flash"
        models_to_try = [primary_model]

        for fallback in ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        config = types.GenerateContentConfig(
            system_instruction=PRESCRIPTION_EXPLAINER_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        )

        parts = []

        # Add image/PDF file part
        doc_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
        parts.append(doc_part)

        # If PDF, add extracted plain text context if available
        pdf_text = ""
        if mime_type == "application/pdf":
            pdf_text = self._extract_pdf_text_fallback(file_bytes)

        prompt_text = "Please analyze this uploaded doctor's prescription document carefully. Identify and explain diagnosis (if clearly present), tests, medicines & abbreviations, doctor instructions, and any unclear items strictly according to instructions."
        if pdf_text:
            prompt_text += f"\n\nExtracted text from PDF layer for reference:\n{pdf_text}"
        if user_notes:
            prompt_text += f"\n\nAdditional notes provided by user: {user_notes}"

        parts.append(types.Part.from_text(text=prompt_text))

        contents = [types.Content(role="user", parts=parts)]

        last_error = None
        for model_name in models_to_try:
            try:
                logger.info(f"Analyzing prescription using model {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                if response and response.text:
                    return self._clean_and_parse_json(response.text)
            except Exception as e:
                logger.warning(f"Prescription analysis with model {model_name} failed: {e}. Trying next model...")
                last_error = e

        if last_error:
            raise last_error

        raise RuntimeError("Failed to obtain prescription analysis from AI service.")

    async def analyze_prescription(
        self,
        file_bytes: bytes,
        mime_type: str,
        user_notes: Optional[str] = None
    ) -> PrescriptionExplanationOutput:
        """Asynchronously process prescription image or PDF."""
        if not file_bytes:
            raise ValueError("No file content received.")

        supported_mimes = [
            "image/jpeg", "image/png", "image/webp", "image/gif", "image/heic",
            "application/pdf"
        ]
        if mime_type.lower() not in supported_mimes:
            raise ValueError(f"Unsupported file type '{mime_type}'. Please upload an image (JPG, PNG, WEBP) or a PDF file.")

        try:
            output = await asyncio.to_thread(
                self._analyze_sync,
                file_bytes,
                mime_type,
                user_notes
            )
            return output
        except ValueError as ve:
            logger.warning(f"Prescription service validation error: {ve}")
            raise ve
        except APIError as ae:
            logger.error(f"Gemini API Error in prescription analysis: {ae}")
            raise RuntimeError("AI vision service error while processing prescription.")
        except Exception as ex:
            logger.error(f"Unexpected error analyzing prescription: {ex}")
            raise RuntimeError(f"An error occurred while reading the prescription: {str(ex)}")


prescription_service = PrescriptionService()
