from models.tools.role import Role


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
