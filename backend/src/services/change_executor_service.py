"""Change Executor Service coordinating safe filesystem mutation and bounded test execution."""
import logging
from pathlib import Path
from typing import Optional

from backend.src.executor.applier import ApplyResult, PatchApplier
from backend.src.executor.validation_engine import ExecutionResult, ValidationEngine
from backend.src.models.patch_plan import PatchPlan
from backend.src.models.workflow_result import ValidationResult
from backend.src.repository.manager import IsolatedWorkspace

logger = logging.getLogger("changepilot.services.change_executor_service")


class ChangeExecutorService:
    """Coordinates the atomic application of patches and bounded test verification."""

    @staticmethod
    def apply_patches(
        patch_plan: PatchPlan,
        workspace: IsolatedWorkspace,
        story_id: str,
        title: str,
        base_branch: str
    ) -> tuple[ApplyResult, Optional[str]]:
        """Applies patches into isolated workspace, commits them, and extracts the Git diff."""
        logger.info(f"Applying {len(patch_plan.file_patches)} patches to workspace: {workspace.path}")
        apply_res = PatchApplier.apply_patch_plan(patch_plan, workspace.path)

        if not apply_res.success:
            return apply_res, None

        # Commit changes to isolate git history
        commit_msg = f"feat({story_id}): {title}"
        workspace.commit_changes(commit_msg)

        # Generate diff relative to base branch
        diff = workspace.get_diff(base_branch=base_branch)
        if not diff or not diff.strip():
            diff_blocks = []
            for fp in patch_plan.file_patches:
                raw_content = getattr(fp, "content", None) or getattr(fp, "patch_content", None) or ""
                lines = raw_content.splitlines()
                line_count = len(lines) or 1
                if fp.change_type == "CREATE":
                    diff_blocks.append(
                        f"diff --git a/{fp.file_path} b/{fp.file_path}\n"
                        f"new file mode 100644\n"
                        f"--- /dev/null\n"
                        f"+++ b/{fp.file_path}\n"
                        f"@@ -0,0 +1,{line_count} @@\n" +
                        "\n".join(f"+{l}" for l in lines)
                    )
                elif fp.change_type == "DELETE":
                    diff_blocks.append(
                        f"diff --git a/{fp.file_path} b/{fp.file_path}\n"
                        f"deleted file mode 100644\n"
                        f"--- a/{fp.file_path}\n"
                        f"+++ /dev/null"
                    )
                else:
                    diff_blocks.append(
                        f"diff --git a/{fp.file_path} b/{fp.file_path}\n"
                        f"--- a/{fp.file_path}\n"
                        f"+++ b/{fp.file_path}\n"
                        f"@@ -1,1 +1,{line_count} @@\n" +
                        "\n".join(f"+{l}" for l in lines)
                    )
            diff = "\n\n".join(diff_blocks)

        return apply_res, diff

    @staticmethod
    def run_tests(
        workspace_path: Path,
        test_command: Optional[str] = None
    ) -> tuple[ExecutionResult, ValidationResult]:
        """Executes the test runner inside the isolated workspace with timeout bounds."""
        cmd = test_command or "pytest"
        logger.info(f"Executing test command: '{cmd}' in {workspace_path}")

        exec_res = ValidationEngine.run_command(cmd, workspace_path)

        val_result = ValidationResult(
            validator_name="ValidationEngine.TestRunner",
            passed=exec_res.success,
            errors=[exec_res.error] if exec_res.error else ([] if exec_res.success else ["Test suite execution failed."]),
            warnings=[],
            output=exec_res.stdout + ("\n" + exec_res.stderr if exec_res.stderr else ""),
            details={
                "command": cmd,
                "return_code": exec_res.return_code,
                "duration_seconds": exec_res.duration_seconds,
            }
        )

        return exec_res, val_result
