"""Authentication, Identity and Authorization package for ChangePilot."""
from backend.src.auth.models import User, UserRole, AuthProvider, AuthSessionResponse, LoginRequest
from backend.src.auth.jwt_handler import create_access_token, decode_access_token
from backend.src.auth.service import AuthService, auth_service
from backend.src.auth.dependencies import get_current_user, get_optional_user
from backend.src.auth.authorization import AuthorizationService, AccessLevel, authz_service

__all__ = [
    "User",
    "UserRole",
    "AuthProvider",
    "AuthSessionResponse",
    "LoginRequest",
    "create_access_token",
    "decode_access_token",
    "AuthService",
    "auth_service",
    "get_current_user",
    "get_optional_user",
    "AuthorizationService",
    "AccessLevel",
    "authz_service",
]
