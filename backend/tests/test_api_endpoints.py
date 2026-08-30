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
