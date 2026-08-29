"""JWT generation and verification utility for ChangePilot."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from backend.src.auth.models import TokenPayload, User
from backend.src.config import settings

logger = logging.getLogger("changepilot.auth.jwt")


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a signed JWT access token containing user identity and role claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": user.id,
        "email": user.email,
        "username": user.username,
        "roles": [r.value if hasattr(r, "value") else str(r) for r in user.roles],
        "provider": user.provider.value if hasattr(user.provider, "value") else str(user.provider),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """Decodes and validates a signed JWT token, returning the TokenPayload or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        logger.warning("JWT Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT Token signature: {e}")
        return None
    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        return None
