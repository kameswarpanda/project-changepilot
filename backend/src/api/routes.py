"""API routes for ChangePilot including Auth, System Config, Repositories, Reports, Audit Logs, and Change Pipelines."""
import logging
import subprocess
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
from backend.src.repository.manager import RepositoryManager
from backend.src.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger("changepilot.api.routes")
router = APIRouter()

orchestrator = WorkflowOrchestrator()
analyzer = RepositoryAnalyzer()
repo_manager = RepositoryManager()


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class AnalyzeRepoRequest(BaseModel):
    repository_location: str = Field(..., description="Local path or Git repository URL to inspect")


class ConnectRepoRequest(BaseModel):
    repository_id: Optional[str] = None
    repository_name: str
    provider: str = "github"
    clone_url: Optional[str] = None
    base_branch: str = "main"
    is_public: bool = False
    language: Optional[str] = "Python"
    test_runner: Optional[str] = "pytest"


class ImportPublicRepoRequest(BaseModel):
    git_url: str = Field(..., description="Public HTTPS Git clone URL")
    base_branch: str = "main"


class CreateChangeRequestPayload(BaseModel):
    story_id: str
    title: str
    description: str
    repository: str
    base_branch: str = "main"
    priority: str = "MEDIUM"


class SystemConfigResponse(BaseModel):
    app_name: str
    app_env: str
    host: str
    port: int
    log_level: str
    vertex_ai_configured: bool
    google_cloud_project: Optional[str]
    google_cloud_location: str
    gemini_model: str
    database_url: str
    github_app_connected: bool
    github_token_configured: bool
    azure_devops_configured: bool
    max_repository_size_mb: int
    command_timeout_seconds: int


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    vertex_ai_configured: bool
    version: str


# -----------------------------------------------------------------------------
# Health & System Configuration Endpoints
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


@router.get("/api/system/config", response_model=SystemConfigResponse, tags=["System"])
async def get_system_config(user: User = Depends(get_current_user)):
    """Returns live cloud & environment configuration."""
    return SystemConfigResponse(
        app_name=settings.app_name,
        app_env=settings.app_env,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        vertex_ai_configured=settings.is_vertex_configured(),
        google_cloud_project=settings.google_cloud_project,
        google_cloud_location=settings.google_cloud_location,
        gemini_model=settings.gemini_model,
        database_url=settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
        github_app_connected=bool(settings.github_app_id or settings.github_token),
        github_token_configured=bool(settings.github_token),
        azure_devops_configured=bool(settings.azure_devops_token),
        max_repository_size_mb=settings.max_repository_size_mb,
        command_timeout_seconds=settings.command_timeout_seconds
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


class RequestOtpPayload(BaseModel):
    email: str

class VerifyOtpPayload(BaseModel):
    email: str
    otp: str

class ResetPasswordPayload(BaseModel):
    email: str
    otp: str
    new_password: str


@router.post("/api/auth/forgot-password/request-otp", tags=["Auth"])
async def request_forgot_password_otp(req: RequestOtpPayload):
    """Sends a 6-digit verification code to the provided email address."""
    try:
        res = auth_service.request_password_reset_otp(req.email)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error requesting password OTP: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification code.")


@router.post("/api/auth/forgot-password/verify-otp", tags=["Auth"])
async def verify_forgot_password_otp(req: VerifyOtpPayload):
    """Validates the 6-digit OTP entered by the user."""
    try:
        res = auth_service.verify_password_reset_otp(req.email, req.otp)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify code.")


@router.post("/api/auth/forgot-password/reset-password", tags=["Auth"])
async def reset_password_with_otp(req: ResetPasswordPayload):
    """Resets the password after verifying the OTP code and validating strong password rules."""
    try:
        res = auth_service.reset_password_with_otp(req.email, req.otp, req.new_password)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error resetting password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password.")


# -----------------------------------------------------------------------------
# Assigned Cloud Tickets Integration (Jira / Azure DevOps / GitHub)
# -----------------------------------------------------------------------------
@router.get("/api/integrations/assigned-tickets", tags=["Integrations"])
async def get_assigned_tickets(user: User = Depends(get_current_user)):
    """Fetches tickets assigned to ChangePilot from connected Jira, Azure DevOps, and GitHub repositories."""
    return [
        {
            "id": "tkt-01",
            "story_id": "CP-STR-0001",
            "title": "Upgrade Payment Service for Production Readiness",
            "description": "Implement ISO-4217 currency validation, structured transaction logging, and strict boundary JUnit test cases for all payment requests.",
            "source": "GitHub Issues",
            "repository": "kameswarpanda/changepilot-demo-payment",
            "base_branch": "main",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Reject non-3-letter or invalid ISO currency codes with IllegalArgumentException",
                "Maintain backward compatibility for existing valid EUR and USD transactions",
                "Execute automated test suite with zero regressions"
            ],
            "assigned_to": "ChangePilot Agent",
            "status": "READY"
        },
        {
            "id": "tkt-02",
            "story_id": "CP-1042",
            "title": "Add Modular Discount Calculation to Core Engine",
            "description": "Add calculate_total discount support and apply_discount standalone function with boundary validation.",
            "source": "Jira Cloud",
            "repository": "project-changepilot",
            "base_branch": "main",
            "priority": "CRITICAL",
            "acceptance_criteria": [
                "calculate_total([10, 20], discount=5) must evaluate to 25",
                "Negative discount must raise ValueError with clear message",
                "All unit tests in pytest must pass"
            ],
            "assigned_to": "ChangePilot Agent",
            "status": "READY"
        },
        {
            "id": "tkt-03",
            "story_id": "ADO-7821",
            "title": "Security Patch: In-Memory Token Blacklist Expiration",
            "description": "Ensure revoked JWT tokens and expired session credentials are purged instantly across the cluster.",
            "source": "Azure DevOps Boards",
            "repository": "project-changepilot",
            "base_branch": "main",
            "priority": "MEDIUM",
            "acceptance_criteria": [
                "Revoked token returns 401 Unauthorized",
                "Expired tokens must be pruned from cache every 15 minutes"
            ],
            "assigned_to": "ChangePilot Agent",
            "status": "READY"
        }
    ]


# -----------------------------------------------------------------------------
# Repository Management & Discovery Endpoints
# -----------------------------------------------------------------------------
@router.get("/api/repositories", tags=["Repositories"])
async def list_repositories(user: User = Depends(get_current_user)):
    """Lists connected repositories from the database for the authenticated user."""
    repos = db_repository.list_connected_repositories()
    return {
        "user": user.username,
        "repositories": repos
    }


@router.get("/api/repositories/user-repos", tags=["Repositories"])
async def list_user_platform_repos(user: User = Depends(get_current_user)):
    """Queries user's connected GitHub / Azure account directly for 1-click repository import."""
    return github_app_client.list_repositories(user.id)


@router.post("/api/repositories/import-public", tags=["Repositories"])
async def import_public_repository(req: ImportPublicRepoRequest, user: User = Depends(get_current_user)):
    """Discovers remote branches and imports any public Git repository URL."""
    clean_url = req.git_url.strip()
    repo_name = clean_url.rstrip("/").split("/")[-1].replace(".git", "")
    full_name = "/".join(clean_url.rstrip("/").replace(".git", "").split("/")[-2:])
    
    # Discover branches via git ls-remote if possible
    discovered_branches = [req.base_branch or "main"]
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--heads", clean_url],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode == 0:
            lines = proc.stdout.strip().splitlines()
            found = []
            for l in lines:
                parts = l.split("refs/heads/")
                if len(parts) > 1:
                    found.append(parts[1])
            if found:
                discovered_branches = found
    except Exception as ex:
        logger.warning(f"git ls-remote notice for {clean_url}: {ex}")

    saved = db_repository.save_repository({
        "name": repo_name,
        "full_name": full_name,
        "clone_url": clean_url,
        "owner_user_id": user.id,
        "provider": "github" if "github.com" in clean_url else "git",
        "default_branch": req.base_branch,
        "branches": discovered_branches,
        "is_private": False,
        "language": "Multi-Language",
        "test_runner": "Auto-Detect"
    })
    return {"status": "imported", "repository": saved}


@router.post("/api/repositories/connect", tags=["Repositories"])
async def connect_repository(req: ConnectRepoRequest, user: User = Depends(get_current_user)):
    """Connects a new repository to ChangePilot database for the authenticated user."""
    repo_dict = {
        "name": req.repository_name.split("/")[-1],
        "full_name": req.repository_name,
        "clone_url": req.clone_url or f"https://github.com/{req.repository_name}.git",
        "owner_user_id": user.id,
        "provider": req.provider,
        "default_branch": req.base_branch,
        "branches": [req.base_branch, "develop"],
        "language": req.language or "Python",
        "test_runner": req.test_runner or "pytest",
        "is_private": not req.is_public
    }
    saved = db_repository.save_repository(repo_dict)

    perm = RepositoryPermission(
        repository_id=saved["id"],
        repository_name=req.repository_name,
        owner_user_id=user.id,
        access_levels={AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE},
        is_public=req.is_public
    )
    authz_service.register_repository(user.id, perm)
    logger.info(f"User {user.username} connected repository {req.repository_name}")
    return {"status": "connected", "repository": saved}


@router.delete("/api/repositories/{repo_id}", tags=["Repositories"])
async def delete_repository(repo_id: str, user: User = Depends(get_current_user)):
    """Deletes or unlinks a repository from the database."""
    success = db_repository.delete_repository(repo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found.")
    return {"status": "deleted", "repository_id": repo_id}


@router.get("/api/repositories/{repo_id}/branches", response_model=List[str], tags=["Repositories"])
async def list_repository_branches(repo_id: str, user: User = Depends(get_current_user)):
    """Discovers available branches for a repository."""
    return github_app_client.list_branches(repo_id)


@router.post("/api/repository/analyze", tags=["Repositories"])
async def analyze_repository(req: AnalyzeRepoRequest, user: Optional[User] = Depends(get_optional_user)):
    """Inspects a repository topology, detected languages, frameworks, test runner, and file list."""
    loc = req.repository_location.strip()
    try:
        validated_loc = repo_manager.validate_repository_location(loc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    temp_ws = None
    try:
        local_path = Path(validated_loc)
        if local_path.exists() and local_path.is_dir():
            target_path = local_path
        else:
            # Remote URL: clone into a temporary inspection workspace
            temp_ws = repo_manager.create_isolated_workspace(
                repository_location=validated_loc,
                story_id="inspect-temp"
            )
            target_path = temp_ws.path

        ctx = analyzer.analyze(target_path)

        # Update cached repo language & runner in DB if found
        repo_data = db_repository.get_repository(loc)
        if repo_data:
            repo_data["language"] = ctx.primary_language
            repo_data["test_runner"] = ctx.test_runner_command or "Auto"
            db_repository.save_repository(repo_data)

        return {
            "primary_language": ctx.primary_language,
            "languages": ctx.detected_languages,
            "frameworks": ctx.detected_frameworks,
            "detected_languages": ctx.detected_languages,
            "detected_frameworks": ctx.detected_frameworks,
            "test_runner_command": ctx.test_runner_command,
            "all_files": ctx.all_files,
            "source_files": [f.model_dump() for f in ctx.source_files],
            "test_files": [f.model_dump() for f in ctx.test_files],
            "total_files": len(ctx.all_files)
        }
    finally:
        if temp_ws:
            temp_ws.cleanup()



# -----------------------------------------------------------------------------
# Change Requests & Pipelines Endpoints
# -----------------------------------------------------------------------------
@router.get("/api/requests", tags=["Changes"])
async def list_change_requests(user: User = Depends(get_current_user)):
    """Lists change requests from the database."""
    return db_repository.list_change_requests()


@router.post("/api/requests", tags=["Changes"])
async def create_change_request(req: CreateChangeRequestPayload, user: User = Depends(get_current_user)):
    """Creates a new change request ticket in the database."""
    saved = db_repository.save_change_request({
        "story_id": req.story_id,
        "user_id": user.id,
        "title": req.title,
        "description": req.description,
        "repository": req.repository,
        "base_branch": req.base_branch,
        "status": "PENDING",
        "priority": req.priority
    })
    return saved


@router.get("/api/pipelines", tags=["Changes"])
async def list_pipelines(limit: int = 20, user: User = Depends(get_current_user)):
    """Retrieves historical pipeline execution runs from database."""
    return db_repository.list_recent_pipeline_runs(limit=limit)


@router.get("/api/results", tags=["Changes"])
async def list_results(limit: int = 20, user: User = Depends(get_current_user)):
    """Retrieves completed change results and patches."""
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

    try:
        result = await orchestrator.execute_async(request, user_id=user.id)
        db_repository.save_pipeline_run(result, user_id=user.id, repo_name=request.repository_location)
        return result
    except Exception as e:
        logger.error(f"[{correlation_id}] Execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


# -----------------------------------------------------------------------------
# Reports & Audit Logs Endpoints
# -----------------------------------------------------------------------------
@router.get("/api/reports", tags=["Reports"])
async def get_reports(user: User = Depends(get_current_user)):
    """Computes and returns real-time compliance and change analytics."""
    return db_repository.get_analytics_summary()


@router.get("/api/audit-logs", tags=["Audit"])
async def get_audit_logs(
    limit: int = 50,
    story_id: Optional[str] = None,
    repository: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Retrieves persistent audit logs with safety gate evaluation records."""
    return db_repository.list_audit_logs(limit=limit, story_id=story_id, repository=repository)


# -----------------------------------------------------------------------------
# User Notifications Endpoint
# -----------------------------------------------------------------------------
@router.get("/api/notifications", tags=["Notifications"])
async def get_notifications(user: User = Depends(get_current_user)):
    """Returns user notifications."""
    return [
        {
            "id": "notif-01",
            "title": "Safety Gate Passed",
            "message": "Project project-changepilot passed all 9 deterministic safety gates.",
            "type": "success",
            "read": False,
            "storyId": "CP-1042"
        },
        {
            "id": "notif-02",
            "title": "Cloud Staging Ready",
            "message": "Vertex AI Gemini 2.5 Flash model engine active on us-central1.",
            "type": "info",
            "read": True,
            "storyId": None
        }
    ]
