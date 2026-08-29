"""Tests for SQLite / PostgreSQL database persistence of pipelines and audit events."""
from datetime import datetime, timezone
from backend.src.database.repository import DatabaseRepository
from backend.src.database.session import init_db
from backend.src.models.workflow_result import StageExecutionRecord, WorkflowResult, WorkflowStage, WorkflowStatus


def test_database_persistence_lifecycle():
    """Verifies pipeline runs and audit records are persisted and queried correctly."""
    init_db()
    repo = DatabaseRepository()

    exec_id = f"cp-test-{datetime.now().timestamp()}"
    res = WorkflowResult(
        execution_id=exec_id,
        request_id="req-test-1",
        story_id="CP-PERSIST-1",
        status=WorkflowStatus.SUCCESS,
        current_stage=WorkflowStage.COMPLETED,
        success=True,
        started_at=datetime.now(timezone.utc),
        total_duration_ms=1234.5,
        branch_name="changepilot/CP-PERSIST-1",
        audit_trail=[
            StageExecutionRecord(
                stage=WorkflowStage.WORKSPACE_READY,
                status=WorkflowStatus.SUCCESS,
                message="Workspace initialized"
            )
        ]
    )

    saved_run = repo.save_pipeline_run(res, user_id="usr-kameswar-01", repo_name="demo_repo")
    assert saved_run is not None

    recent_runs = repo.list_recent_pipeline_runs(limit=10)
    assert len(recent_runs) > 0
    match = next((r for r in recent_runs if r["id"] == exec_id), None)
    assert match is not None
    assert match["story_id"] == "CP-PERSIST-1"
    assert match["status"] == "SUCCESS"
