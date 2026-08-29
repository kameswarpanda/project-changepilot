"""Google ADK & GenAI Agent Runner providing structured invocation with Vertex AI and fallback support."""
import json
import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from backend.src.config import settings

logger = logging.getLogger("changepilot.agents.adk_runner")

T = TypeVar("T", bound=BaseModel)


class ADKAgentRunner:
    """Executes agentic reasoning tasks using Google GenAI SDK with Vertex AI / ADC support."""

    def __init__(self):
        self._client = None
        self._initialize()

    def _initialize(self):
        """Initializes client with Vertex AI ADC or API Key."""
        try:
            from google import genai

            if settings.google_genai_use_vertexai:
                project = settings.google_cloud_project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
                location = settings.google_cloud_location or os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
                has_adc = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

                if project or has_adc:
                    logger.info(f"Initializing Google GenAI client (Vertex AI project: {project}, location: {location})")
                    self._client = genai.Client(
                        vertexai=True,
                        project=project,
                        location=location
                    )
                else:
                    logger.info("Vertex AI: No project or ADC credentials configured in environment.")
                    self._client = None
            elif settings.gemini_api_key:
                logger.info("Initializing Google GenAI client with API key.")
                self._client = genai.Client(api_key=settings.gemini_api_key)
            else:
                self._client = None
        except Exception as e:
            logger.warning(f"ADK Client initialization skipped or unavailable: {e}")
            self._client = None

    def is_available(self) -> bool:
        """Returns True if the live Google GenAI / Vertex AI client is ready."""
        return self._client is not None

    def run_agent_task(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
        temperature: float = 0.1,
    ) -> T:
        """Executes a structured schema-enforced generation task."""
        if not self._client:
            raise RuntimeError(
                "Google GenAI / Vertex AI client is unavailable. Please configure Application Default Credentials or GEMINI_API_KEY."
            )

        from google.genai import types

        model_name = settings.gemini_model or "gemini-2.5-flash"
        logger.info(f"Executing agent task via model '{model_name}'...")

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

            parsed = json.loads(response_text)
            return response_schema.model_validate(parsed)

        except Exception as e:
            logger.error(f"ADK Agent Runner task failed: {e}")
            raise RuntimeError(f"Model generation error: {str(e)}") from e
