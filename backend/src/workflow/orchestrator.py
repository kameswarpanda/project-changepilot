"""Workflow Orchestrator orchestrating end-to-end execution of ChangePilot."""
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.src.agents.change_analyst import ChangeAnalystAgent
from backend.src.config import settings
from backend.src.agents.code_generator import CodeGeneratorAgent
from backend.src.executor.applier import PatchApplier
from backend.src.executor.validation_engine import ValidationEngine
from backend.src.models.change_request import ChangeRequest
from backend.src.models.workflow_result import (
    StageExecutionRecord,
    ValidationResult,
    WorkflowResult,
    WorkflowStage,
    WorkflowStatus,
)
from backend.src.repository.analyzer import RepositoryAnalyzer, RepositoryContext
from backend.src.repository.manager import IsolatedWorkspace, RepositoryManager
from backend.src.validators.change_plan_validator import ChangePlanValidator
from backend.src.validators.patch_plan_consistency_validator import PatchPlanConsistencyValidator
from backend.src.validators.patch_validator import PatchValidator

logger = logging.getLogger("changepilot.workflow.orchestrator")


class WorkflowOrchestrator:
    """Coordinates analysis, AI planning, deterministic validation, safe patching, and testing."""

    def __init__(
        self,
        repo_manager: Optional[RepositoryManager] = None,
        repo_analyzer: Optional[RepositoryAnalyzer] = None,
        change_analyst: Optional[ChangeAnalystAgent] = None,
        code_generator: Optional[CodeGeneratorAgent] = None,
    ):
        self.repo_manager = repo_manager or RepositoryManager()
        self.repo_analyzer = repo_analyzer or RepositoryAnalyzer()
        self.change_analyst = change_analyst or ChangeAnalystAgent()
        self.code_generator = code_generator or CodeGeneratorAgent()

    def execute(self, request: ChangeRequest) -> WorkflowResult:
        """Executes the complete autonomous software-change workflow."""
        execution_id = f"cp-exec-{uuid.uuid4().hex[:8]}"
        start_time = datetime.now(timezone.utc)
        start_timestamp = time.time()

        audit_trail: list[StageExecutionRecord] = []
        validation_results: list[ValidationResult] = []
        workspace: Optional[IsolatedWorkspace] = None

        current_stage = WorkflowStage.INITIALIZED
        logger.info(f"Starting execution {execution_id} for Story: {request.story_id} ('{request.title}')")

        def record_stage_start(stage: WorkflowStage, msg: str = "") -> StageExecutionRecord:
            nonlocal current_stage
            current_stage = stage
            record = StageExecutionRecord(
                stage=stage,
                status=WorkflowStatus.IN_PROGRESS,
                started_at=datetime.now(timezone.utc),
                message=msg
            )
            audit_trail.append(record)
            logger.info(f"[{execution_id}] Stage started: {stage.value} - {msg}")
            return record

        def record_stage_done(record: StageExecutionRecord, status: WorkflowStatus, msg: str = "", details: dict = None):
            record.status = status
            record.completed_at = datetime.now(timezone.utc)
            record.duration_ms = round((record.completed_at - record.started_at).total_seconds() * 1000, 2)
            record.message = msg
            if details:
                record.details.update(details)
            logger.info(f"[{execution_id}] Stage completed: {record.stage.value} in {record.duration_ms}ms ({status.value})")

        try:
            # -------------------------------------------------------------
            # Stage 1: Workspace Preparation
            # -------------------------------------------------------------
            stage_rec = record_stage_start(
                WorkflowStage.WORKSPACE_READY,
                f"Isolating repository from {request.repository_location}"
            )
            workspace = self.repo_manager.create_isolated_workspace(
                repository_location=request.repository_location,
                story_id=request.story_id,
                base_branch=request.base_branch,
                custom_branch=request.target_branch
            )
            record_stage_done(
                stage_rec,
                WorkflowStatus.SUCCESS,
                f"Workspace ready on branch {workspace.branch_name}",
                {"branch": workspace.branch_name, "path": str(workspace.path)}
            )

            # -------------------------------------------------------------
            # Stage 2: Deterministic Repository Analysis
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.REPO_ANALYZED, "Analyzing repository topology")
            repo_context: RepositoryContext = self.repo_analyzer.analyze(workspace.path)
            record_stage_done(
                stage_rec,
                WorkflowStatus.SUCCESS,
                f"Analyzed {len(repo_context.all_files)} files. Primary language: {repo_context.primary_language}",
                {
                    "primary_language": repo_context.primary_language,
                    "frameworks": repo_context.detected_frameworks,
                    "test_runner": repo_context.test_runner_command,
                    "file_count": len(repo_context.all_files)
                }
            )

            # -------------------------------------------------------------
            # Stage 3: AI Change Planning (Change Analyst Agent)
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.PLAN_GENERATED, "Change Analyst synthesizing ChangePlan")
            change_plan = self.change_analyst.analyze(request, repo_context)
            record_stage_done(
                stage_rec,
                WorkflowStatus.SUCCESS,
                f"ChangePlan proposed with {len(change_plan.planned_changes)} file modifications.",
                {"summary": change_plan.summary}
            )

            # -------------------------------------------------------------
            # Stage 4: Deterministic Plan Validation Gate
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.PLAN_VALIDATED, "Enforcing ChangePlan safety & consistency rules")
            plan_val_res = ChangePlanValidator.validate(change_plan, repo_context)
            validation_results.append(plan_val_res)

            if not plan_val_res.passed:
                record_stage_done(stage_rec, WorkflowStatus.REJECTED, "ChangePlan failed validation gates.", {"errors": plan_val_res.errors})
                return self._build_result(
                    execution_id=execution_id,
                    request=request,
                    status=WorkflowStatus.REJECTED,
                    stage=WorkflowStage.PLAN_VALIDATED,
                    start_time=start_time,
                    start_timestamp=start_timestamp,
                    audit_trail=audit_trail,
                    validation_results=validation_results,
                    change_plan=change_plan,
                    repo_context=repo_context,
                    error_msg=f"ChangePlan rejected: {'; '.join(plan_val_res.errors)}"
                )

            record_stage_done(stage_rec, WorkflowStatus.SUCCESS, "ChangePlan passed all validation gates.")

            # -------------------------------------------------------------
            # Stage 5: AI Code Generation (Code Generator Agent)
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.PATCH_GENERATED, "Code Generator generating FilePatches")
            patch_plan = self.code_generator.generate_patch(request, change_plan, repo_context)
            record_stage_done(
                stage_rec,
                WorkflowStatus.SUCCESS,
                f"Generated {len(patch_plan.file_patches)} file patches.",
                {"summary": patch_plan.summary}
            )

            # -------------------------------------------------------------
            # Stage 6: Deterministic Patch Validation & Consistency Gates
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.PATCH_VALIDATED, "Validating patch syntax, consistency & boundaries")
            
            # Check 1: Plan-to-Patch Consistency
            consistency_res = PatchPlanConsistencyValidator.validate(patch_plan, change_plan)
            validation_results.append(consistency_res)

            # Check 2: Patch Structural & Safety Validation
            patch_val_res = PatchValidator.validate(patch_plan, workspace.path)
            validation_results.append(patch_val_res)

            if not (consistency_res.passed and patch_val_res.passed):
                combined_errors = consistency_res.errors + patch_val_res.errors
                record_stage_done(stage_rec, WorkflowStatus.REJECTED, "Patch failed validation gates.", {"errors": combined_errors})
                return self._build_result(
                    execution_id=execution_id,
                    request=request,
                    status=WorkflowStatus.REJECTED,
                    stage=WorkflowStage.PATCH_VALIDATED,
                    start_time=start_time,
                    start_timestamp=start_timestamp,
                    audit_trail=audit_trail,
                    validation_results=validation_results,
                    change_plan=change_plan,
                    patch_plan=patch_plan,
                    repo_context=repo_context,
                    error_msg=f"Patch rejected: {'; '.join(combined_errors)}"
                )

            record_stage_done(stage_rec, WorkflowStatus.SUCCESS, "Patch passed all deterministic validation gates.")

            # -------------------------------------------------------------
            # Stage 7: Safe Patch Application
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.PATCH_APPLIED, "Applying patches inside isolated workspace")
            app_result = PatchApplier.apply_patch_plan(patch_plan, workspace.path)

            if not app_result.success:
                record_stage_done(stage_rec, WorkflowStatus.FAILED, "Patch application failed on filesystem.", {"errors": app_result.errors})
                return self._build_result(
                    execution_id=execution_id,
                    request=request,
                    status=WorkflowStatus.FAILED,
                    stage=WorkflowStage.PATCH_APPLIED,
                    start_time=start_time,
                    start_timestamp=start_timestamp,
                    audit_trail=audit_trail,
                    validation_results=validation_results,
                    change_plan=change_plan,
                    patch_plan=patch_plan,
                    repo_context=repo_context,
                    error_msg=f"Patch application failed: {'; '.join(app_result.errors)}"
                )

            # Commit the patch to the feature branch and get diff
            workspace.commit_changes(f"feat({request.story_id}): {request.title}")
            applied_diff = workspace.get_diff(base_branch=request.base_branch)

            record_stage_done(
                stage_rec,
                WorkflowStatus.SUCCESS,
                f"Applied {len(app_result.applied_files)} files. Diff generated ({len(applied_diff)} chars).",
                {"applied_count": len(app_result.applied_files)}
            )

            # -------------------------------------------------------------
            # Stage 8: Bounded Build & Test Execution
            # -------------------------------------------------------------
            stage_rec = record_stage_start(WorkflowStage.TESTS_EXECUTED, "Running automated verification tests")
            test_cmd = repo_context.test_runner_command or "pytest"
            test_exec_result = ValidationEngine.run_command(test_cmd, workspace.path)

            test_val_res = ValidationResult(
                validator_name="ValidationEngine.TestRunner",
                passed=test_exec_result.success,
                errors=[test_exec_result.error] if test_exec_result.error else ([] if test_exec_result.success else ["Tests failed."]),
                output=test_exec_result.stdout + ("\n" + test_exec_result.stderr if test_exec_result.stderr else ""),
                details={"return_code": test_exec_result.return_code, "duration": test_exec_result.duration_seconds}
            )
            validation_results.append(test_val_res)

            if not test_exec_result.success:
                record_stage_done(
                    stage_rec,
                    WorkflowStatus.FAILED,
                    f"Test execution failed (exit code {test_exec_result.return_code}).",
                    {"duration": test_exec_result.duration_seconds}
                )
                return self._build_result(
                    execution_id=execution_id,
                    request=request,
                    status=WorkflowStatus.FAILED,
                    stage=WorkflowStage.TESTS_EXECUTED,
                    start_time=start_time,
                    start_timestamp=start_timestamp,
                    audit_trail=audit_trail,
                    validation_results=validation_results,
                    change_plan=change_plan,
                    patch_plan=patch_plan,
                    applied_diff=applied_diff,
                    test_output=test_val_res.output,
                    test_passed=False,
                    branch_name=workspace.branch_name,
                    repo_context=repo_context,
                    error_msg=f"Automated test verification failed. Tests returned exit code {test_exec_result.return_code}."
                )

            record_stage_done(
                stage_rec,
                WorkflowStatus.SUCCESS,
                f"Automated tests passed in {test_exec_result.duration_seconds}s.",
                {"output_length": len(test_val_res.output or "")}
            )

            # -------------------------------------------------------------
            # Stage 9: Final Success Result
            # -------------------------------------------------------------
            final_rec = record_stage_start(WorkflowStage.COMPLETED, "Autonomous change verified and complete")
            record_stage_done(final_rec, WorkflowStatus.SUCCESS, "ChangePlan, Patch, and Tests fully verified.")

            return self._build_result(
                execution_id=execution_id,
                request=request,
                status=WorkflowStatus.SUCCESS,
                stage=WorkflowStage.COMPLETED,
                start_time=start_time,
                start_timestamp=start_timestamp,
                audit_trail=audit_trail,
                validation_results=validation_results,
                change_plan=change_plan,
                patch_plan=patch_plan,
                applied_diff=applied_diff,
                test_output=test_val_res.output,
                test_passed=True,
                branch_name=workspace.branch_name,
                repo_context=repo_context
            )

        except Exception as e:
            logger.exception(f"Unhandled error in workflow execution: {e}")
            fail_rec = StageExecutionRecord(
                stage=current_stage,
                status=WorkflowStatus.FAILED,
                completed_at=datetime.now(timezone.utc),
                message=f"Fatal exception: {str(e)}"
            )
            audit_trail.append(fail_rec)

            return self._build_result(
                execution_id=execution_id,
                request=request,
                status=WorkflowStatus.FAILED,
                stage=current_stage,
                start_time=start_time,
                start_timestamp=start_timestamp,
                audit_trail=audit_trail,
                validation_results=validation_results,
                error_msg=f"Unexpected pipeline error: {str(e)}"
            )

        finally:
            # Clean up workspace according to policy (preserve on debug/failure if desired, clean by default)
            if workspace and not settings.app_env == "test_preserve":
                try:
                    workspace.cleanup()
                except Exception as ex:
                    logger.warning(f"Workspace cleanup error (non-fatal): {ex}")

    def _build_result(
        self,
        execution_id: str,
        request: ChangeRequest,
        status: WorkflowStatus,
        stage: WorkflowStage,
        start_time: datetime,
        start_timestamp: float,
        audit_trail: list[StageExecutionRecord],
        validation_results: list[ValidationResult],
        change_plan=None,
        patch_plan=None,
        applied_diff=None,
        test_output=None,
        test_passed=None,
        branch_name=None,
        repo_context: Optional[RepositoryContext] = None,
        error_msg: Optional[str] = None
    ) -> WorkflowResult:
        """Constructs a consolidated WorkflowResult."""
        total_duration = round((time.time() - start_timestamp) * 1000, 2)
        repo_summary = None
        if repo_context:
            repo_summary = {
                "primary_language": repo_context.primary_language,
                "detected_languages": repo_context.detected_languages,
                "detected_frameworks": repo_context.detected_frameworks,
                "test_runner": repo_context.test_runner_command,
                "total_files": len(repo_context.all_files),
            }

        return WorkflowResult(
            execution_id=execution_id,
            request_id=request.request_id,
            story_id=request.story_id,
            status=status,
            current_stage=stage,
            success=(status == WorkflowStatus.SUCCESS),
            started_at=start_time,
            completed_at=datetime.now(timezone.utc),
            total_duration_ms=total_duration,
            repository_summary=repo_summary,
            change_plan=change_plan,
            patch_plan=patch_plan,
            validation_results=validation_results,
            applied_diff=applied_diff,
            test_output=test_output,
            test_passed=test_passed,
            branch_name=branch_name,
            audit_trail=audit_trail,
            error_stage=stage if status != WorkflowStatus.SUCCESS else None,
            error_message=error_msg
        )
