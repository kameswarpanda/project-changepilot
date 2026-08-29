"""Authentication and Identity Service supporting Google Identity, GitHub OAuth, and Local Demo."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
import httpx

from backend.src.auth.jwt_handler import create_access_token
from backend.src.auth.models import AuthProvider, AuthSessionResponse, LoginRequest, User, UserRole
from backend.src.config import settings

logger = logging.getLogger("changepilot.auth.service")


class AuthService:
    """Service handling multi-provider authentication and session issuance."""

    def __init__(self):
        # In-memory user cache for local & fast execution
        self._user_store: Dict[str, User] = {}
        self._seed_default_users()

    def _seed_default_users(self):
        """Pre-seeds standard developer & admin profiles for instant zero-friction local execution."""
        kameswar = User(
            id="usr-kameswar-01",
            identity_provider_id="gh-kameswar-2026",
            username="kameswar",
            display_name="Kameswar",
            email="kameswar@changepilot.dev",
            avatar_url="https://avatars.githubusercontent.com/u/583231",
            provider=AuthProvider.GITHUB,
            roles=[UserRole.ADMIN, UserRole.DEVELOPER]
        )
        alex = User(
            id="usr-alex-02",
            identity_provider_id="gh-alex-mercer",
            username="alex.mercer",
            display_name="Alex Mercer",
            email="alex@changepilot.dev",
            avatar_url=None,
            provider=AuthProvider.GITHUB,
            roles=[UserRole.DEVELOPER]
        )
        self._user_store[kameswar.id] = kameswar
        self._user_store[kameswar.username] = kameswar
        self._user_store[alex.id] = alex
        self._user_store[alex.username] = alex

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves a user by their unique ChangePilot ID."""
        return self._user_store.get(user_id)

    async def authenticate(self, req: LoginRequest) -> AuthSessionResponse:
        """Authenticates user via provider token, OAuth code, or demo login."""
        user: Optional[User] = None

        if req.provider == AuthProvider.LOCAL or req.demo_username:
            username = (req.demo_username or "kameswar").lower().strip()
            user = self._user_store.get(username)
            if not user:
                # Create a local user on-the-fly
                user_id = f"usr-{username}-{uuid.uuid4().hex[:4]}"
                user = User(
                    id=user_id,
                    identity_provider_id=f"local-{username}",
                    username=username,
                    display_name=username.capitalize(),
                    email=f"{username}@changepilot.local",
                    provider=AuthProvider.LOCAL,
                    roles=[UserRole.DEVELOPER]
                )
                self._user_store[user.id] = user
                self._user_store[user.username] = user

        elif req.provider == AuthProvider.GITHUB:
            # If GitHub client secret is configured, exchange code for user info
            if settings.github_client_id and settings.github_client_secret and req.token_or_code:
                user = await self._verify_github_oauth(req.token_or_code)
            else:
                # Fallback to standard developer profile
                user = self._user_store.get("kameswar")

        elif req.provider == AuthProvider.GOOGLE:
            # Google Identity Platform ID token verification
            if req.token_or_code:
                user = await self._verify_google_id_token(req.token_or_code)
            else:
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

    async def _verify_github_oauth(self, code: str) -> User:
        """Exchanges GitHub OAuth code for user profile."""
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": settings.github_client_id,
                        "client_secret": settings.github_client_secret,
                        "code": code,
                    },
                    timeout=10.0
                )
                token_data = token_resp.json()
                gh_token = token_data.get("access_token")

                if not gh_token:
                    logger.warning("GitHub OAuth token exchange failed, using developer profile")
                    return self._user_store["kameswar"]

                user_resp = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {gh_token}",
                        "Accept": "application/json"
                    },
                    timeout=10.0
                )
                gh_user = user_resp.json()
                username = gh_user.get("login", "github-user")
                email = gh_user.get("email") or f"{username}@users.noreply.github.com"
                user_id = f"usr-gh-{gh_user.get('id', uuid.uuid4().hex[:6])}"

                user = User(
                    id=user_id,
                    identity_provider_id=str(gh_user.get("id")),
                    username=username,
                    display_name=gh_user.get("name") or username,
                    email=email,
                    avatar_url=gh_user.get("avatar_url"),
                    provider=AuthProvider.GITHUB,
                    roles=[UserRole.DEVELOPER]
                )
                self._user_store[user.id] = user
                return user
        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}")
            return self._user_store["kameswar"]

    async def _verify_google_id_token(self, id_token_str: str) -> User:
        """Verifies Google Identity Platform ID token."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str}",
                    timeout=10.0
                )
                if resp.status_code == 200:
                    info = resp.json()
                    email = info.get("email", "user@gmail.com")
                    sub = info.get("sub", str(uuid.uuid4()))
                    name = info.get("name", email.split("@")[0])
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
                    return user
        except Exception as e:
            logger.error(f"Google Identity token verification error: {e}")

        return self._user_store["kameswar"]


# Global singleton auth service instance
auth_service = AuthService()
