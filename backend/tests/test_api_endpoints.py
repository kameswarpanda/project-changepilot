"""Tests for FastAPI HTTP endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.src.api.server import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "ChangePilot"


def test_analyze_repository_endpoint(tmp_path):
    (tmp_path / "index.py").write_text("print('test')", encoding="utf-8")
    response = client.post("/api/repository/analyze", json={"repository_location": str(tmp_path)})
    assert response.status_code == 200
    data = response.json()
    assert data["primary_language"] == "Python"
    assert "index.py" in data["all_files"]


def test_analyze_repository_invalid_path():
    response = client.post("/api/repository/analyze", json={"repository_location": "non_existent_folder_xyz_123"})
    assert response.status_code == 400


def test_delete_repository_endpoint():
    # Connect a repo first
    client.post(
        "/api/repositories/connect",
        json={"repository_name": "test-repo-to-delete", "provider": "github", "base_branch": "main", "is_public": True}
    )
    # Delete the repo
    del_resp = client.delete("/api/repositories/test-repo-to-delete")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"


def test_assigned_tickets_endpoint():
    """Verifies that the /api/integrations/assigned-tickets endpoint returns structured tickets."""
    resp = client.get("/api/integrations/assigned-tickets")
    assert resp.status_code == 200
    tickets = resp.json()
    assert isinstance(tickets, list)
    assert len(tickets) >= 3
    sources = [t["source"].lower() for t in tickets]
    assert any("jira" in s for s in sources)
    assert any("azure" in s or "ado" in s for s in sources)
    assert any("github" in s for s in sources)


def test_otp_api_endpoints():
    """Verifies the HTTP endpoints for OTP password reset."""
    email = "api_test_user@changepilot.dev"

    # 1. Request OTP
    req_resp = client.post("/api/auth/forgot-password/request-otp", json={"email": email})
    assert req_resp.status_code == 200
    otp = req_resp.json().get("dev_otp")
    assert otp is not None
    assert len(otp) == 6

    # 2. Verify with valid OTP
    verify_resp = client.post("/api/auth/forgot-password/verify-otp", json={"email": email, "otp": otp})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["success"] is True

    # 3. Reset password
    reset_resp = client.post("/api/auth/forgot-password/reset-password", json={
        "email": email,
        "otp": otp,
        "new_password": "NewSecret2026!#"
    })
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

