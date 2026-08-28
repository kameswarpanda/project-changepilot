"""PatchValidator checking structural and safety properties of file patches."""
from pathlib import Path
from typing import List
from backend.src.config import settings
from backend.src.models.change_plan import ChangeType
from backend.src.models.patch_plan import PatchPlan
from backend.src.models.workflow_result import ValidationResult
from backend.src.validators.security_validator import SecurityValidator


class PatchValidator:
    """Validates structural correctness, content integrity, and safety limits of patches."""

    @classmethod
    def validate(cls, patch_plan: PatchPlan, workspace_root: Path) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not patch_plan.file_patches:
            return ValidationResult(
                validator_name="PatchValidator",
                passed=False,
                errors=["PatchPlan contains no file patches."]
            )

        for patch in patch_plan.file_patches:
            clean_path = patch.file_path.strip().replace("\\", "/")

            # Security check on path
            sec_res = SecurityValidator.validate_path_confinement(workspace_root, clean_path)
            if not sec_res.passed:
                errors.extend(sec_res.errors)
                continue

            # Check content expectations based on change_type
            if patch.change_type in [ChangeType.CREATE, ChangeType.MODIFY]:
                if patch.content is None:
                    errors.append(f"Patch for '{clean_path}' ({patch.change_type.value}) requires non-null content.")
                else:
                    byte_len = len(patch.content.encode("utf-8"))
                    if byte_len > settings.max_file_size_bytes:
                        errors.append(
                            f"Patch content for '{clean_path}' exceeds maximum file size limit ({byte_len} bytes > {settings.max_file_size_bytes} bytes)."
                        )

            elif patch.change_type == ChangeType.DELETE:
                if patch.content is not None and patch.content.strip():
                    warnings.append(f"DELETE patch for '{clean_path}' contained content which will be ignored.")

        passed = len(errors) == 0
        return ValidationResult(
            validator_name="PatchValidator",
            passed=passed,
            errors=errors,
            warnings=warnings,
            details={"patch_count": len(patch_plan.file_patches)}
        )
