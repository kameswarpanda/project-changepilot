"""Data models for Identity, Authentication and Sessions in ChangePilot."""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class AuthProvider(str, Enum):
    GITHUB = "github"
    GOOGLE = "google"
    LOCAL = "local"
    PASSWORD = "password"


class User(BaseModel):
    """Authenticated application user."""
    id: str = Field(..., description="Unique User ID (e.g. usr-kameswar-1)")
    identity_provider_id: str = Field(..., description="Provider specific subject/id")
    username: str = Field(..., description="User handle/login")
    display_name: str = Field(..., description="Full Name")
    email: str = Field(..., description="Primary email address")
    avatar_url: Optional[str] = Field(default=None, description="User avatar image URL")
    provider: AuthProvider = Field(default=AuthProvider.GOOGLE, description="Authentication provider")
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.DEVELOPER], description="Assigned roles")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenPayload(BaseModel):
    """JWT Token claims payload."""
    sub: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    roles: List[str] = Field(default_factory=list)
    provider: str = Field(...)
    exp: int = Field(..., description="Expiration timestamp (epoch seconds)")
    iat: int = Field(..., description="Issued at timestamp (epoch seconds)")


from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Login payload supporting Google ID tokens, Email/Password, or Demo login."""
    provider: AuthProvider = Field(default=AuthProvider.GOOGLE)
    email: Optional[str] = Field(default=None, description="User email address")
    password: Optional[str] = Field(default=None, description="User password")
    token_or_code: Optional[str] = Field(default=None, description="Google OAuth ID token or credential")
    demo_username: Optional[str] = Field(default=None, description="For local/demo quick login")

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class RegisterRequest(BaseModel):
    """User registration payload with Email, Password, and Full Name."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password (min 6 characters)")
    display_name: str = Field(..., description="Full Name")


class AuthSessionResponse(BaseModel):
    """Response returned upon successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
