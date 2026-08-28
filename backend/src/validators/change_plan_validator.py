"""ChangePlanValidator validating semantic correctness and repository grounding of ChangePlan."""
from pathlib import Path
from typing import List, Set
from backend.src.models.change_plan import ChangePlan, ChangeType
from backend.src.models.workflow_result import ValidationResult
from backend.src.repository.analyzer import RepositoryContext
from backend.src.validators.security_validator import SecurityValidator


class ChangePlanValidator:
    """Validates that a ChangePlan adheres to repository constraints and safety rules."""

    @classmethod
    def validate(cls, plan: ChangePlan, repo_context: RepositoryContext) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        workspace_root = Path(repo_context.root_path)

        # 1. Validate story_id and summary
        if not plan.story_id.strip():
            errors.append("ChangePlan must have a non-empty story_id.")
        if not plan.summary.strip() or len(plan.summary) < 10:
            errors.append("ChangePlan summary must be descriptive (at least 10 characters).")

        # 2. Validate planned changes exist
        if not plan.planned_changes:
            errors.append("ChangePlan must include at least one planned change.")

        existing_files: Set[str] = {f.replace("\\", "/") for f in repo_context.all_files}
        planned_paths: Set[str] = set()

        for idx, change in enumerate(plan.planned_changes):
            clean_path = change.file_path.strip().replace("\\", "/")

            if not clean_path:
                errors.append(f"Planned change #{idx+1} has an empty file_path.")
                continue

            # Security check: path confinement
            sec_res = SecurityValidator.validate_path_confinement(workspace_root, clean_path)
            if not sec_res.passed:
                errors.extend(sec_res.errors)
                continue

            # Check duplicate paths in same plan
            if clean_path in planned_paths:
                errors.append(f"Duplicate planned change for file '{clean_path}'.")
            planned_paths.add(clean_path)

            # Check existence against repository topology
            file_exists = clean_path in existing_files or (workspace_root / clean_path).exists()

            if change.change_type == ChangeType.CREATE:
                if file_exists:
                    errors.append(
                        f"Cannot CREATE file '{clean_path}' because it already exists in the repository."
                    )
            elif change.change_type == ChangeType.MODIFY:
                if not file_exists:
                    errors.append(
                        f"Cannot MODIFY file '{clean_path}' because it does not exist in the repository."
                    )
            elif change.change_type == ChangeType.DELETE:
                if not file_exists:
                    errors.append(
                        f"Cannot DELETE file '{clean_path}' because it does not exist in the repository."
                    )

            if not change.description.strip():
                warnings.append(f"Planned change for '{clean_path}' lacks detailed description.")

        passed = len(errors) == 0
        return ValidationResult(
            validator_name="ChangePlanValidator",
            passed=passed,
            errors=errors,
            warnings=warnings,
            details={"planned_count": len(plan.planned_changes), "impacted_count": len(plan.impacted_files)}
        )
