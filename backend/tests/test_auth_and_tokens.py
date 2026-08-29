"""Tests for JWT token creation, validation, and authentication service."""
import pytest
from datetime import timedelta
from backend.src.auth.jwt_handler import create_access_token, decode_access_token
from backend.src.auth.models import AuthProvider, LoginRequest, User, UserRole
from backend.src.auth.service import AuthService


def test_jwt_create_and_decode():
    """Verifies that a valid JWT is created and decoded with all claims intact."""
    user = User(
        id="usr-test-1",
        identity_provider_id="gh-12345",
        username="tester",
        display_name="Test User",
        email="tester@example.com",
        provider=AuthProvider.GITHUB,
        roles=[UserRole.DEVELOPER]
    )

    token = create_access_token(user)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.sub == user.id
    assert payload.username == user.username
    assert payload.email == user.email
    assert payload.provider == "github"
    assert "developer" in payload.roles


def test_jwt_expired_token_rejected():
    """Verifies that an expired JWT token is rejected."""
    user = User(
        id="usr-expired",
        identity_provider_id="gh-000",
        username="expired_user",
        display_name="Expired User",
        email="expired@example.com",
        provider=AuthProvider.LOCAL
    )

    token = create_access_token(user, expires_delta=timedelta(seconds=-10))
    payload = decode_access_token(token)
    assert payload is None


def test_jwt_tampered_token_rejected():
    """Verifies that tampering with a JWT token signature results in rejection."""
    user = User(
        id="usr-valid",
        identity_provider_id="gh-111",
        username="valid_user",
        display_name="Valid",
        email="valid@example.com"
    )

    token = create_access_token(user)
    tampered_token = token[:-5] + "XXXXX"
    payload = decode_access_token(tampered_token)
    assert payload is None


@pytest.mark.asyncio
async def test_auth_service_demo_login():
    """Verifies demo/local authentication creates valid session and user."""
    auth_svc = AuthService()
    req = LoginRequest(provider=AuthProvider.LOCAL, demo_username="kameswar")
    session = await auth_svc.authenticate(req)

    assert session.access_token is not None
    assert session.user.username == "kameswar"
    assert session.user.email == "kameswar@changepilot.dev"
    assert UserRole.ADMIN in session.user.roles
