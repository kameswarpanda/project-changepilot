"""Change Analyst Service coordinating agent reasoning and schema validation for ChangePlan."""
import logging
from typing import Optional

from backend.src.agents.change_analyst import ChangeAnalystAgent
from backend.src.models.change_plan import ChangePlan
from backend.src.models.change_request import ChangeRequest
from backend.src.models.workflow_result import ValidationResult
from backend.src.repository.context_builder import RepositoryContext
from backend.src.validators.change_plan_validator import ChangePlanValidator

logger = logging.getLogger("changepilot.services.change_analyst_service")


class ChangeAnalystService:
    """High-level service managing change analysis, planning, and pre-validation."""

    def __init__(self, agent: Optional[ChangeAnalystAgent] = None):
        self.agent = agent or ChangeAnalystAgent()

    def generate_and_validate_plan(
        self,
        request: ChangeRequest,
        context: RepositoryContext
    ) -> tuple[ChangePlan, ValidationResult]:
        """Generates a ChangePlan and immediately enforces deterministic validation gates."""
        logger.info(f"Generating ChangePlan for story {request.story_id}...")
        plan = self.agent.analyze(request, context)

        logger.info(f"Validating ChangePlan for story {request.story_id}...")
        val_result = ChangePlanValidator.validate(plan, context)

        return plan, val_result
