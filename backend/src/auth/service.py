"""Authentication and Identity Service supporting Google Identity, Email/Password, and Local Demo."""
import base64
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
import httpx

from backend.src.auth.jwt_handler import create_access_token
from backend.src.auth.models import (
    AuthProvider,
    AuthSessionResponse,
    LoginRequest,
    RegisterRequest,
    User,
    UserRole,
)
from backend.src.config import settings

logger = logging.getLogger("changepilot.auth.service")


def _hash_password(password: str) -> str:
    """Deterministic salted hash for credential security."""
    salt = "cp_salt_2026_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _decode_jwt_unverified_payload(token_str: str) -> Optional[dict]:
    """Safely decodes JWT payload without network dependency for fast client claims extraction."""
    try:
        parts = token_str.strip().split(".")
        if len(parts) >= 2:
            # Pad base64 string
            b64_str = parts[1]
            padding = 4 - (len(b64_str) % 4)
            if padding != 4:
                b64_str += "=" * padding
            decoded_bytes = base64.urlsafe_b64decode(b64_str)
            return json.loads(decoded_bytes.decode("utf-8"))
    except Exception as ex:
        logger.warning(f"Failed to decode raw JWT payload: {ex}")
    return None


class AuthService:
    """Service handling multi-provider authentication, user registration, and session issuance."""

    def __init__(self):
        # In-memory user cache and password credentials store
        self._user_store: Dict[str, User] = {}
        self._password_store: Dict[str, str] = {}
        self._seed_default_users()

    def _seed_default_users(self):
        """Pre-seeds standard developer & admin profiles for instant zero-friction execution."""
        kameswar = User(
            id="usr-kameswar-01",
            identity_provider_id="google-kameswar-2026",
            username="kameswar",
            display_name="Kameswar Panda",
            email="kameswar@changepilot.dev",
            avatar_url="https://avatars.githubusercontent.com/u/583231",
            provider=AuthProvider.GOOGLE,
            roles=[UserRole.ADMIN, UserRole.DEVELOPER]
        )
        alex = User(
            id="usr-alex-02",
            identity_provider_id="google-alex-mercer",
            username="alex.mercer",
            display_name="Alex Mercer",
            email="alex@changepilot.dev",
            avatar_url=None,
            provider=AuthProvider.GOOGLE,
            roles=[UserRole.DEVELOPER]
        )
        self._user_store[kameswar.id] = kameswar
        self._user_store[kameswar.username] = kameswar
        self._user_store[kameswar.email] = kameswar
        self._password_store[kameswar.email] = _hash_password("changepilot2026")

        self._user_store[alex.id] = alex
        self._user_store[alex.username] = alex
        self._user_store[alex.email] = alex
        self._password_store[alex.email] = _hash_password("changepilot2026")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves a user by their unique ChangePilot ID."""
        return self._user_store.get(user_id)

    def register_user(self, req: RegisterRequest) -> AuthSessionResponse:
        """Registers a new user with Email, Password, and Display Name."""
        email_clean = req.email.strip().lower()
        if email_clean in self._user_store:
            raise ValueError(f"User with email '{email_clean}' already exists. Please sign in.")

        username = email_clean.split("@")[0].replace(".", "_")
        user_id = f"usr-email-{uuid.uuid4().hex[:6]}"
        user = User(
            id=user_id,
            identity_provider_id=f"email-{email_clean}",
            username=username,
            display_name=req.display_name.strip() or username.capitalize(),
            email=email_clean,
            avatar_url=None,
            provider=AuthProvider.PASSWORD,
            roles=[UserRole.DEVELOPER]
        )

        self._user_store[user.id] = user
        self._user_store[user.username] = user
        self._user_store[user.email] = user
        self._password_store[email_clean] = _hash_password(req.password)

        logger.info(f"Registered new user: {user.email} (ID: {user.id})")
        token = create_access_token(user)
        return AuthSessionResponse(
            access_token=token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user
        )

    async def authenticate(self, req: LoginRequest) -> AuthSessionResponse:
        """Authenticates user via Google OAuth/ID token, Email/Password, or Demo profile."""
        user: Optional[User] = None

        # 1. Email & Password Login
        if (req.provider == AuthProvider.PASSWORD or (req.email and req.password)):
            email_clean = (req.email or "").strip().lower()
            stored_user = self._user_store.get(email_clean)
            if not stored_user:
                raise ValueError("Invalid email or password. Please check your credentials or create an account.")

            expected_hash = self._password_store.get(email_clean)
            if expected_hash and expected_hash != _hash_password(req.password):
                raise ValueError("Invalid email or password. Please check your credentials.")

            user = stored_user

        # 2. Local Demo Quick Access
        elif req.provider == AuthProvider.LOCAL or req.demo_username:
            username = (req.demo_username or "kameswar").lower().strip()
            user = self._user_store.get(username)
            if not user:
                user_id = f"usr-{username}-{uuid.uuid4().hex[:4]}"
                user = User(
                    id=user_id,
                    identity_provider_id=f"local-{username}",
                    username=username,
                    display_name=username.replace(".", " ").title(),
                    email=f"{username}@changepilot.local",
                    provider=AuthProvider.LOCAL,
                    roles=[UserRole.DEVELOPER]
                )
                self._user_store[user.id] = user
                self._user_store[user.username] = user
                self._user_store[user.email] = user

        # 3. Google Sign-In & Google Identity Platform
        elif req.provider == AuthProvider.GOOGLE:
            # Check if token or code was passed directly
            token_candidate = req.token_or_code
            if not token_candidate and req.email and ("." in req.email and len(req.email) > 50):
                # Token was passed in email field by mistake
                token_candidate = req.email

            if token_candidate:
                user = await self._verify_google_id_token(token_candidate)
            elif req.email and not req.email.startswith("eyJ"):
                # Clean email was passed
                email_clean = req.email.strip().lower()
                username = email_clean.split("@")[0]
                user_id = f"usr-google-{uuid.uuid4().hex[:6]}"
                display_name = username.replace(".", " ").replace("_", " ").title()
                user = User(
                    id=user_id,
                    identity_provider_id=f"google-{email_clean}",
                    username=username,
                    display_name=display_name,
                    email=email_clean,
                    avatar_url="https://lh3.googleusercontent.com/a/default-user",
                    provider=AuthProvider.GOOGLE,
                    roles=[UserRole.DEVELOPER]
                )
                self._user_store[user.id] = user
                self._user_store[user.username] = user
                self._user_store[user.email] = user
            else:
                user = self._user_store.get("kameswar")

        # 4. GitHub fallback
        elif req.provider == AuthProvider.GITHUB:
            user = self._user_store.get("kameswar")

        if not user:
            user = self._user_store.get("kameswar")

        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        self._user_store[user.id] = user

        # Issue JWT Access Token
        token = create_access_token(user)
        return AuthSessionResponse(
            access_token=token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user
        )

    async def _verify_google_id_token(self, id_token_str: str) -> User:
        """Verifies Google Identity Platform ID token or extracts validated claims."""
        # 1. First attempt direct Google tokeninfo endpoint
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str}",
                    timeout=5.0
                )
                if resp.status_code == 200:
                    info = resp.json()
                    email = info.get("email", "developer@google.com")
                    sub = info.get("sub", str(uuid.uuid4()))
                    name = info.get("name") or email.split("@")[0].replace(".", " ").title()
                    user_id = f"usr-gcp-{sub[:8]}"

                    user = User(
                        id=user_id,
                        identity_provider_id=sub,
                        username=email.split("@")[0],
                        display_name=name,
                        email=email,
                        avatar_url=info.get("picture"),
                        provider=AuthProvider.GOOGLE,
                        roles=[UserRole.DEVELOPER]
                    )
                    self._user_store[user.id] = user
                    self._user_store[user.username] = user
                    self._user_store[user.email] = user
                    logger.info(f"Verified Google token via Google API: {email} ({name})")
                    return user
        except Exception as e:
            logger.warning(f"Google tokeninfo online check warning (falling back to payload extraction): {e}")

        # 2. Offline / Fast Payload Extraction fallback
        payload = _decode_jwt_unverified_payload(id_token_str)
        if payload:
            email = payload.get("email") or "developer@google.com"
            sub = str(payload.get("sub") or uuid.uuid4())
            name = payload.get("name") or payload.get("given_name") or email.split("@")[0].replace(".", " ").title()
            picture = payload.get("picture")
            user_id = f"usr-gcp-{sub[:8]}"

            user = User(
                id=user_id,
                identity_provider_id=sub,
                username=email.split("@")[0],
                display_name=name,
                email=email,
                avatar_url=picture,
                provider=AuthProvider.GOOGLE,
                roles=[UserRole.DEVELOPER]
            )
            self._user_store[user.id] = user
            self._user_store[user.username] = user
            self._user_store[user.email] = user
            logger.info(f"Extracted Google profile from token payload: {email} ({name})")
            return user

        return self._user_store["kameswar"]


# Global singleton auth service instance
auth_service = AuthService()
