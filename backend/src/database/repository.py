"""Repository CRUD layer for ChangePilot persistence."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.src.database.models import (
    AssignedTicketModel,
    AuditLogModel,
    ChangeRequestModel,
    PasswordResetOtpModel,
    PipelineRunModel,
    RepositoryModel,
    UserIntegrationModel,
    UserModel,
    Base
)
from backend.src.database.session import SessionLocal, engine
from backend.src.models.workflow_result import WorkflowResult
from backend.src.config import settings

logger = logging.getLogger("changepilot.database.repository")


class DatabaseRepository:
    """Provides high-level persistent operations across databases."""

    def __init__(self):
        # Auto-create tables on initialization
        try:
            Base.metadata.create_all(bind=engine)
            self._migrate_schema()
            self._seed_initial_data()
        except Exception as e:
            logger.warning(f"Database table initialization notice: {e}")

    def _migrate_schema(self):
        """Auto-migrates columns in both SQLite and PostgreSQL on application startup."""
        try:
            with engine.connect() as conn:
                if settings.database_url.startswith("sqlite"):
                    res = conn.execute(text("PRAGMA table_info(users)"))
                    cols = [row[1] for row in res.fetchall()]
                    if cols and "password_hash" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)"))
                        conn.commit()
                        logger.info("Auto-migrated 'password_hash' column into SQLite users table.")

                    # Ensure existing default users have a valid password hash
                    import hashlib
                    default_hash = hashlib.sha256(("cp_salt_2026_" + "changepilot2026").encode("utf-8")).hexdigest()
                    conn.execute(text("UPDATE users SET password_hash = :ph WHERE password_hash IS NULL"), {"ph": default_hash})
                    conn.commit()
                else:
                    # PostgreSQL / Cloud SQL auto-migrations
                    try:
                        conn.execute(text("ALTER TABLE pipeline_runs ALTER COLUMN title TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE pipeline_runs ALTER COLUMN repository TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE pipeline_runs ALTER COLUMN branch_name TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE pipeline_runs ALTER COLUMN current_stage TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE change_requests ALTER COLUMN title TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE change_requests ALTER COLUMN repository TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE assigned_tickets ALTER COLUMN title TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE assigned_tickets ALTER COLUMN repository TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN action TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN safety_rule TYPE TEXT;"))
                        conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN target_repository TYPE TEXT;"))
                        conn.commit()
                        logger.info("Auto-migrated all PostgreSQL Cloud SQL text columns to TEXT.")
                    except Exception as pg_err:
                        logger.debug(f"PostgreSQL column migration notice: {pg_err}")
        except Exception as e:
            logger.debug(f"Migration check notice: {e}")

    def _seed_initial_data(self):
        """Seeds initial connected repositories and change requests if empty."""
        session: Session = SessionLocal()
        try:
            # Seed users if none exist
            if session.query(UserModel).count() == 0:
                import hashlib
                def _hash_pwd(pwd: str) -> str:
                    return hashlib.sha256(("cp_salt_2026_" + pwd).encode("utf-8")).hexdigest()

                users = [
                    UserModel(
                        id="usr-kameswar-01",
                        identity_provider_id="google-kameswar-2026",
                        username="kameswar",
                        display_name="Kameswar Panda",
                        email="kameswar@changepilot.dev",
                        password_hash=_hash_pwd("changepilot2026"),
                        avatar_url="https://avatars.githubusercontent.com/u/583231",
                        provider="google",
                        roles=["admin", "developer"]
                    ),
                    UserModel(
                        id="usr-alex-02",
                        identity_provider_id="google-alex-mercer",
                        username="alex.mercer",
                        display_name="Alex Mercer",
                        email="alex@changepilot.dev",
                        password_hash=_hash_pwd("changepilot2026"),
                        avatar_url=None,
                        provider="google",
                        roles=["developer"]
                    )
                ]
                for u in users:
                    session.merge(u)

            # Seed repositories if none exist
            if session.query(RepositoryModel).count() == 0:
                repos = [
                    RepositoryModel(
                        id="repo-changepilot",
                        name="project-changepilot",
                        full_name="kameswarpanda/project-changepilot",
                        clone_url="https://github.com/kameswarpanda/project-changepilot.git",
                        owner_user_id="usr-kameswar-01",
                        provider="github",
                        default_branch="main",
                        branches=["main", "develop", "feature/auth-gates"],
                        language="Python / TypeScript",
                        test_runner="pytest / npm test",
                        is_private=True
                    ),
                    RepositoryModel(
                        id="repo-calculator-service",
                        name="calculator-service",
                        full_name="company/calculator-service",
                        clone_url="https://github.com/company/calculator-service.git",
                        owner_user_id="usr-kameswar-01",
                        provider="github",
                        default_branch="main",
                        branches=["main", "develop", "feature/discounts"],
                        language="Python",
                        test_runner="pytest",
                        is_private=False
                    ),
                    RepositoryModel(
                        id="repo-payment-service",
                        name="payment-service",
                        full_name="company/payment-service",
                        clone_url="https://dev.azure.com/company/payments/_git/payment-service",
                        owner_user_id="usr-kameswar-01",
                        provider="azure_devops",
                        default_branch="develop",
                        branches=["main", "develop", "staging"],
                        language="Go",
                        test_runner="go test",
                        is_private=True
                    )
                ]
                for r in repos:
                    session.merge(r)

            # Seed change requests if none exist
            if session.query(ChangeRequestModel).count() == 0:
                requests = [
                    ChangeRequestModel(
                        id="cr-1042",
                        story_id="CP-1042",
                        user_id="usr-kameswar-01",
                        title="Add Percentage Discount Rule to Calculator Engine",
                        description="Implement apply_discount(total, percent) method with validation that percentage is between 0 and 100.",
                        repository="calculator-service",
                        base_branch="main",
                        status="COMPLETED",
                        priority="HIGH"
                    ),
                    ChangeRequestModel(
                        id="cr-1043",
                        story_id="CP-1043",
                        user_id="usr-kameswar-01",
                        title="Refactor Session Expiration & Refresh Token Strategy",
                        description="Update auth middleware to reject revoked JWT tokens and enforce strict expiration timeouts.",
                        repository="project-changepilot",
                        base_branch="main",
                        status="IN_PROGRESS",
                        priority="CRITICAL"
                    )
                ]
                for req in requests:
                    session.merge(req)

            # Seed assigned cloud tickets if none exist
            if session.query(AssignedTicketModel).count() == 0:
                tickets = [
                    AssignedTicketModel(
                        id="tkt-01",
                        story_id="CP-STR-0001",
                        user_id="usr-kameswar-01",
                        title="Upgrade Payment Service for Production Readiness",
                        description="Implement ISO-4217 currency validation, structured transaction logging, and strict boundary JUnit test cases for all payment requests.",
                        source="GitHub Issues",
                        repository="kameswarpanda/changepilot-demo-payment",
                        base_branch="main",
                        priority="HIGH",
                        acceptance_criteria=[
                            "Reject non-3-letter or invalid ISO currency codes with IllegalArgumentException",
                            "Maintain backward compatibility for existing valid EUR and USD transactions",
                            "Execute automated test suite with zero regressions"
                        ],
                        assigned_to="ChangePilot Agent",
                        status="READY"
                    ),
                    AssignedTicketModel(
                        id="tkt-02",
                        story_id="CP-1042",
                        user_id="usr-kameswar-01",
                        title="Add Modular Discount Calculation to Core Engine",
                        description="Add calculate_total discount support and apply_discount standalone function with boundary validation.",
                        source="Jira Cloud",
                        repository="project-changepilot",
                        base_branch="main",
                        priority="CRITICAL",
                        acceptance_criteria=[
                            "calculate_total([10, 20], discount=5) must evaluate to 25",
                            "Negative discount must raise ValueError with clear message",
                            "All unit tests in pytest must pass"
                        ],
                        assigned_to="ChangePilot Agent",
                        status="READY"
                    ),
                    AssignedTicketModel(
                        id="tkt-03",
                        story_id="ADO-7821",
                        user_id="usr-kameswar-01",
                        title="Security Patch: In-Memory Token Blacklist Expiration",
                        description="Ensure revoked JWT tokens and expired session credentials are purged instantly across the cluster.",
                        source="Azure DevOps Boards",
                        repository="project-changepilot",
                        base_branch="main",
                        priority="MEDIUM",
                        acceptance_criteria=[
                            "Revoked token returns 401 Unauthorized",
                            "Expired tokens must be pruned from cache every 15 minutes"
                        ],
                        assigned_to="ChangePilot Agent",
                        status="READY"
                    )
                ]
                for t in tickets:
                    session.merge(t)

            session.commit()
        except Exception as e:
            session.rollback()
            logger.warning(f"Seeding initial data notice: {e}")
        finally:
            session.close()

    def save_pipeline_run(self, result: WorkflowResult, user_id: str = "usr-kameswar-01", repo_name: str = "project-changepilot") -> Optional[PipelineRunModel]:
        """Persists a pipeline run and its audit trail."""
        session: Session = SessionLocal()
        try:
            audit_serialized = []
            for rec in result.audit_trail:
                if hasattr(rec, "model_dump"):
                    audit_serialized.append(rec.model_dump(mode="json"))
                elif hasattr(rec, "dict"):
                    audit_serialized.append(rec.dict())
                else:
                    audit_serialized.append(dict(rec))

                # Also insert into persistent AuditLogModel with accurate step-level status
                try:
                    rec_status = getattr(rec, "status", None)
                    rec_status_str = rec_status.value if hasattr(rec_status, "value") else str(rec_status or "")
                    step_passed = ("SUCCESS" in rec_status_str.upper()) or ("PASS" in rec_status_str.upper())
                    
                    stage_name = getattr(rec, "stage", str(result.current_stage))
                    stage_name_str = stage_name.value if hasattr(stage_name, "value") else str(stage_name)
                    message = getattr(rec, "message", getattr(rec, "action", "SAFETY_GATE_EVALUATION"))

                    audit_entry = AuditLogModel(
                        id=f"aud-{uuid.uuid4().hex[:8]}",
                        correlation_id=result.execution_id,
                        story_id=result.story_id,
                        user_id=user_id,
                        user_email="kameswarpanda11@gmail.com",
                        stage=stage_name_str,
                        action=message,
                        target_repository=repo_name,
                        target_branch=result.branch_name,
                        status="PASSED" if step_passed else "FAILED",
                        safety_rule=getattr(rec, "rule", "Deterministic Safety Gate"),
                        details=audit_serialized[-1]
                    )
                    session.merge(audit_entry)
                except Exception as ex:
                    logger.debug(f"Audit log record persistence notice: {ex}")

            pr_serialized = None
            if result.pull_request:
                if hasattr(result.pull_request, "model_dump"):
                    pr_serialized = result.pull_request.model_dump(mode="json")
                else:
                    pr_serialized = result.pull_request

            run = PipelineRunModel(
                id=result.execution_id,
                story_id=result.story_id,
                user_id=user_id,
                title=result.change_plan.summary if result.change_plan else result.story_id,
                repository=repo_name,
                base_branch=getattr(result, "base_branch", "main"),
                branch_name=result.branch_name,
                status=result.status.value if hasattr(result.status, "value") else str(result.status),
                current_stage=result.current_stage.value if hasattr(result.current_stage, "value") else str(result.current_stage),
                success=result.success,
                test_passed=result.test_passed,
                total_duration_ms=result.total_duration_ms,
                started_at=result.started_at,
                completed_at=result.completed_at,
                applied_diff=result.applied_diff,
                pull_request=pr_serialized,
                audit_trail=audit_serialized
            )
            try:
                session.merge(run)
                session.commit()
                logger.info(f"Persisted pipeline run {result.execution_id} to database.")
                return run
            except Exception as initial_err:
                session.rollback()
                logger.warning(f"Initial run persistence warning: {initial_err}. Retrying with defensive field normalization.")
                # Defensively normalize strings in case DB still has strict VARCHAR column constraints
                run.title = (run.title or "")[:250] if run.title else None
                run.repository = (run.repository or "")[:250] if run.repository else None
                run.branch_name = (run.branch_name or "")[:120] if run.branch_name else None
                run.current_stage = (run.current_stage or "")[:60] if run.current_stage else None
                session.merge(run)
                session.commit()
                logger.info(f"Persisted pipeline run {result.execution_id} with defensive field limits.")
                return run
        except Exception as e:
            session.rollback()
            logger.error(f"Error persisting pipeline run: {e}")
            return None
        finally:
            session.close()

    def list_recent_pipeline_runs(self, user_id: Optional[str] = None, limit: int = 20) -> List[dict]:
        """Lists recent pipeline runs from database filtered by user_id."""
        session: Session = SessionLocal()
        try:
            query = session.query(PipelineRunModel)
            if user_id:
                query = query.filter(PipelineRunModel.user_id == user_id)
            runs = query.order_by(PipelineRunModel.started_at.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "story_id": r.story_id,
                    "title": r.title,
                    "repository": r.repository,
                    "base_branch": r.base_branch,
                    "branch_name": r.branch_name,
                    "status": r.status,
                    "success": r.success,
                    "duration_ms": r.total_duration_ms,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                    "applied_diff": r.applied_diff,
                    "pull_request": r.pull_request
                }
                for r in runs
            ]
        except Exception as e:
            logger.warning(f"Error querying pipeline runs: {e}")
            return []
        finally:
            session.close()

    def list_audit_logs(self, user_id: Optional[str] = None, limit: int = 50, story_id: Optional[str] = None, repository: Optional[str] = None) -> List[dict]:
        """Queries persistent audit logs filtered strictly by user_id."""
        session: Session = SessionLocal()
        try:
            q = session.query(AuditLogModel)
            if user_id:
                q = q.filter(AuditLogModel.user_id == user_id)
            if story_id:
                q = q.filter(AuditLogModel.story_id == story_id)
            if repository:
                q = q.filter(AuditLogModel.target_repository == repository)
            logs = q.order_by(AuditLogModel.timestamp.desc()).limit(limit).all()
            return [
                {
                    "id": l.id,
                    "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                    "correlation_id": l.correlation_id,
                    "story_id": l.story_id,
                    "user_email": l.user_email,
                    "stage": l.stage,
                    "action": l.action,
                    "target_repository": l.target_repository,
                    "target_branch": l.target_branch,
                    "status": l.status,
                    "safety_rule": l.safety_rule
                }
                for l in logs
            ]
        except Exception as e:
            logger.warning(f"Error querying audit logs: {e}")
            return []
        finally:
            session.close()

    def list_change_requests(self, user_id: Optional[str] = None) -> List[dict]:
        """Lists change requests from database strictly filtered by user_id."""
        session: Session = SessionLocal()
        try:
            query = session.query(ChangeRequestModel)
            if user_id:
                query = query.filter(ChangeRequestModel.user_id == user_id)
            requests = query.order_by(ChangeRequestModel.created_at.desc()).all()
            return [
                {
                    "id": req.id,
                    "story_id": req.story_id,
                    "title": req.title,
                    "description": req.description,
                    "repository": req.repository,
                    "base_branch": req.base_branch,
                    "status": req.status,
                    "priority": req.priority,
                    "created_at": req.created_at.isoformat() if req.created_at else None
                }
                for req in requests
            ]
        except Exception as e:
            logger.warning(f"Error querying change requests: {e}")
            return []
        finally:
            session.close()

    def save_change_request(self, req: dict) -> dict:
        """Persists a new change request."""
        session: Session = SessionLocal()
        try:
            req_id = req.get("id") or f"cr-{uuid.uuid4().hex[:4]}"
            model = ChangeRequestModel(
                id=req_id,
                story_id=req.get("story_id", "CP-AUTO"),
                user_id=req.get("user_id", "usr-kameswar-01"),
                title=req.get("title", "Autonomous Change"),
                description=req.get("description", ""),
                repository=req.get("repository", "project-changepilot"),
                base_branch=req.get("base_branch", "main"),
                status=req.get("status", "PENDING"),
                priority=req.get("priority", "MEDIUM")
            )
            session.merge(model)
            session.commit()
            return {
                "id": model.id,
                "story_id": model.story_id,
                "title": model.title,
                "status": model.status
            }
        except Exception as e:
            session.rollback()
            logger.warning(f"Error saving change request: {e}")
            raise
        finally:
            session.close()

    def delete_change_request(self, request_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes a change request from database strictly for the user."""
        session: Session = SessionLocal()
        try:
            q = session.query(ChangeRequestModel).filter(
                (ChangeRequestModel.id == request_id) | (ChangeRequestModel.story_id == request_id)
            )
            if user_id:
                q = q.filter(ChangeRequestModel.user_id == user_id)
            req = q.first()
            if req:
                session.delete(req)
                session.commit()
                logger.info(f"Deleted change request {request_id} for user {user_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.warning(f"Error deleting change request {request_id}: {e}")
            return False
        finally:
            session.close()

    def list_connected_repositories(self, user_id: Optional[str] = None) -> List[dict]:
        """Lists connected repositories from database strictly filtered by owner user_id."""
        session: Session = SessionLocal()
        try:
            query = session.query(RepositoryModel)
            if user_id:
                query = query.filter(RepositoryModel.owner_user_id == user_id)
            repos = query.all()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "full_name": r.full_name,
                    "clone_url": r.clone_url,
                    "owner_user_id": r.owner_user_id,
                    "provider": r.provider,
                    "default_branch": r.default_branch,
                    "branches": r.branches or ["main"],
                    "language": r.language,
                    "test_runner": r.test_runner,
                    "is_private": r.is_private,
                    "path": r.full_name
                }
                for r in repos
            ]
        except Exception as e:
            logger.warning(f"Error querying repositories: {e}")
            return []
        finally:
            session.close()

    def get_repository(self, identifier: str) -> Optional[dict]:
        """Finds a repository by exact ID, name, full_name, or clone_url."""
        session: Session = SessionLocal()
        try:
            ident_clean = identifier.strip().rstrip("/").replace(".git", "")
            r = session.query(RepositoryModel).filter(
                (RepositoryModel.id == identifier) |
                (RepositoryModel.name == identifier) |
                (RepositoryModel.full_name == identifier) |
                (RepositoryModel.clone_url == identifier) |
                (RepositoryModel.name == ident_clean) |
                (RepositoryModel.full_name == ident_clean)
            ).first()
            if r:
                return {
                    "id": r.id,
                    "name": r.name,
                    "full_name": r.full_name,
                    "clone_url": r.clone_url,
                    "provider": r.provider,
                    "default_branch": r.default_branch,
                    "branches": r.branches or ["main"],
                    "language": r.language,
                    "test_runner": r.test_runner,
                    "is_private": r.is_private,
                    "path": r.clone_url or r.full_name
                }
            return None
        except Exception as e:
            logger.warning(f"Error finding repository {identifier}: {e}")
            return None
        finally:
            session.close()

    def delete_repository(self, repo_id: str) -> bool:
        """Deletes/unlinks a repository from the database."""
        session: Session = SessionLocal()
        try:
            r = session.query(RepositoryModel).filter(
                (RepositoryModel.id == repo_id) |
                (RepositoryModel.name == repo_id) |
                (RepositoryModel.full_name == repo_id)
            ).first()
            if r:
                session.delete(r)
                session.commit()
                logger.info(f"Unlinked and deleted repository {repo_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.warning(f"Error deleting repository {repo_id}: {e}")
            return False
        finally:
            session.close()

    def delete_user_repositories(self, user_id: str, provider: Optional[str] = None) -> int:
        """Deletes all repositories connected by a specific user (optionally filtered by provider)."""
        session: Session = SessionLocal()
        try:
            q = session.query(RepositoryModel).filter(RepositoryModel.owner_user_id == user_id)
            if provider:
                q = q.filter(RepositoryModel.provider == provider)
            deleted_count = q.delete(synchronize_session=False)
            session.commit()
            logger.info(f"Deleted {deleted_count} connected repositories for user {user_id} (provider={provider})")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.warning(f"Error deleting repositories for user {user_id}: {e}")
            return 0
        finally:
            session.close()

    def delete_user_github_account_repositories(self, user_id: str) -> int:
        """Deletes only repositories imported via GitHub account token for the user, preserving public URL imports."""
        session: Session = SessionLocal()
        try:
            q = session.query(RepositoryModel).filter(
                RepositoryModel.owner_user_id == user_id,
                RepositoryModel.provider.in_(["github_account", "github"])
            )
            deleted_count = q.delete(synchronize_session=False)
            session.commit()
            logger.info(f"Deleted {deleted_count} GitHub account repositories for user {user_id} (public URL repositories preserved)")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.warning(f"Error deleting GitHub account repositories for user {user_id}: {e}")
            return 0
        finally:
            session.close()

    def save_repository(self, repo_dict: dict) -> dict:
        """Persists a new connected repository strictly linked to owner_user_id."""
        session: Session = SessionLocal()
        try:
            repo_id = repo_dict.get("id") or f"repo-{uuid.uuid4().hex[:6]}"
            model = RepositoryModel(
                id=repo_id,
                name=repo_dict.get("name", "repo"),
                full_name=repo_dict.get("full_name", "repo"),
                clone_url=repo_dict.get("clone_url"),
                owner_user_id=repo_dict.get("owner_user_id", "usr-kameswar-01"),
                provider=repo_dict.get("provider", "github"),
                default_branch=repo_dict.get("default_branch", "main"),
                branches=repo_dict.get("branches", ["main"]),
                language=repo_dict.get("language", "Python"),
                test_runner=repo_dict.get("test_runner", "pytest"),
                is_private=repo_dict.get("is_private", True)
            )
            session.merge(model)
            session.commit()
            return {
                "id": model.id,
                "name": model.name,
                "full_name": model.full_name,
                "provider": model.provider,
                "branches": model.branches,
                "clone_url": model.clone_url,
                "language": model.language,
                "test_runner": model.test_runner
            }
        except Exception as e:
            session.rollback()
            logger.warning(f"Error saving repository: {e}")
            raise
        finally:
            session.close()

    def get_analytics_summary(self, user_id: Optional[str] = None) -> dict:
        """Computes live aggregated change analytics strictly filtered by user_id."""
        session: Session = SessionLocal()
        try:
            run_query = session.query(PipelineRunModel)
            repo_query = session.query(RepositoryModel)
            req_query = session.query(ChangeRequestModel)
            if user_id:
                run_query = run_query.filter(PipelineRunModel.user_id == user_id)
                repo_query = repo_query.filter(RepositoryModel.owner_user_id == user_id)
                req_query = req_query.filter(ChangeRequestModel.user_id == user_id)

            total_runs = run_query.count()
            success_runs = run_query.filter(PipelineRunModel.success == True).count()
            failed_runs = total_runs - success_runs
            pass_rate = round((success_runs / total_runs * 100), 1) if total_runs > 0 else 100.0

            total_repos = repo_query.count()
            total_requests = req_query.count()

            # Dynamic mean duration calculation from runs
            runs = run_query.all()
            durations = [r.total_duration_ms for r in runs if r.total_duration_ms and r.total_duration_ms > 0]
            mean_duration = round(sum(durations) / len(durations), 1) if durations else 2500.0

            # Dynamic language breakdown from connected repositories
            repos = repo_query.all()
            lang_counts: Dict[str, int] = {}
            for repo in repos:
                lang = (repo.language or "Unknown").capitalize()
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

            if not lang_counts:
                lang_counts = {"Python": 1}

            total_lang_count = sum(lang_counts.values())
            languages_breakdown = {
                lang: round((cnt / total_lang_count) * 100)
                for lang, cnt in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
            }
            primary_language = list(languages_breakdown.keys())[0] if languages_breakdown else "Python"

            languages_list = [
                {"name": lang, "percentage": pct}
                for lang, pct in languages_breakdown.items()
            ]

            summary_obj = {
                "total_runs": total_runs,
                "successful_runs": success_runs,
                "failed_runs": failed_runs,
                "success_rate": pass_rate,
                "pass_rate": pass_rate,
                "tests_executed": total_runs * 9,
                "mean_duration_ms": mean_duration
            }

            return {
                "total_pipeline_runs": total_runs,
                "successful_runs": success_runs,
                "failed_runs": failed_runs,
                "safety_pass_rate": pass_rate,
                "connected_repositories": total_repos,
                "total_change_requests": total_requests,
                "mean_duration_ms": mean_duration,
                "gate_evaluations_count": total_runs * 9,
                "primary_language": primary_language,
                "languages_breakdown": languages_breakdown,
                "languages": languages_list,
                "summary": summary_obj
            }
        except Exception as e:
            logger.warning(f"Error querying analytics: {e}")
            return {
                "total_pipeline_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "safety_pass_rate": 100.0,
                "connected_repositories": 0,
                "total_change_requests": 0,
                "mean_duration_ms": 2500.0,
                "gate_evaluations_count": 0,
                "primary_language": "Python",
                "languages_breakdown": {"Python": 100},
                "languages": [{"name": "Python", "percentage": 100}],
                "summary": {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "success_rate": 100.0,
                    "pass_rate": 100.0,
                    "tests_executed": 0,
                    "mean_duration_ms": 2500.0
                }
            }
        finally:
            session.close()

    def get_user_integrations(self, user_id: str) -> dict:
        """Gets user-specific integrations (e.g. GitHub token)."""
        session: Session = SessionLocal()
        try:
            integ = session.query(UserIntegrationModel).filter(UserIntegrationModel.user_id == user_id).first()
            if integ:
                return {
                    "github_token": integ.github_token,
                    "azure_token": integ.azure_token,
                    "jira_token": integ.jira_token
                }
            return {}
        except Exception as e:
            logger.warning(f"Error querying user integrations: {e}")
            return {}
        finally:
            session.close()

    def save_user_github_token(self, user_id: str, token: str) -> dict:
        """Saves a GitHub Personal Access Token strictly for a specific user."""
        session: Session = SessionLocal()
        try:
            integ = session.query(UserIntegrationModel).filter(UserIntegrationModel.user_id == user_id).first()
            if not integ:
                integ = UserIntegrationModel(
                    id=f"int-{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    github_token=token
                )
                session.add(integ)
            else:
                integ.github_token = token
                integ.updated_at = datetime.now(timezone.utc)
            session.commit()
            return {"user_id": user_id, "github_token": token}
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving user GitHub token: {e}")
            raise
        finally:
            session.close()

    def delete_user_github_token(self, user_id: str) -> bool:
        """Clears the GitHub token strictly for a specific user."""
        session: Session = SessionLocal()
        try:
            integ = session.query(UserIntegrationModel).filter(UserIntegrationModel.user_id == user_id).first()
            if integ:
                integ.github_token = None
                session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.warning(f"Error deleting user GitHub token: {e}")
            return False
        finally:
            session.close()

    def list_assigned_tickets(self, user_id: Optional[str] = None) -> List[dict]:
        """Queries assigned cloud tickets directly from persistent database."""
        session: Session = SessionLocal()
        try:
            q = session.query(AssignedTicketModel)
            if user_id and user_id != "all":
                q = q.filter((AssignedTicketModel.user_id == user_id) | (AssignedTicketModel.user_id == "usr-kameswar-01"))
            tickets = q.order_by(AssignedTicketModel.created_at.desc()).all()
            return [
                {
                    "id": t.id,
                    "story_id": t.story_id,
                    "title": t.title,
                    "description": t.description,
                    "source": t.source,
                    "repository": t.repository,
                    "base_branch": t.base_branch,
                    "priority": t.priority,
                    "acceptance_criteria": t.acceptance_criteria or [],
                    "assigned_to": t.assigned_to,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in tickets
            ]
        except Exception as e:
            logger.warning(f"Error querying assigned tickets: {e}")
            return []
        finally:
            session.close()

    def save_assigned_ticket(self, tkt: dict, user_id: str = "usr-kameswar-01") -> dict:
        """Persists a new or updated assigned cloud ticket in the database."""
        session: Session = SessionLocal()
        try:
            tkt_id = tkt.get("id") or f"tkt-{uuid.uuid4().hex[:6]}"
            model = AssignedTicketModel(
                id=tkt_id,
                story_id=tkt.get("story_id", "CP-NEW"),
                user_id=user_id,
                title=tkt.get("title", "New Change Task"),
                description=tkt.get("description", ""),
                source=tkt.get("source", "Cloud Integration"),
                repository=tkt.get("repository", "project-changepilot"),
                base_branch=tkt.get("base_branch", "main"),
                priority=tkt.get("priority", "HIGH"),
                acceptance_criteria=tkt.get("acceptance_criteria", []),
                assigned_to=tkt.get("assigned_to", "ChangePilot Agent"),
                status=tkt.get("status", "READY")
            )
            session.merge(model)
            session.commit()
            return {
                "id": model.id,
                "story_id": model.story_id,
                "title": model.title,
                "source": model.source,
                "status": model.status
            }
        except Exception as e:
            session.rollback()
            logger.warning(f"Error saving assigned ticket: {e}")
            raise
        finally:
            session.close()

    def delete_assigned_ticket(self, ticket_id: str) -> bool:
        """Deletes an assigned ticket by its ID."""
        session: Session = SessionLocal()
        try:
            t = session.query(AssignedTicketModel).filter(AssignedTicketModel.id == ticket_id).first()
            if t:
                session.delete(t)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.warning(f"Error deleting assigned ticket: {e}")
            return False
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # User Account Database Operations
    # -------------------------------------------------------------------------
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Retrieves user model from database by ID."""
        session: Session = SessionLocal()
        try:
            u = session.query(UserModel).filter(UserModel.id == user_id).first()
            if u:
                return {
                    "id": u.id,
                    "identity_provider_id": u.identity_provider_id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "email": u.email,
                    "password_hash": u.password_hash,
                    "avatar_url": u.avatar_url,
                    "provider": u.provider,
                    "roles": u.roles or ["developer"],
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
                }
            return None
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Retrieves user model from database by email."""
        session: Session = SessionLocal()
        try:
            clean_email = email.strip().lower()
            u = session.query(UserModel).filter(func.lower(UserModel.email) == clean_email).first()
            if u:
                return {
                    "id": u.id,
                    "identity_provider_id": u.identity_provider_id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "email": u.email,
                    "password_hash": u.password_hash,
                    "avatar_url": u.avatar_url,
                    "provider": u.provider,
                    "roles": u.roles or ["developer"],
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
                }
            return None
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Retrieves user model from database by username."""
        session: Session = SessionLocal()
        try:
            clean_name = username.strip().lower()
            u = session.query(UserModel).filter(func.lower(UserModel.username) == clean_name).first()
            if u:
                return {
                    "id": u.id,
                    "identity_provider_id": u.identity_provider_id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "email": u.email,
                    "password_hash": u.password_hash,
                    "avatar_url": u.avatar_url,
                    "provider": u.provider,
                    "roles": u.roles or ["developer"],
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
                }
            return None
        finally:
            session.close()

    def save_user(self, user_data: dict) -> dict:
        """Saves or updates user model in database."""
        session: Session = SessionLocal()
        try:
            user_id = user_data.get("id") or f"usr-{uuid.uuid4().hex[:6]}"
            model = UserModel(
                id=user_id,
                identity_provider_id=user_data.get("identity_provider_id", f"local-{user_id}"),
                username=user_data.get("username", user_id),
                display_name=user_data.get("display_name", "ChangePilot Developer"),
                email=user_data.get("email", f"{user_id}@changepilot.dev").strip().lower(),
                password_hash=user_data.get("password_hash"),
                avatar_url=user_data.get("avatar_url"),
                provider=user_data.get("provider", "google"),
                roles=user_data.get("roles", ["developer"]),
                last_login_at=datetime.now(timezone.utc)
            )
            session.merge(model)
            session.commit()
            return {
                "id": model.id,
                "username": model.username,
                "display_name": model.display_name,
                "email": model.email,
                "avatar_url": model.avatar_url,
                "provider": model.provider,
                "roles": model.roles
            }
        except Exception as e:
            session.rollback()
            logger.warning(f"Error saving user: {e}")
            raise
        finally:
            session.close()

    def update_user_password(self, email: str, password_hash: str) -> bool:
        """Updates user password hash in persistent database."""
        session: Session = SessionLocal()
        try:
            clean_email = email.strip().lower()
            u = session.query(UserModel).filter(func.lower(UserModel.email) == clean_email).first()
            if u:
                u.password_hash = password_hash
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.warning(f"Error updating password: {e}")
            return False
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Password Reset OTP Database Operations
    # -------------------------------------------------------------------------
    def save_password_reset_otp(self, email: str, otp_hash: str, expires_minutes: int = 10) -> dict:
        """Stores a password reset OTP verification record with TTL."""
        session: Session = SessionLocal()
        try:
            from datetime import timedelta
            clean_email = email.strip().lower()
            # Clean old records for this email
            session.query(PasswordResetOtpModel).filter(func.lower(PasswordResetOtpModel.email) == clean_email).delete()
            otp_id = f"otp-{uuid.uuid4().hex[:8]}"
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
            model = PasswordResetOtpModel(
                id=otp_id,
                email=clean_email,
                otp_hash=otp_hash,
                expires_at=expires_at,
                verified=False
            )
            session.add(model)
            session.commit()
            return {"id": model.id, "email": model.email, "expires_at": model.expires_at}
        except Exception as e:
            session.rollback()
            logger.warning(f"Error saving reset OTP: {e}")
            raise
        finally:
            session.close()

    def verify_password_reset_otp(self, email: str, otp_hash: str) -> bool:
        """Validates OTP hash and expiration time against database record."""
        session: Session = SessionLocal()
        try:
            clean_email = email.strip().lower()
            rec = session.query(PasswordResetOtpModel).filter(
                func.lower(PasswordResetOtpModel.email) == clean_email,
                PasswordResetOtpModel.otp_hash == otp_hash,
                PasswordResetOtpModel.expires_at > datetime.now(timezone.utc)
            ).first()
            if rec:
                rec.verified = True
                session.commit()
                return True
            return False
        finally:
            session.close()

    def mark_password_reset_otp_used(self, email: str) -> bool:
        """Invalidates/deletes OTP records upon successful password change."""
        session: Session = SessionLocal()
        try:
            clean_email = email.strip().lower()
            session.query(PasswordResetOtpModel).filter(func.lower(PasswordResetOtpModel.email) == clean_email).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()


# Global singleton database repository
db_repository = DatabaseRepository()
