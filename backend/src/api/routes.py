"""API routes for ChangePilot."""
import logging
import uuid
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.src.config import settings
from backend.src.models.change_request import ChangeRequest
from backend.src.models.workflow_result import WorkflowResult
from backend.src.repository.analyzer import RepositoryAnalyzer, RepositoryContext
from backend.src.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger("changepilot.api.routes")
router = APIRouter()

orchestrator = WorkflowOrchestrator()
analyzer = RepositoryAnalyzer()


class AnalyzeRepoRequest(BaseModel):
    repository_location: str = Field(..., description="Local path or Git repository URL to inspect")


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    vertex_ai_configured: bool
    version: str


@router.get("/health", response_model=HealthResponse, tags=["Health"])
@router.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint providing runtime and model configuration status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        environment=settings.app_env,
        vertex_ai_configured=settings.is_vertex_configured(),
        version="1.0.0"
    )


@router.post("/api/repository/analyze", response_model=RepositoryContext, tags=["Repository"])
async def analyze_repository(
    request: AnalyzeRepoRequest,
    x_correlation_id: str = Header(default=None)
):
    """Analyzes a repository topology, detecting languages, frameworks, tests, and manifests."""
    correlation_id = x_correlation_id or str(uuid.uuid4())
    logger.info(f"[{correlation_id}] Repository analysis requested for: {request.repository_location}")

    try:
        validated_loc = orchestrator.repo_manager.validate_repository_location(request.repository_location)
        local_path = Path(validated_loc)

        if local_path.exists() and local_path.is_dir():
            return analyzer.analyze(local_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direct analysis requires an accessible local repository path. Remote URLs are analyzed during full execution."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{correlation_id}] Repository analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to analyze repository: {str(e)}"
        )


@router.post("/api/changes/execute", response_model=WorkflowResult, tags=["Changes"])
async def execute_change_request(
    request: ChangeRequest,
    x_correlation_id: str = Header(default=None)
):
    """Executes the full autonomous software change workflow."""
    correlation_id = x_correlation_id or request.request_id
    logger.info(f"[{correlation_id}] Initiating execution for story: {request.story_id}")

    try:
        result = orchestrator.execute(request)
        return result
    except Exception as e:
        logger.exception(f"[{correlation_id}] Execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution encountered an internal error: {str(e)}"
        )
