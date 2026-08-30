"""Repository Manager providing isolated workspaces and safe Git operations."""
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from git import Repo

from backend.src.config import settings

logger = logging.getLogger("changepilot.repository.manager")


class RepositorySecurityError(Exception):
    """Raised when a repository operation violates safety constraints."""
    pass


class IsolatedWorkspace:
    """Represents an isolated working copy of a repository for a single execution."""

    def __init__(
        self,
        workspace_path: Path,
        branch_name: str,
        repo: Optional[Repo] = None,
        baseline_sha: Optional[str] = None
    ):
        self.path = workspace_path
        self.branch_name = branch_name
        self.repo = repo
        self.baseline_sha = baseline_sha
        self._cleaned = False

    def get_diff(self, base_branch: str = "main") -> str:
        """Returns unified diff of all modifications relative to baseline or HEAD."""
        if not self.repo:
            return ""
        try:
            # Check uncommitted changes first
            uncommitted = self.repo.git.diff("HEAD")
            if uncommitted:
                return uncommitted

            # Check diff against baseline commit
            if self.baseline_sha:
                try:
                    return self.repo.git.diff(self.baseline_sha, "HEAD")
                except Exception:
                    pass

            # Fallback to HEAD~1
            try:
                return self.repo.git.diff("HEAD~1", "HEAD")
            except Exception:
                pass

            # Fallback to base branch
            if base_branch in self.repo.heads:
                return self.repo.git.diff(base_branch, self.branch_name)

            return ""
        except Exception as e:
            logger.warning(f"Failed to obtain git diff: {e}")
            return ""

    def commit_changes(self, message: str) -> bool:
        """Stages all changes and commits them in the isolated workspace."""
        if not self.repo:
            return False
        try:
            self.repo.git.add(all=True)
            # Check if there are any staged changes
            if self.repo.is_dirty(index=True, working_tree=True, untracked_files=True):
                self.repo.index.commit(message)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    def cleanup(self, force: bool = False):
        """Safely cleans up the temporary workspace directory."""
        if self._cleaned:
            return
        try:
            if self.repo:
                self.repo.close()
            if self.path.exists():
                # On Windows, readonly files may block rmtree, use onerror handler
                def on_rm_error(func, path, exc_info):
                    try:
                        os.chmod(path, 0o777)
                        func(path)
                    except Exception:
                        pass
                shutil.rmtree(self.path, onerror=on_rm_error)
            self._cleaned = True
            logger.info(f"Cleaned up workspace at {self.path}")
        except Exception as e:
            logger.warning(f"Error during workspace cleanup: {e}")


class RepositoryManager:
    """Manages repository validation, isolation, cloning, and branch lifecycle."""

    def __init__(self, base_workspace_dir: Optional[str] = None):
        self.base_workspace_dir = Path(base_workspace_dir or settings.workspace_base_dir).resolve()
        self.base_workspace_dir.mkdir(parents=True, exist_ok=True)

    def validate_repository_location(self, location: str) -> str:
        """Validates that the repository location is safe (local path, DB repo, shorthand, or approved URL)."""
        location = location.strip()
        if not location:
            raise RepositorySecurityError("Repository location cannot be empty.")

        # Block command injection flags in Git URL/path
        if location.startswith("-") or "--" in location:
            raise RepositorySecurityError("Repository location contains invalid command-line flags.")

        # 1. Check local path directly
        local_path = Path(location)
        if local_path.exists():
            return str(local_path.resolve())

        # 2. Check if location is registered in ChangePilot database
        try:
            from backend.src.database.repository import DatabaseRepository
            db_repo = DatabaseRepository()
            matched = db_repo.get_repository(location)
            if matched and matched.get("clone_url"):
                return matched["clone_url"]
        except Exception:
            pass

        # 3. Check remote HTTP/HTTPS Git URL
        if location.startswith("https://") or location.startswith("http://"):
            for forbidden in [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]:
                if forbidden in location:
                    raise RepositorySecurityError(f"Repository URL contains forbidden character: {forbidden}")
            return location

        # 4. Check GitHub shorthand "owner/repo" or "owner/repo.git" (e.g. kameswarpanda/changepilot-demo-payment)
        if "/" in location and not location.startswith("/"):
            parts = location.strip().split("/")
            if len(parts) == 2 and all(p.replace("-", "").replace("_", "").replace(".", "").isalnum() for p in parts):
                return f"https://github.com/{location.replace('.git', '')}.git"

        # 5. Check local relative directory in cwd or project root
        for candidate in [Path(".") / location, Path("..") / location]:
            if candidate.exists() and candidate.is_dir():
                return str(candidate.resolve())

        raise RepositorySecurityError(
            f"Repository location is not a valid accessible local path or HTTP(S) URL: {location}"
        )

    def check_size_limits(self, repo_path: Path):
        """Enforces limits on repository total size and file count."""
        total_size = 0
        total_files = 0
        max_bytes = settings.max_repository_size_mb * 1024 * 1024
        max_files = settings.max_repository_files

        for root, dirs, files in os.walk(repo_path):
            # Exclude .git directory from file count checks if large
            if ".git" in dirs:
                dirs.remove(".git")
            for f in files:
                total_files += 1
                if total_files > max_files:
                    raise RepositorySecurityError(
                        f"Repository exceeds maximum file count limit of {max_files} files."
                    )
                fp = Path(root) / f
                try:
                    total_size += fp.stat().st_size
                    if total_size > max_bytes:
                        raise RepositorySecurityError(
                            f"Repository exceeds maximum size limit of {settings.max_repository_size_mb} MB."
                        )
                except (OSError, FileNotFoundError):
                    continue

    def create_isolated_workspace(
        self,
        repository_location: str,
        story_id: str,
        base_branch: str = "main",
        custom_branch: Optional[str] = None,
    ) -> IsolatedWorkspace:
        """Creates an isolated copy of the repository in a unique directory."""
        validated_loc = self.validate_repository_location(repository_location)
        unique_id = uuid.uuid4().hex[:8]
        safe_story = "".join(c if c.isalnum() or c in "-_" else "_" for c in story_id)
        workspace_dir = self.base_workspace_dir / f"ws_{safe_story}_{unique_id}"
        branch_name = custom_branch or f"changepilot/{safe_story}-{unique_id}"

        workspace_dir.mkdir(parents=True, exist_ok=True)

        try:
            local_src = Path(validated_loc)
            if local_src.exists() and local_src.is_dir():
                # Local repository: copy to isolated directory
                # Check source limits first
                self.check_size_limits(local_src)

                # Copy files ignoring .git if broken, or copy everything
                shutil.copytree(local_src, workspace_dir, dirs_exist_ok=True)

                # Initialize or open git repo in workspace
                git_dir = workspace_dir / ".git"
                if not git_dir.exists():
                    repo = Repo.init(workspace_dir)
                    repo.git.add(all=True)
                    repo.index.commit("Initial repository baseline")
                else:
                    repo = Repo(workspace_dir)

                # Capture baseline commit SHA
                baseline_sha = repo.head.commit.hexsha if repo.heads else None

                # Create and checkout feature branch
                try:
                    current_heads = [h.name for h in repo.heads]
                    if branch_name not in current_heads:
                        repo.create_head(branch_name)
                    repo.heads[branch_name].checkout()
                except Exception as e:
                    logger.warning(f"Branch checkout warning: {e}")
                    repo.git.checkout("-B", branch_name)

                return IsolatedWorkspace(
                    workspace_path=workspace_dir,
                    branch_name=branch_name,
                    repo=repo,
                    baseline_sha=baseline_sha
                )

            else:
                # Remote Git repository: clone with timeout
                logger.info(f"Cloning {validated_loc} to {workspace_dir}")
                repo = Repo.clone_from(
                    url=validated_loc,
                    to_path=workspace_dir,
                    kill_after_timeout=settings.clone_timeout_seconds,
                    depth=50
                )
                self.check_size_limits(workspace_dir)
                baseline_sha = repo.head.commit.hexsha if repo.heads else None
                repo.git.checkout("-B", branch_name)
                return IsolatedWorkspace(
                    workspace_path=workspace_dir,
                    branch_name=branch_name,
                    repo=repo,
                    baseline_sha=baseline_sha
                )

        except Exception as e:
            # Clean up on failure
            try:
                shutil.rmtree(workspace_dir, ignore_errors=True)
            except Exception:
                pass
            raise RepositorySecurityError(f"Failed to prepare isolated workspace: {str(e)}") from e
