"""Code Generation Service coordinating patch generation and consistency gates."""
import logging
from pathlib import Path
from typing import Optional

from backend.src.agents.code_generator import CodeGeneratorAgent
from backend.src.models.change_plan import ChangePlan
from backend.src.models.change_request import ChangeRequest
from backend.src.models.patch_plan import PatchPlan
from backend.src.models.workflow_result import ValidationResult
from backend.src.repository.context_builder import RepositoryContext
from backend.src.validators.patch_plan_consistency_validator import PatchPlanConsistencyValidator
from backend.src.validators.patch_validator import PatchValidator

logger = logging.getLogger("changepilot.services.code_generation_service")


class CodeGenerationService:
    """Service handling patch synthesis, consistency enforcement, and patch safety checks."""

    def __init__(self, agent: Optional[CodeGeneratorAgent] = None):
        self.agent = agent or CodeGeneratorAgent()

    def generate_and_validate_patch(
        self,
        request: ChangeRequest,
        plan: ChangePlan,
        context: RepositoryContext,
        workspace_path: Path
    ) -> tuple[PatchPlan, ValidationResult, ValidationResult]:
        """Generates PatchPlan and runs both consistency and structural safety gates."""
        logger.info(f"Generating PatchPlan for story {plan.story_id}...")
        patch_plan = self.agent.generate_patch(request, plan, context)

        logger.info(f"Validating PatchPlan consistency against ChangePlan...")
        consistency_res = PatchPlanConsistencyValidator.validate(patch_plan, plan)

        logger.info(f"Validating PatchPlan confinement and structural syntax...")
        safety_res = PatchValidator.validate(patch_plan, workspace_path)

        return patch_plan, consistency_res, safety_res
