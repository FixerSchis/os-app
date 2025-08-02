import pytest
from flask import url_for

from models.database.permissions import Permission, Role
from models.tools.user import User


class TestRoleManagement:
    """Test cases for role management functionality."""

    def test_role_list_access_requires_permission(self, test_client, regular_user):
        """Test that role list requires user.roles permission."""
        # Ensure the user is properly authenticated
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/roles")
        # User should be redirected to login if not authenticated, or get 403 if authenticated
        # but no permission
        assert response.status_code in [302, 403]
        if response.status_code == 302:
            # The redirect might go to '/' which then redirects to login
            assert response.location in ["/", "/auth/login"] or "/auth/login" in response.location

    def test_role_list_with_permission(self, test_client, auth_user_with_roles_permission):
        """Test that role list is accessible with proper permission."""
        response = test_client.get("/tools/roles")
        assert response.status_code == 200
        assert b"Role Management" in response.data

    def test_create_role_requires_permission(self, test_client, regular_user):
        """Test that creating roles requires user.roles permission."""
        # Ensure the user is properly authenticated
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/roles/new")
        # User should be redirected to login if not authenticated, or get 403 if authenticated
        # but no permission
        assert response.status_code in [302, 403]
        if response.status_code == 302:
            # The redirect might go to '/' which then redirects to login
            assert response.location in ["/", "/auth/login"] or "/auth/login" in response.location

    def test_create_role_with_permission(self, test_client, auth_user_with_roles_permission):
        """Test that creating roles is accessible with proper permission."""
        response = test_client.get("/tools/roles/new")
        assert response.status_code == 200
        assert b"Create New Role" in response.data

    def test_edit_owner_role_forbidden(
        self, test_client, auth_user_with_roles_permission, db_session
    ):
        """Test that editing owner role is forbidden."""
        # Create owner role
        owner_role = Role(name="owner", description="Owner role", is_system_role=True)
        db_session.add(owner_role)
        db_session.commit()

        response = test_client.get(f"/tools/roles/{owner_role.id}/edit")
        assert response.status_code == 302  # Redirect with flash message

    def test_delete_owner_role_forbidden(
        self, test_client, auth_user_with_roles_permission, db_session
    ):
        """Test that deleting owner role is forbidden."""
        # Create owner role
        owner_role = Role(name="owner", description="Owner role", is_system_role=True)
        db_session.add(owner_role)
        db_session.commit()

        response = test_client.post(f"/tools/roles/{owner_role.id}/delete")
        assert response.status_code == 302  # Redirect with flash message

    def test_delete_default_role_forbidden(
        self, test_client, auth_user_with_roles_permission, db_session
    ):
        """Test that deleting default role is forbidden."""
        # Create default role
        default_role = Role(name="default", description="Default role", is_system_role=True)
        db_session.add(default_role)
        db_session.commit()

        response = test_client.post(f"/tools/roles/{default_role.id}/delete")
        assert response.status_code == 302  # Redirect with flash message

    def test_promote_user_requires_owner_promote_permission(self, test_client, regular_user):
        """Test that promoting users requires owner.promote permission."""
        # Ensure the user is properly authenticated
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.post("/tools/roles/promote-user")
        # User should be redirected to login if not authenticated, or get 403 if authenticated
        # but no permission
        assert response.status_code in [302, 403]
        if response.status_code == 302:
            # The redirect might go to '/' which then redirects to login
            assert response.location in ["/", "/auth/login"] or "/auth/login" in response.location


@pytest.fixture
def auth_user_with_roles_permission(test_client, db_session):
    """Create a user with user.roles permission."""
    import uuid

    # Create a new user
    unique_id = uuid.uuid4().hex
    user = User(
        email=f"test_user_{unique_id}@example.com",
        first_name="Test",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)

    # Create a permission
    permission = Permission(name="user.roles", description="Manage roles", category="user")
    db_session.add(permission)

    # Create a role with the permission (use unique name)
    role = Role(name=f"test_role_{unique_id}", description="Test role")
    role.permissions.append(permission)
    db_session.add(role)

    # Assign role to user
    user.role = role
    db_session.commit()

    # Set up session
    with test_client.session_transaction() as sess:
        sess["_user_id"] = user.id
        sess["_fresh"] = True

    return user
