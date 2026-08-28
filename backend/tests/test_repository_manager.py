"""Tests for RepositoryManager and workspace isolation."""
import os
import pytest
from pathlib import Path
from backend.src.repository.manager import RepositoryManager, RepositorySecurityError


def test_validate_repository_location_local(tmp_path):
    manager = RepositoryManager(base_workspace_dir=str(tmp_path / "workspaces"))
    loc = manager.validate_repository_location(str(tmp_path))
    assert Path(loc).resolve() == tmp_path.resolve()


def test_validate_repository_location_url(tmp_path):
    manager = RepositoryManager(base_workspace_dir=str(tmp_path / "workspaces"))
    url = "https://github.com/example/sample-repo.git"
    assert manager.validate_repository_location(url) == url


def test_validate_repository_location_injection_rejected(tmp_path):
    manager = RepositoryManager(base_workspace_dir=str(tmp_path / "workspaces"))
    with pytest.raises(RepositorySecurityError, match="invalid command-line flags"):
        manager.validate_repository_location("--upload-pack=evil")

    with pytest.raises(RepositorySecurityError, match="forbidden character"):
        manager.validate_repository_location("https://github.com/foo/bar; rm -rf /")


def test_create_isolated_workspace_local(tmp_path):
    # Setup mock local repo
    src_repo = tmp_path / "src_repo"
    src_repo.mkdir()
    (src_repo / "main.py").write_text("print('hello')", encoding="utf-8")

    manager = RepositoryManager(base_workspace_dir=str(tmp_path / "workspaces"))
    workspace = manager.create_isolated_workspace(
        repository_location=str(src_repo),
        story_id="STORY-101"
    )

    assert workspace.path.exists()
    assert (workspace.path / "main.py").exists()
    assert workspace.branch_name.startswith("changepilot/STORY-101-")

    # Cleanup
    workspace.cleanup()
    assert not workspace.path.exists()
