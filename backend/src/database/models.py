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
    password_hash = Column(String(256), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    provider = Column(String(32), default="google")
    roles = Column(JSON, default=lambda: ["developer"])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RepositoryModel(Base):
    """Connected repository entity."""
    __tablename__ = "repositories"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), index=True)
    full_name = Column(String(256), index=True)
    clone_url = Column(String(512), nullable=True)
    owner_user_id = Column(String(64), index=True)
    provider = Column(String(32), default="github")
    default_branch = Column(String(64), default="main")
    branches = Column(JSON, default=lambda: ["main"])
    language = Column(String(64), default="Python")
    test_runner = Column(String(64), default="pytest")
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChangeRequestModel(Base):
    """Persisted change story/ticket entity."""
    __tablename__ = "change_requests"

    id = Column(String(64), primary_key=True, index=True)
    story_id = Column(String(64), index=True)
    user_id = Column(String(64), index=True)
    title = Column(String(256))
    description = Column(Text)
    repository = Column(String(256))
    base_branch = Column(String(64), default="main")
    status = Column(String(32), default="PENDING", index=True)
    priority = Column(String(32), default="MEDIUM")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


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


class AuditLogModel(Base):
    """Granular audit event record for safety gate validation, patches, and user triggers."""
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    correlation_id = Column(String(64), index=True)
    story_id = Column(String(64), index=True)
    user_id = Column(String(64), index=True)
    user_email = Column(String(128), index=True)
    stage = Column(String(64), index=True)
    action = Column(String(128))
    target_repository = Column(String(256))
    target_branch = Column(String(128), nullable=True)
    status = Column(String(32), index=True)
    safety_rule = Column(String(128), nullable=True)
    details = Column(JSON, nullable=True)


class AssignedTicketModel(Base):
    """Assigned cloud work ticket from Jira, Azure DevOps, or GitHub Issues."""
    __tablename__ = "assigned_tickets"

    id = Column(String(64), primary_key=True, index=True)
    story_id = Column(String(64), index=True)
    user_id = Column(String(64), index=True, default="usr-kameswar-01")
    title = Column(String(256))
    description = Column(Text)
    source = Column(String(64), default="GitHub Issues")
    repository = Column(String(256), default="project-changepilot")
    base_branch = Column(String(64), default="main")
    priority = Column(String(32), default="HIGH")
    acceptance_criteria = Column(JSON, default=list)
    assigned_to = Column(String(128), default="ChangePilot Agent")
    status = Column(String(32), default="READY")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PasswordResetOtpModel(Base):
    """Stores password reset OTP verification records with strict TTL and audit status."""
    __tablename__ = "password_reset_otps"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(128), index=True)
    otp_hash = Column(String(256))
    expires_at = Column(DateTime)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

