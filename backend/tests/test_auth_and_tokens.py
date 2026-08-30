"""Tests for JWT token creation, validation, and authentication service."""
import pytest
from datetime import timedelta
from backend.src.auth.jwt_handler import create_access_token, decode_access_token
from backend.src.auth.models import AuthProvider, LoginRequest, RegisterRequest, User, UserRole
from backend.src.auth.service import AuthService


def test_jwt_create_and_decode():
    """Verifies that a valid JWT is created and decoded with all claims intact."""
    user = User(
        id="usr-test-1",
        identity_provider_id="gh-12345",
        username="tester",
        display_name="Test User",
        email="tester@example.com",
        provider=AuthProvider.GOOGLE,
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
    assert payload.provider == "google"
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


@pytest.mark.asyncio
async def test_auth_service_register_and_login_flow():
    """Verifies user registration with email/password and subsequent login."""
    auth_svc = AuthService()
    
    # 1. Register new user
    reg_req = RegisterRequest(
        email="developer.lead@enterprise.com",
        password="SecurePassword2026!",
        display_name="Lead Engineer"
    )
    reg_session = auth_svc.register_user(reg_req)
    assert reg_session.access_token is not None
    assert reg_session.user.email == "developer.lead@enterprise.com"
    assert reg_session.user.display_name == "Lead Engineer"

    # 2. Login with correct password
    login_req = LoginRequest(
        provider=AuthProvider.PASSWORD,
        email="developer.lead@enterprise.com",
        password="SecurePassword2026!"
    )
    login_session = await auth_svc.authenticate(login_req)
    assert login_session.access_token is not None
    assert login_session.user.id == reg_session.user.id

    # 3. Login with wrong password throws ValueError
    wrong_pw_req = LoginRequest(
        provider=AuthProvider.PASSWORD,
        email="developer.lead@enterprise.com",
        password="WrongPassword123"
    )
    with pytest.raises(ValueError):
        await auth_svc.authenticate(wrong_pw_req)


@pytest.mark.asyncio
async def test_auth_service_google_login():
    """Verifies Google Sign-In issuance."""
    auth_svc = AuthService()
    google_req = LoginRequest(
        provider=AuthProvider.GOOGLE,
        email="alex.google@cloud.com"
    )
    session = await auth_svc.authenticate(google_req)
    assert session.access_token is not None
    assert session.user.provider == AuthProvider.GOOGLE
    assert session.user.email == "alex.google@cloud.com"


def test_strong_password_validator():
    """Verifies that password complexity rules are strictly enforced."""
    from backend.src.auth.service import validate_strong_password
    valid, msg = validate_strong_password("Short1!")
    assert not valid
    assert "8 characters" in msg

    valid, msg = validate_strong_password("alllowercase1!")
    assert not valid
    assert "uppercase" in msg

    valid, msg = validate_strong_password("ALLUPPERCASE1!")
    assert not valid
    assert "lowercase" in msg

    valid, msg = validate_strong_password("NoNumberHere!")
    assert not valid
    assert "number" in msg

    valid, msg = validate_strong_password("NoSpecial123")
    assert not valid
    assert "special character" in msg

    valid, msg = validate_strong_password("StrongPass123!")
    assert valid
    assert msg == ""


def test_otp_forgot_password_full_flow():
    """Verifies the 3-step OTP password reset flow."""
    auth_svc = AuthService()
    email = "security_lead@changepilot.dev"

    # Step 1: Request OTP
    res = auth_svc.request_password_reset_otp(email)
    assert isinstance(res, dict)
    otp = res["dev_otp"]
    assert isinstance(otp, str)
    assert len(otp) == 6

    # Step 2: Verify with bad OTP raises ValueError
    with pytest.raises(ValueError) as exc:
        auth_svc.verify_password_reset_otp(email, "000000")
    assert "Invalid verification code" in str(exc.value)

    # Step 3: Verify with correct OTP
    good_res = auth_svc.verify_password_reset_otp(email, otp)
    assert good_res["success"] is True

    # Step 4: Reset password with weak password fails
    with pytest.raises(ValueError) as exc:
        auth_svc.reset_password_with_otp(email, otp, "weak")
    assert "Password" in str(exc.value)

    # Step 5: Reset password with strong password succeeds
    reset_ok = auth_svc.reset_password_with_otp(email, otp, "NewSecurePass2026!#")
    assert reset_ok["success"] is True

