"""Vertex AI Client supporting Application Default Credentials and structured output."""
import json
import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from backend.src.config import settings

logger = logging.getLogger("changepilot.agents.vertex_client")

T = TypeVar("T", bound=BaseModel)


class VertexClient:
    """Interface to Google GenAI / Vertex AI with ADC support."""

    def __init__(self):
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the Google GenAI SDK client with Vertex AI or API key."""
        try:
            from google import genai
            from google.genai import types

            if settings.google_genai_use_vertexai:
                project = settings.google_cloud_project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
                location = settings.google_cloud_location or os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
                has_adc_file = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

                if project or has_adc_file:
                    logger.info(f"Initializing Vertex AI client (Project: {project}, Location: {location})")
                    self._client = genai.Client(
                        vertexai=True,
                        project=project,
                        location=location
                    )
                else:
                    logger.info("Vertex AI: No project or ADC credentials configured in environment. Using fallback mode.")
                    self._client = None
            elif settings.gemini_api_key:
                logger.info("Initializing GenAI client with API key.")
                self._client = genai.Client(api_key=settings.gemini_api_key)
            else:
                logger.info("Neither Vertex AI project nor GEMINI_API_KEY configured.")
        except Exception as e:
            logger.warning(f"Vertex AI initialization skipped or unavailable: {e}")
            self._client = None

    def is_available(self) -> bool:
        """Returns True if the live GenAI / Vertex client is active."""
        return self._client is not None

    def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
        temperature: float = 0.1,
    ) -> T:
        """Generates a structured Pydantic object from the LLM."""
        if not self._client:
            raise RuntimeError(
                "Vertex AI client is not available. Please configure GOOGLE_CLOUD_PROJECT or Application Default Credentials."
            )

        from google.genai import types

        model_name = settings.gemini_model or "gemini-3.7-flash"
        logger.info(f"Invoking Vertex AI model: {model_name}")

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=response_schema,
            )

            response = self._client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )

            response_text = response.text
            if not response_text:
                raise ValueError("Model returned an empty response.")

            # Parse JSON and validate into Pydantic model
            parsed_data = json.loads(response_text)
            return response_schema.model_validate(parsed_data)

        except Exception as e:
            logger.error(f"Vertex AI structured generation failed: {e}")
            raise RuntimeError(f"Vertex AI model error: {str(e)}") from e
