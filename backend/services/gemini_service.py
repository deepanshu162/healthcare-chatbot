import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.config import settings
from backend.models.chat_models import ResponseType, StructuredAiOutput
from backend.prompts.system_prompt import HEALTHAI_SYSTEM_PROMPT

logger = logging.getLogger("healthai.gemini_service")


class GeminiService:
    """Service for interacting with Google Gemini API for structured healthcare guidance."""

    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._cached_api_key: Optional[str] = None

    def _get_client(self) -> genai.Client:
        """Initialize or retrieve the GenAI client with configured API key."""
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError(
                "Gemini API key is not configured. "
                "Please set your GEMINI_API_KEY in the .env file to enable AI responses."
            )

        # Re-initialize client if key changed or not yet created
        if self._client is None or self._cached_api_key != api_key:
            self._client = genai.Client(api_key=api_key)
            self._cached_api_key = api_key
        return self._client

    def _format_contents(self, history: List[Dict[str, str]], current_message: str) -> List[Any]:
        """Convert conversation history and current message into Gemini SDK content objects."""
        contents: List[Any] = []

        # Add past turns
        for turn in history:
            role = turn.get("role", "user")
            content_text = turn.get("content", "")
            if not content_text:
                continue

            sdk_role = "user" if role == "user" else "model"
            contents.append(
                types.Content(
                    role=sdk_role,
                    parts=[types.Part.from_text(text=content_text)]
                )
            )

        # Add current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=current_message)]
            )
        )

        return contents

    def _clean_and_parse_json(self, raw_text: str) -> StructuredAiOutput:
        """Sanitize and parse Gemini output into validated StructuredAiOutput model."""
        if not raw_text or not raw_text.strip():
            return StructuredAiOutput(
                response_type=ResponseType.GUIDANCE,
                message="I received your message, but I could not generate guidance. Please try again.",
                questions=[],
                risk_hint="unknown"
            )

        text = raw_text.strip()

        # Strip markdown code fence if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        try:
            parsed = json.loads(text)
            return StructuredAiOutput.model_validate(parsed)
        except Exception as err:
            logger.warning(f"Failed to parse direct JSON from Gemini: {err}. Attempting regex extraction.")

            # Attempt regex extraction of JSON object {...}
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    return StructuredAiOutput.model_validate(parsed)
                except Exception as inner_err:
                    logger.error(f"Regex JSON fallback failed: {inner_err}")

            # Safe graceful fallback
            return StructuredAiOutput(
                response_type=ResponseType.GUIDANCE,
                message=text,
                questions=[],
                risk_hint="unknown"
            )

    def _generate_sync(self, history: List[Dict[str, str]], user_message: str) -> StructuredAiOutput:
        """Synchronous call to Gemini API with system instructions, JSON mode, and fallback support."""
        client = self._get_client()
        primary_model = settings.GEMINI_MODEL or "gemini-3.6-flash"
        models_to_try = [primary_model]

        for fallback in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        config = types.GenerateContentConfig(
            system_instruction=HEALTHAI_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.3,
        )

        contents = self._format_contents(history, user_message)

        last_error = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                if response and response.text:
                    return self._clean_and_parse_json(response.text)
            except Exception as e:
                logger.warning(f"Attempt with model {model_name} failed: {e}. Trying fallback...")
                last_error = e

        if last_error:
            raise last_error

        return StructuredAiOutput(
            response_type=ResponseType.GUIDANCE,
            message="Unable to process your request at this time. Please try again later.",
            questions=[],
            risk_hint="unknown"
        )

    async def generate_assessment(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> StructuredAiOutput:
        """Asynchronously generate healthcare symptom assessment for user message."""
        clean_message = user_message.strip()
        if not clean_message:
            raise ValueError("Message cannot be empty.")

        hist = history or []

        try:
            # Run in thread executor to avoid blocking FastAPI event loop
            output = await asyncio.to_thread(self._generate_sync, hist, clean_message)
            return output
        except ValueError as ve:
            logger.warning(f"Configuration or input error: {ve}")
            raise ve
        except APIError as ae:
            logger.error(f"Gemini API Error: {ae.message if hasattr(ae, 'message') else str(ae)}")
            raise RuntimeError(
                f"Gemini API service error: {ae.message if hasattr(ae, 'message') else 'Unable to reach AI service.'}"
            )
        except Exception as ex:
            logger.error(f"Unexpected error calling Gemini API: {str(ex)}")
            raise RuntimeError(
                "An unexpected error occurred while communicating with the AI service. Please check your network and API configuration."
            )


# Global singleton instance
gemini_service = GeminiService()
