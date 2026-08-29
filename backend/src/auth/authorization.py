"""Authorization and Repository Access Control Layer for ChangePilot."""
import logging
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from backend.src.auth.models import User, UserRole

logger = logging.getLogger("changepilot.auth.authorization")


class AccessLevel(str, Enum):
    """Repository access permission levels."""
    READ = "READ"          # Can inspect structure and view history
    WRITE = "WRITE"        # Can create change requests & drafts
    EXECUTE = "EXECUTE"    # Can run autonomous modification pipelines


class RepositoryPermission(BaseModel):
    """Permission mapping between a User and a Repository."""
    repository_id: str
    repository_name: str
    owner_user_id: str
    access_levels: Set[AccessLevel] = Field(default_factory=lambda: {AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE})
    is_public: bool = False


class AuthorizationService:
    """Evaluates granular access permissions for Users, Repositories, and Pipelines."""

    def __init__(self):
        # In-memory repository permissions store (repository_id -> RepositoryPermission)
        self._repo_permissions: Dict[str, RepositoryPermission] = {}
        # User to accessible repository IDs
        self._user_repos: Dict[str, Set[str]] = {}
        self._seed_default_permissions()

    def _seed_default_permissions(self):
        """Seeds default repository access rules for standard repositories."""
        # Demo calculator repository (Accessible to all authenticated users)
        demo_perm = RepositoryPermission(
            repository_id="demo_repo",
            repository_name="demo_repo (Calculator)",
            owner_user_id="usr-kameswar-01",
            access_levels={AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE},
            is_public=True
        )
        self.register_repository("usr-kameswar-01", demo_perm)

        # Enterprise Monorepo (Belongs to Kameswar)
        enterprise_perm = RepositoryPermission(
            repository_id="core-infrastructure-monorepo",
            repository_name="company/core-infrastructure-monorepo",
            owner_user_id="usr-kameswar-01",
            access_levels={AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE},
            is_public=False
        )
        self.register_repository("usr-kameswar-01", enterprise_perm)

    def register_repository(self, user_id: str, perm: RepositoryPermission):
        """Associates a connected repository with an owner user."""
        self._repo_permissions[perm.repository_id] = perm
        if user_id not in self._user_repos:
            self._user_repos[user_id] = set()
        self._user_repos[user_id].add(perm.repository_id)

    def has_repository_access(
        self,
        user: User,
        repository_id: str,
        required_level: AccessLevel = AccessLevel.READ
    ) -> bool:
        """Evaluates whether an authenticated user has the requested permission level on a repository."""
        # Admins have universal permission
        if UserRole.ADMIN in user.roles:
            return True

        perm = self._repo_permissions.get(repository_id)
        if not perm:
            # For dynamic local paths or new demo targets, default allow for owner / developer
            return True

        # Public repositories are readable by all authenticated users
        if perm.is_public and required_level == AccessLevel.READ:
            return True

        # User is the owner of the repository
        if perm.owner_user_id == user.id:
            return required_level in perm.access_levels

        # Check user specific permissions
        if user.id in self._user_repos and repository_id in self._user_repos[user.id]:
            return required_level in perm.access_levels

        logger.warning(f"User {user.username} ({user.id}) denied {required_level.value} access to {repository_id}")
        return False

    def list_accessible_repositories(self, user: User) -> List[RepositoryPermission]:
        """Lists all repositories accessible to the given user."""
        if UserRole.ADMIN in user.roles:
            return list(self._repo_permissions.values())

        user_repo_ids = self._user_repos.get(user.id, set())
        accessible = []
        for repo_id, perm in self._repo_permissions.items():
            if perm.is_public or perm.owner_user_id == user.id or repo_id in user_repo_ids:
                accessible.append(perm)
        return accessible


# Global singleton authorization service
authz_service = AuthorizationService()
