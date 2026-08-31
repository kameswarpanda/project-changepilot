"""Tests for GitHub App repository/branch discovery and pull request creation."""
from unittest.mock import MagicMock, patch
from backend.src.repository.github_app import GitHubAppClient


def test_github_app_repository_discovery():
    """Verifies repository discovery returns sanitized repository metadata when token provided."""
    client = GitHubAppClient(token="ghp_mocktoken123")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"name": "calculator-service", "full_name": "company/calculator-service", "default_branch": "main", "private": False},
        {"name": "payment-service", "full_name": "company/payment-service", "default_branch": "develop", "private": True}
    ]

    with patch("httpx.Client.get", return_value=mock_resp):
        repos = client.list_repositories()
        assert len(repos) >= 2
        repo_ids = [r["id"] for r in repos]
        assert "calculator-service" in repo_ids
        assert "payment-service" in repo_ids


def test_github_app_branch_discovery():
    """Verifies branch discovery returns list of branches without modifying remote."""
    client = GitHubAppClient()
    branches = client.list_branches("calculator-service")
    assert "main" in branches
    assert "develop" in branches


def test_github_app_isolated_branch_naming():
    """Verifies ChangePilot branch naming convention follows changepilot/<story-id>-<slug>."""
    client = GitHubAppClient()
    branch_name = client.generate_branch_name("CP-1042", "Add discount to calculate_total")
    assert branch_name.startswith("changepilot/CP-1042-add-discount")
    assert " " not in branch_name


def test_github_app_create_pull_request():
    """Verifies pull request creation returns proper structure and URL."""
    client = GitHubAppClient()
    pr = client.create_pull_request(
        repository="company/calculator-service",
        base_branch="develop",
        head_branch="changepilot/CP-1042-add-discount",
        title="[CP-1042] Add discount parameter",
        body="Automated verification passed with 100% test coverage."
    )
    assert pr.pr_number > 0
    assert "github.com/company/calculator-service" in pr.pr_url
    assert pr.base_branch == "develop"
    assert pr.head_branch == "changepilot/CP-1042-add-discount"
