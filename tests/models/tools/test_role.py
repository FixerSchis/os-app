from models.database.permissions import Permission, Role


def test_new_role(db):
    """Test creation of a new Role."""
    role_name = "test_role"
    description = "A test role for testing purposes"

    role = Role(name=role_name, description=description)

    db.session.add(role)
    db.session.commit()

    # Retrieve and assert
    retrieved_role = Role.query.filter_by(name=role_name).first()

    assert retrieved_role is not None
    assert retrieved_role.name == role_name
    assert retrieved_role.description == description
    assert retrieved_role.id is not None
    assert retrieved_role.is_system_role is False


def test_role_with_permissions(db):
    """Test creating a role with permissions."""
    # Create a permission first
    permission = Permission(
        name="test.permission", description="A test permission", category="test"
    )
    db.session.add(permission)
    db.session.commit()

    # Create a role
    role = Role(name="test_role_with_perms", description="Role with permissions")
    db.session.add(role)
    db.session.commit()

    # Add permission to role
    role.add_permission(permission)
    db.session.commit()

    # Test that role has the permission
    assert role.has_permission("test.permission")
    assert len(role.permissions) == 1
    assert role.permissions[0].name == "test.permission"
