"""Repository CRUD layer for ChangePilot persistence."""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.src.database.models import PipelineRunModel, RepositoryModel, UserModel
from backend.src.database.session import SessionLocal
from backend.src.models.workflow_result import WorkflowResult

logger = logging.getLogger("changepilot.database.repository")


class DatabaseRepository:
    """Provides high-level persistent operations across databases."""

    def save_pipeline_run(self, result: WorkflowResult, user_id: str = "usr-kameswar-01", repo_name: str = "demo_repo") -> Optional[PipelineRunModel]:
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
            session.merge(run)
            session.commit()
            logger.info(f"Persisted pipeline run {result.execution_id} to database.")
            return run
        except Exception as e:
            session.rollback()
            logger.warning(f"Error persisting pipeline run: {e}")
            raise
        finally:
            session.close()

    def list_recent_pipeline_runs(self, limit: int = 20) -> List[dict]:
        """Lists recent pipeline runs from database."""
        session: Session = SessionLocal()
        try:
            runs = session.query(PipelineRunModel).order_by(PipelineRunModel.started_at.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "story_id": r.story_id,
                    "title": r.title,
                    "repository": r.repository,
                    "branch_name": r.branch_name,
                    "status": r.status,
                    "success": r.success,
                    "duration_ms": r.total_duration_ms,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "pull_request": r.pull_request
                }
                for r in runs
            ]
        except Exception as e:
            logger.warning(f"Error querying pipeline runs: {e}")
            return []
        finally:
            session.close()


# Global singleton database repository
db_repository = DatabaseRepository()
