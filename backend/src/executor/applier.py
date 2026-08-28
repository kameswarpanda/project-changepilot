"""Patch Applier enforcing strict filesystem boundaries for safe workspace mutation."""
import logging
import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

from backend.src.models.change_plan import ChangeType
from backend.src.models.patch_plan import PatchPlan
from backend.src.validators.security_validator import SecurityValidator

logger = logging.getLogger("changepilot.executor.applier")


class AppliedFileResult(BaseModel):
    """Result of applying an individual file patch."""
    file_path: str
    change_type: ChangeType
    success: bool
    error: str = ""


class PatchApplicationResult(BaseModel):
    """Aggregate result of applying a full PatchPlan."""
    success: bool
    applied_files: List[AppliedFileResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class PatchApplier:
    """Safely mutates the isolated repository workspace according to a validated PatchPlan."""

    @classmethod
    def apply_patch_plan(cls, patch_plan: PatchPlan, workspace_root: Path) -> PatchApplicationResult:
        """Applies all file patches in the PatchPlan to the workspace."""
        workspace_root = workspace_root.resolve()
        applied_results: List[AppliedFileResult] = []
        overall_errors: List[str] = []

        logger.info(f"Applying PatchPlan for story {patch_plan.story_id} to {workspace_root}")

        for patch in patch_plan.file_patches:
            clean_rel = patch.file_path.strip().replace("\\", "/")

            # Security gate: Path confinement check
            sec_check = SecurityValidator.validate_path_confinement(workspace_root, clean_rel)
            if not sec_check.passed:
                err = f"Security rejection for '{clean_rel}': {'; '.join(sec_check.errors)}"
                applied_results.append(AppliedFileResult(
                    file_path=clean_rel,
                    change_type=patch.change_type,
                    success=False,
                    error=err
                ))
                overall_errors.append(err)
                continue

            target_path = (workspace_root / clean_rel).resolve()

            try:
                if patch.change_type == ChangeType.CREATE:
                    if target_path.exists():
                        err = f"Cannot CREATE '{clean_rel}': file already exists."
                        applied_results.append(AppliedFileResult(
                            file_path=clean_rel,
                            change_type=patch.change_type,
                            success=False,
                            error=err
                        ))
                        overall_errors.append(err)
                        continue

                    # Ensure parent directories exist
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    content = patch.content or ""
                    target_path.write_text(content, encoding="utf-8")
                    applied_results.append(AppliedFileResult(
                        file_path=clean_rel,
                        change_type=patch.change_type,
                        success=True
                    ))
                    logger.info(f"Successfully CREATED {clean_rel}")

                elif patch.change_type == ChangeType.MODIFY:
                    if not target_path.exists() or not target_path.is_file():
                        err = f"Cannot MODIFY '{clean_rel}': target file does not exist."
                        applied_results.append(AppliedFileResult(
                            file_path=clean_rel,
                            change_type=patch.change_type,
                            success=False,
                            error=err
                        ))
                        overall_errors.append(err)
                        continue

                    content = patch.content or ""
                    target_path.write_text(content, encoding="utf-8")
                    applied_results.append(AppliedFileResult(
                        file_path=clean_rel,
                        change_type=patch.change_type,
                        success=True
                    ))
                    logger.info(f"Successfully MODIFIED {clean_rel}")

                elif patch.change_type == ChangeType.DELETE:
                    if not target_path.exists():
                        err = f"Cannot DELETE '{clean_rel}': target file does not exist."
                        applied_results.append(AppliedFileResult(
                            file_path=clean_rel,
                            change_type=patch.change_type,
                            success=False,
                            error=err
                        ))
                        overall_errors.append(err)
                        continue

                    if target_path.is_dir():
                        err = f"Cannot DELETE '{clean_rel}': target is a directory."
                        applied_results.append(AppliedFileResult(
                            file_path=clean_rel,
                            change_type=patch.change_type,
                            success=False,
                            error=err
                        ))
                        overall_errors.append(err)
                        continue

                    target_path.unlink()
                    applied_results.append(AppliedFileResult(
                        file_path=clean_rel,
                        change_type=patch.change_type,
                        success=True
                    ))
                    logger.info(f"Successfully DELETED {clean_rel}")

            except Exception as e:
                err = f"Filesystem error on '{clean_rel}': {str(e)}"
                applied_results.append(AppliedFileResult(
                    file_path=clean_rel,
                    change_type=patch.change_type,
                    success=False,
                    error=err
                ))
                overall_errors.append(err)

        is_success = len(overall_errors) == 0
        return PatchApplicationResult(
            success=is_success,
            applied_files=applied_results,
            errors=overall_errors
        )
