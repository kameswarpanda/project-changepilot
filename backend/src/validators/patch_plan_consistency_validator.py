"""PatchPlanConsistencyValidator ensuring code patches strictly match approved ChangePlan."""
from typing import Dict, List
from backend.src.models.change_plan import ChangePlan, ChangeType
from backend.src.models.patch_plan import PatchPlan
from backend.src.models.workflow_result import ValidationResult


class PatchPlanConsistencyValidator:
    """Enforces strict 1-to-1 consistency between generated code patches and approved ChangePlan."""

    @classmethod
    def validate(cls, patch_plan: PatchPlan, approved_plan: ChangePlan) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Map planned changes by normalized path
        planned_map: Dict[str, ChangeType] = {
            c.file_path.strip().replace("\\", "/"): c.change_type
            for c in approved_plan.planned_changes
        }

        # Map generated patches by normalized path
        generated_map: Dict[str, ChangeType] = {}

        for patch in patch_plan.file_patches:
            clean_path = patch.file_path.strip().replace("\\", "/")

            if clean_path in generated_map:
                errors.append(f"Duplicate patch proposed for file '{clean_path}'.")
            generated_map[clean_path] = patch.change_type

            # Rule 1: No unapproved files allowed in patch
            if clean_path not in planned_map:
                errors.append(
                    f"Code Generator proposed patch for '{clean_path}', but this file was NOT approved in ChangePlan."
                )
                continue

            # Rule 2: Change types must match approved plan
            expected_type = planned_map[clean_path]
            if patch.change_type != expected_type:
                errors.append(
                    f"Change type mismatch for '{clean_path}': ChangePlan approved {expected_type.value}, "
                    f"but PatchPlan generated {patch.change_type.value}."
                )

        # Rule 3: Check if all approved changes were generated
        for planned_path, change_type in planned_map.items():
            if planned_path not in generated_map:
                errors.append(
                    f"Approved planned change for '{planned_path}' ({change_type.value}) was not included in PatchPlan."
                )

        passed = len(errors) == 0
        return ValidationResult(
            validator_name="PatchPlanConsistencyValidator",
            passed=passed,
            errors=errors,
            warnings=warnings,
            details={
                "approved_files": list(planned_map.keys()),
                "generated_files": list(generated_map.keys())
            }
        )
