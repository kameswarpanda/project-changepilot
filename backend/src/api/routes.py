"""API routes for ChangePilot including Auth, Authorization, Repositories, and Change Pipelines."""
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.src.auth.authorization import AccessLevel, authz_service, RepositoryPermission
from backend.src.auth.dependencies import get_current_user, get_optional_user
from backend.src.auth.models import AuthSessionResponse, LoginRequest, RegisterRequest, User
from backend.src.auth.service import auth_service
from backend.src.config import settings
from backend.src.database.repository import db_repository
from backend.src.models.change_request import ChangeRequest
from backend.src.models.workflow_result import WorkflowResult
from backend.src.repository.analyzer import RepositoryAnalyzer, RepositoryContext
from backend.src.repository.github_app import github_app_client
from backend.src.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger("changepilot.api.routes")
router = APIRouter()

orchestrator = WorkflowOrchestrator()
analyzer = RepositoryAnalyzer()


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class AnalyzeRepoRequest(BaseModel):
    repository_location: str = Field(..., description="Local path or Git repository URL to inspect")


class ConnectRepoRequest(BaseModel):
    repository_id: str
    repository_name: str
    provider: str = "github"
    base_branch: str = "main"
    is_public: bool = False


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    vertex_ai_configured: bool
    version: str


# -----------------------------------------------------------------------------
# Health & Status Endpoints
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Identity & Authentication Endpoints
# -----------------------------------------------------------------------------
@router.post("/api/auth/register", response_model=AuthSessionResponse, tags=["Auth"])
async def register(req: RegisterRequest):
    """Registers a new user with Email, Password, and Full Name."""
    try:
        session = auth_service.register_user(req)
        return session
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed.")


@router.post("/api/auth/login", response_model=AuthSessionResponse, tags=["Auth"])
async def login(req: LoginRequest):
    """Authenticates user with Google Identity, Email/Password, or Demo profile."""
    try:
        session = await auth_service.authenticate(req)
        return session
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error during login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication failed.")


@router.get("/api/auth/me", response_model=User, tags=["Auth"])
async def get_me(user: User = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    return user


# -----------------------------------------------------------------------------
# Repository Management & Discovery Endpoints
# -----------------------------------------------------------------------------
@router.get("/api/repositories", tags=["Repositories"])
async def list_repositories(user: User = Depends(get_current_user)):
    """Lists repositories accessible to the authenticated user."""
    perms = authz_service.list_accessible_repositories(user)
    gh_repos = github_app_client.list_repositories(user.id)
    return {
        "user": user.username,
        "repositories": gh_repos,
        "permissions": perms
    }


@router.get("/api/repositories/{repo_id}/branches", response_model=List[str], tags=["Repositories"])
async def list_repository_branches(repo_id: str, user: User = Depends(get_current_user)):
    """Discovers available branches for a repository."""
    return github_app_client.list_branches(repo_id)


@router.post("/api/repositories/connect", tags=["Repositories"])
async def connect_repository(req: ConnectRepoRequest, user: User = Depends(get_current_user)):
    """Connects a new repository to ChangePilot for the authenticated user."""
    perm = RepositoryPermission(
        repository_id=req.repository_id,
        repository_name=req.repository_name,
        owner_user_id=user.id,
        access_levels={AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE},
        is_public=req.is_public
    )
    authz_service.register_repository(user.id, perm)
    logger.info(f"User {user.username} connected repository {req.repository_name}")
    return {"status": "connected", "repository": req.repository_name}


@router.post("/api/repository/analyze", response_model=RepositoryContext, tags=["Repositories"])
async def analyze_repository(
    request: AnalyzeRepoRequest,
    user: User = Depends(get_current_user),
    x_correlation_id: str = Header(default=None)
):
    """Analyzes a repository topology, detecting languages, frameworks, tests, and manifests."""
    correlation_id = x_correlation_id or str(uuid.uuid4())
    logger.info(f"[{correlation_id}] Repository analysis requested by {user.username} for: {request.repository_location}")

    # Enforce READ authorization on repository
    if not authz_service.has_repository_access(user, request.repository_location, AccessLevel.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User '{user.username}' is not authorized to access repository '{request.repository_location}'."
        )

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


# -----------------------------------------------------------------------------
# Change Pipeline Endpoints
# -----------------------------------------------------------------------------
@router.get("/api/pipelines", tags=["Changes"])
async def list_pipelines(limit: int = 20, user: User = Depends(get_current_user)):
    """Retrieves historical pipeline execution runs."""
    return db_repository.list_recent_pipeline_runs(limit=limit)


@router.post("/api/changes/execute", response_model=WorkflowResult, tags=["Changes"])
async def execute_change_request(
    request: ChangeRequest,
    user: User = Depends(get_current_user),
    x_correlation_id: str = Header(default=None)
):
    """Executes the full autonomous software change workflow."""
    correlation_id = x_correlation_id or request.request_id
    logger.info(f"[{correlation_id}] Initiating execution for story: {request.story_id} by user: {user.username}")

    # Enforce EXECUTE authorization on repository
    if not authz_service.has_repository_access(user, request.repository_location, AccessLevel.EXECUTE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User '{user.username}' is not authorized to execute changes on '{request.repository_location}'."
        )

    try:
        result = orchestrator.execute(request, user_id=user.id)
        return result
    except Exception as e:
        logger.exception(f"[{correlation_id}] Execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution encountered an internal error: {str(e)}"
        )
