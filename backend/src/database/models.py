"""SQLAlchemy ORM models for persistent storage in ChangePilot."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserModel(Base):
    """User account entity."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    identity_provider_id = Column(String(128), index=True)
    username = Column(String(64), unique=True, index=True)
    display_name = Column(String(128))
    email = Column(String(128), unique=True, index=True)
    avatar_url = Column(String(512), nullable=True)
    provider = Column(String(32), default="github")
    roles = Column(JSON, default=lambda: ["developer"])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RepositoryModel(Base):
    """Connected repository entity."""
    __tablename__ = "repositories"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), index=True)
    full_name = Column(String(256), index=True)
    owner_user_id = Column(String(64), index=True)
    provider = Column(String(32), default="github")
    default_branch = Column(String(64), default="main")
    language = Column(String(64), default="Python")
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PipelineRunModel(Base):
    """Historical execution run record."""
    __tablename__ = "pipeline_runs"

    id = Column(String(64), primary_key=True, index=True)
    story_id = Column(String(64), index=True)
    user_id = Column(String(64), index=True, default="usr-kameswar-01")
    title = Column(String(256))
    repository = Column(String(256))
    base_branch = Column(String(64), default="main")
    branch_name = Column(String(128), nullable=True)
    status = Column(String(32), index=True)
    current_stage = Column(String(64))
    success = Column(Boolean, default=False)
    test_passed = Column(Boolean, nullable=True)
    total_duration_ms = Column(Float, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    applied_diff = Column(Text, nullable=True)
    pull_request = Column(JSON, nullable=True)
    audit_trail = Column(JSON, default=list)
