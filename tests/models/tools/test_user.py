import uuid

import pytest

from models.database.permissions import Permission, Role
from models.enums import CharacterStatus
from models.tools.user import User


def test_user_password_hashing(new_user):
    """Test password hashing functionality."""
    assert new_user.check_password("password")
    assert not new_user.check_password("wrongpassword")


def test_user_permissions(db, new_user):
    """Test basic permission functionality."""
    # Create a test permission
    test_permission = Permission(
        name="test.permission", description="Test permission", category="test"
    )
    db.session.add(test_permission)

    # Create a test role with the permission
    test_role = Role(name="test_role", description="Test role")
    test_role.add_permission(test_permission)
    db.session.add(test_role)
    db.session.commit()

    # Assign role to user
    new_user.role = test_role
    db.session.commit()

    # Test permission checking
    assert new_user.has_permission("test.permission")
    assert not new_user.has_permission("nonexistent.permission")
    assert new_user.has_any_permission(["test.permission", "other.permission"])
    assert new_user.has_all_permissions(["test.permission"])


def test_owner_role_permissions(db, new_user):
    """Test that the owner role grants all permissions."""
    # Create all permissions
    permissions_data = [
        ("user.roles", "Manage user roles", "user"),
        ("character.edit_all", "Edit any character", "character"),
        ("database.backup", "Create database backups", "database"),
    ]

    permissions = {}
    for name, description, category in permissions_data:
        permission = Permission(name=name, description=description, category=category)
        db.session.add(permission)
        permissions[name] = permission

    # Create owner role with all permissions
    owner_role = Role(name="owner", description="System owner", is_system_role=True)
    for permission in permissions.values():
        owner_role.add_permission(permission)
    db.session.add(owner_role)
    db.session.commit()

    new_user.role = owner_role
    db.session.commit()

    # Owner should have all permissions
    assert new_user.has_permission("user.roles")
    assert new_user.has_permission("character.edit_all")
    assert new_user.has_permission("database.backup")


def test_admin_role_permissions(db, new_user):
    """Test that the admin role grants admin permissions but not user management."""
    # Create permissions
    permissions_data = [
        ("character.edit_all", "Edit any character", "character"),
        ("database.backup", "Create database backups", "database"),
        ("user.roles", "Manage user roles", "user"),
    ]

    permissions = {}
    for name, description, category in permissions_data:
        permission = Permission(name=name, description=description, category=category)
        db.session.add(permission)
        permissions[name] = permission

    # Create admin role with specific permissions
    admin_role = Role(name="admin", description="Administrator", is_system_role=True)
    admin_role.add_permission(permissions["character.edit_all"])
    admin_role.add_permission(permissions["database.backup"])
    # Note: admin role doesn't get user.roles permission
    db.session.add(admin_role)
    db.session.commit()

    new_user.role = admin_role
    db.session.commit()

    # Admin should have most permissions but not user management
    assert new_user.has_permission("character.edit_all")
    assert new_user.has_permission("database.backup")
    assert not new_user.has_permission("user.roles")  # Admin doesn't have user management


def test_user_character_points(new_user):
    """Test character point management."""
    assert new_user.character_points == 0.0
    new_user.add_character_points(10)
    assert new_user.character_points == 10.0
    assert new_user.can_spend_character_points(5)
    assert not new_user.can_spend_character_points(15)
    new_user.spend_character_points(5)
    assert new_user.character_points == 5.0
    with pytest.raises(ValueError):
        new_user.spend_character_points(10)


def test_user_active_character(db, new_user, character):
    """Test active character detection."""
    # Initially no active character
    character.status = CharacterStatus.DEVELOPING.value
    db.session.commit()
    assert not new_user.has_active_character()
    assert new_user.get_active_character() is None

    # Set character to active
    character.status = CharacterStatus.ACTIVE.value
    db.session.commit()
    assert new_user.has_active_character()
    active_char = new_user.get_active_character()
    assert active_char is not None
    assert active_char.id == character.id
    assert active_char.status == CharacterStatus.ACTIVE.value


def test_email_verification_token(new_user):
    """Test the email verification token generation and validation."""
    token = new_user.generate_verification_token()
    assert token is not None
    assert new_user.verification_token == token
    assert new_user.verify_email(token)
    assert new_user.email_verified
    assert new_user.verification_token is None

    # Test with invalid token
    assert not new_user.verify_email("invalid_token")


def test_email_change(db, new_user):
    """Test the email change request and confirmation process."""
    new_email = "new.email@example.com"
    success, token = new_user.request_email_change(new_email)
    db.session.commit()

    assert success
    assert token is not None
    assert new_user.new_email == new_email

    # Confirm with a different user (should fail)
    other_user = User(email="other@example.com", first_name="Other", surname="User")
    other_user.set_password("password")
    db.session.add(other_user)
    db.session.commit()
    assert not other_user.confirm_email_change(token)

    # Confirm with correct user
    success = new_user.confirm_email_change(token)
    db.session.commit()

    assert success
    assert new_user.email == new_email
    assert new_user.new_email is None


def test_password_reset(new_user):
    """Test the password reset token generation and validation."""
    token = new_user.generate_reset_token()
    assert token is not None
    assert new_user.verify_reset_token(token)

    # Test reset with a new password
    new_password = "new_password"
    assert new_user.reset_password(token, new_password)
    assert new_user.check_password(new_password)
    assert not new_user.check_password("password")
    assert new_user.reset_token is None

    # Test with invalid token
    assert not new_user.reset_password("invalid_token", "another_password")


def test_notification_preferences(new_user):
    """Test user notification preferences."""
    # Default should be True, even if email not verified
    assert new_user.should_notify("downtime_completed")

    new_user.email_verified = True
    assert new_user.should_notify("downtime_completed")

    # Update preferences
    prefs = {"downtime_completed": False, "new_event": True}
    new_user.update_notification_preferences(prefs)
    assert not new_user.should_notify("downtime_completed")
    assert new_user.should_notify("new_event")
    assert new_user.should_notify("wiki_published")  # Unchanged preference
