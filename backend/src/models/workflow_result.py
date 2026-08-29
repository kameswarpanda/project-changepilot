"""WorkflowResult and execution lifecycle status models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .change_plan import ChangePlan
from .patch_plan import PatchPlan


class WorkflowStage(str, Enum):
    INITIALIZED = "INITIALIZED"
    WORKSPACE_READY = "WORKSPACE_READY"
    REPO_ANALYZED = "REPO_ANALYZED"
    PLAN_GENERATED = "PLAN_GENERATED"
    PLAN_VALIDATED = "PLAN_VALIDATED"
    PATCH_GENERATED = "PATCH_GENERATED"
    PATCH_VALIDATED = "PATCH_VALIDATED"
    PATCH_APPLIED = "PATCH_APPLIED"
    TESTS_EXECUTED = "TESTS_EXECUTED"
    BRANCH_COMMITTED = "BRANCH_COMMITTED"
    PULL_REQUEST_CREATED = "PULL_REQUEST_CREATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class StageExecutionRecord(BaseModel):
    """Audit log entry for an individual workflow stage."""
    stage: WorkflowStage
    status: WorkflowStatus
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of a deterministic validation check or test run."""
    validator_name: str
    passed: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    output: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Consolidated end-to-end result of a ChangePilot workflow execution."""
    execution_id: str
    request_id: str
    story_id: str
    status: WorkflowStatus
    current_stage: WorkflowStage
    success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[float] = None

    # Intermediate and final outputs
    repository_summary: Optional[Dict[str, Any]] = None
    change_plan: Optional[ChangePlan] = None
    patch_plan: Optional[PatchPlan] = None
    validation_results: List[ValidationResult] = Field(default_factory=list)
    applied_diff: Optional[str] = None
    test_output: Optional[str] = None
    test_passed: Optional[bool] = None
    branch_name: Optional[str] = None
    commit_sha: Optional[str] = None
    pull_request: Optional[Dict[str, Any]] = None

    # Audit trail and diagnostics
    audit_trail: List[StageExecutionRecord] = Field(default_factory=list)
    error_stage: Optional[WorkflowStage] = None
    error_message: Optional[str] = None
