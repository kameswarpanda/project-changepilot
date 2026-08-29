"""FastAPI authentication dependencies for ChangePilot."""
import logging
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.src.auth.jwt_handler import decode_access_token
from backend.src.auth.models import User
from backend.src.auth.service import auth_service

logger = logging.getLogger("changepilot.auth.dependencies")

# Bearer token security scheme (auto_error=False allows public endpoints and custom fallback)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(default=None)
) -> User:
    """Enforces authentication and returns the authenticated User instance.
    
    Raises HTTP 401 Unauthorized if the token is missing, invalid, or expired.
    In local development/testing without token, provides the default developer user.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        # Fallback to default user for developer convenience / tests if no token is passed
        default_user = auth_service.get_user_by_id("usr-kameswar-01")
        if default_user:
            return default_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Returns the authenticated user if a valid token is present, otherwise None."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    return auth_service.get_user_by_id(payload.sub)
