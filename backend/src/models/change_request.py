"""ChangeRequest model representing an incoming software change request."""
from enum import Enum
import uuid
from typing import Optional
from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    ANALYZE_ONLY = "ANALYZE_ONLY"
    LOCAL_WORKSPACE = "LOCAL_WORKSPACE"
    BRANCH_COMMIT_PR = "BRANCH_COMMIT_PR"


class ChangeRequest(BaseModel):
    """Developer submitted change request."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request/correlation ID")
    story_id: str = Field(..., description="Story or ticket identifier (e.g. CP-101)")
    title: str = Field(..., min_length=3, max_length=200, description="Short title of the change")
    description: str = Field(..., min_length=10, description="Detailed requirements for the code change")
    repository_location: str = Field(..., description="Local filesystem path or safe remote Git URL")
    base_branch: str = Field(default="main", description="Target base branch e.g. main / develop")
    target_branch: Optional[str] = Field(default=None, description="Custom branch name for changes")
    execution_mode: ExecutionMode = Field(default=ExecutionMode.BRANCH_COMMIT_PR, description="Execution mode")
    auto_apply: bool = Field(default=True, description="Whether to apply and test changes automatically")
