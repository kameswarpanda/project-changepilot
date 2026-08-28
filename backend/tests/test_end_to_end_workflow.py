"""End-to-end integration and failure scenario tests for ChangePilot."""
import pytest
from pathlib import Path

from backend.src.agents.change_analyst import ChangeAnalystAgent
from backend.src.agents.code_generator import CodeGeneratorAgent
from backend.src.models.change_plan import ChangePlan, ChangeType, PlannedChange
from backend.src.models.change_request import ChangeRequest
from backend.src.models.patch_plan import FilePatch, PatchPlan
from backend.src.models.workflow_result import WorkflowStage, WorkflowStatus
from backend.src.workflow.orchestrator import WorkflowOrchestrator


def test_e2e_demo_calculator_success():
    """Tests the canonical hackathon demo flow: flat discount on calculator with pytest validation."""
    demo_repo_path = Path(__file__).resolve().parent.parent.parent / "demo_repo"

    request = ChangeRequest(
        story_id="CP-DEMO-1",
        title="Add optional flat monetary discount to calculator",
        description=(
            "Add an optional flat monetary discount parameter to the calculate_total function. "
            "Preserve existing callers when discount is None. Reject negative discounts and "
            "discounts greater than calculated total with ValueError. Update unit tests."
        ),
        repository_location=str(demo_repo_path)
    )

    orchestrator = WorkflowOrchestrator()
    result = orchestrator.execute(request)

    assert result.success is True
    assert result.status == WorkflowStatus.SUCCESS
    assert result.current_stage == WorkflowStage.COMPLETED
    assert result.test_passed is True
    assert result.applied_diff is not None
    assert "def apply_discount" in result.applied_diff or "discount" in result.applied_diff
    assert len(result.audit_trail) >= 8


def test_failure_scenario_invalid_repo_location():
    """Verify malformed/invalid repo location fails gracefully before mutation."""
    request = ChangeRequest(
        story_id="CP-FAIL-1",
        title="Invalid repo test",
        description="Try to mutate invalid location",
        repository_location="/path/to/nonexistent/directory"
    )

    orchestrator = WorkflowOrchestrator()
    result = orchestrator.execute(request)

    assert result.success is False
    assert result.status == WorkflowStatus.FAILED
    assert result.error_stage == WorkflowStage.WORKSPACE_READY


def test_failure_scenario_plan_validation_rejection(tmp_path):
    """Verify orchestrator fails closed when ChangePlan proposes ungrounded file modification."""
    (tmp_path / "app.py").write_text("def run(): pass", encoding="utf-8")

    class BadAnalyst(ChangeAnalystAgent):
        def analyze(self, req, ctx):
            return ChangePlan(
                story_id=req.story_id,
                summary="Bad plan modifying imaginary file",
                planned_changes=[
                    PlannedChange(
                        file_path="non_existent_file.py",
                        change_type=ChangeType.MODIFY,
                        description="Try to modify missing file"
                    )
                ]
            )

    orchestrator = WorkflowOrchestrator(change_analyst=BadAnalyst())
    request = ChangeRequest(
        story_id="CP-FAIL-2",
        title="Hallucinated file plan",
        description="Test plan rejection",
        repository_location=str(tmp_path)
    )

    result = orchestrator.execute(request)
    assert result.success is False
    assert result.status == WorkflowStatus.REJECTED
    assert result.current_stage == WorkflowStage.PLAN_VALIDATED
    assert "Cannot MODIFY file" in result.error_message


def test_failure_scenario_patch_consistency_rejection(tmp_path):
    """Verify orchestrator rejects patch that touches unapproved files."""
    (tmp_path / "app.py").write_text("def run(): pass", encoding="utf-8")

    class BadCodeGenerator(CodeGeneratorAgent):
        def generate_patch(self, req, plan, ctx):
            return PatchPlan(
                story_id=plan.story_id,
                summary="Rogue patch",
                file_patches=[
                    FilePatch(
                        file_path="unapproved_file.py",
                        change_type=ChangeType.CREATE,
                        content="evil = True"
                    )
                ]
            )

    orchestrator = WorkflowOrchestrator(code_generator=BadCodeGenerator())
    request = ChangeRequest(
        story_id="CP-FAIL-3",
        title="Inconsistent patch test",
        description="Test patch consistency validator rejection",
        repository_location=str(tmp_path)
    )

    result = orchestrator.execute(request)
    assert result.success is False
    assert result.status == WorkflowStatus.REJECTED
    assert result.current_stage == WorkflowStage.PATCH_VALIDATED
    assert "NOT approved in ChangePlan" in result.error_message
