import importlib.util
from pathlib import Path

from models.database.permissions import Role


def _load_setup_permissions():
    path = Path(__file__).resolve().parents[1] / "scripts" / "setup_permissions.py"
    spec = importlib.util.spec_from_file_location("setup_permissions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_admin_role_does_not_receive_owner_promote(db):
    setup = _load_setup_permissions()
    permissions = setup.create_default_permissions()
    roles = setup.create_default_roles(permissions)

    assert roles["owner"].has_permission("owner.promote")
    assert not roles["admin"].has_permission("owner.promote")
    assert roles["admin"].has_permission("user.view")
    assert roles["admin"].has_permission("user.edit")
    assert roles["admin"].has_permission("user.roles")


def test_existing_admin_role_loses_owner_promote(db):
    setup = _load_setup_permissions()
    permissions = setup.create_default_permissions()
    roles = setup.create_default_roles(permissions)

    roles["admin"].add_permission(permissions["owner.promote"])
    db.session.commit()
    assert roles["admin"].has_permission("owner.promote")

    setup.create_default_roles(permissions)

    admin = Role.query.filter_by(name="admin").first()
    owner = Role.query.filter_by(name="owner").first()
    assert admin.has_permission("owner.promote") is False
    assert owner.has_permission("owner.promote") is True
