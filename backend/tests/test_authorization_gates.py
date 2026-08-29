"""Tests for authorization rules and repository permission gates."""
from backend.src.auth.authorization import AccessLevel, AuthorizationService, RepositoryPermission
from backend.src.auth.models import AuthProvider, User, UserRole


def test_authorization_admin_has_full_access():
    """Verifies that admin users bypass repository access limitations."""
    authz = AuthorizationService()
    admin_user = User(
        id="usr-admin",
        identity_provider_id="gh-admin",
        username="admin_kameswar",
        display_name="Admin",
        email="admin@example.com",
        roles=[UserRole.ADMIN]
    )

    assert authz.has_repository_access(admin_user, "private-repo-secret", AccessLevel.READ) is True
    assert authz.has_repository_access(admin_user, "private-repo-secret", AccessLevel.WRITE) is True
    assert authz.has_repository_access(admin_user, "private-repo-secret", AccessLevel.EXECUTE) is True


def test_authorization_user_denied_unregistered_private_repo():
    """Verifies that non-admin users cannot access private repositories they do not own."""
    authz = AuthorizationService()
    developer_a = User(
        id="usr-dev-a",
        identity_provider_id="gh-dev-a",
        username="dev_a",
        display_name="Developer A",
        email="dev_a@example.com",
        roles=[UserRole.DEVELOPER]
    )

    developer_b = User(
        id="usr-dev-b",
        identity_provider_id="gh-dev-b",
        username="dev_b",
        display_name="Developer B",
        email="dev_b@example.com",
        roles=[UserRole.DEVELOPER]
    )

    # Register private repository owned by Developer A
    perm = RepositoryPermission(
        repository_id="private-payroll",
        repository_name="company/private-payroll",
        owner_user_id=developer_a.id,
        access_levels={AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE},
        is_public=False
    )
    authz.register_repository(developer_a.id, perm)

    # Developer A has full access
    assert authz.has_repository_access(developer_a, "private-payroll", AccessLevel.EXECUTE) is True

    # Developer B is denied access
    assert authz.has_repository_access(developer_b, "private-payroll", AccessLevel.READ) is False
    assert authz.has_repository_access(developer_b, "private-payroll", AccessLevel.EXECUTE) is False


def test_authorization_public_repo_readable_by_all():
    """Verifies that public repositories are readable by any authenticated developer."""
    authz = AuthorizationService()
    developer = User(
        id="usr-dev-c",
        identity_provider_id="gh-dev-c",
        username="dev_c",
        display_name="Developer C",
        email="dev_c@example.com",
        roles=[UserRole.DEVELOPER]
    )

    public_perm = RepositoryPermission(
        repository_id="open-source-docs",
        repository_name="company/open-source-docs",
        owner_user_id="usr-owner-x",
        access_levels={AccessLevel.READ},
        is_public=True
    )
    authz.register_repository("usr-owner-x", public_perm)

    assert authz.has_repository_access(developer, "open-source-docs", AccessLevel.READ) is True
    assert authz.has_repository_access(developer, "open-source-docs", AccessLevel.EXECUTE) is False
