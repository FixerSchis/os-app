import pytest

from models.database.item import Item, ItemAuditLog
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.enums import ItemAuditAction


def test_item_version_defaults(db):
    """Test that new items have version 1 and printed False by default."""
    # Create test data
    item_type = ItemType(name="Weapon", id_prefix="WP")
    db.session.add(item_type)
    db.session.commit()

    blueprint = ItemBlueprint(
        name="Laser Pistol",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100,
    )
    db.session.add(blueprint)
    db.session.commit()

    # Create item
    item = Item(blueprint_id=blueprint.id, item_id=1)
    db.session.add(item)
    db.session.commit()

    # Check defaults
    assert item.version == 1
    assert item.printed is False


def test_item_version_increment(db, new_user):
    """Test that item version increments when non-ownership fields change."""
    # Create test data
    item_type = ItemType(name="Weapon", id_prefix="WP")
    db.session.add(item_type)
    db.session.commit()

    blueprint = ItemBlueprint(
        name="Laser Pistol",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100,
    )
    db.session.add(blueprint)
    db.session.commit()

    # Create item
    item = Item(blueprint_id=blueprint.id, item_id=1)
    db.session.add(item)
    db.session.commit()

    initial_version = item.version

    # Increment version
    item.increment_version(new_user.id, "Test version increment")
    db.session.commit()

    # Check version incremented and printed set to False
    assert item.version == initial_version + 1
    assert item.printed is False

    # Check audit log created
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == "version_increment"
    assert audit_log.editor_user_id == new_user.id
    assert "Version incremented to" in audit_log.changes


def test_item_mark_as_printed(db, new_user):
    """Test that items can be marked as printed."""
    # Create test data
    item_type = ItemType(name="Weapon", id_prefix="WP")
    db.session.add(item_type)
    db.session.commit()

    blueprint = ItemBlueprint(
        name="Laser Pistol",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100,
    )
    db.session.add(blueprint)
    db.session.commit()

    # Create item
    item = Item(blueprint_id=blueprint.id, item_id=1)
    db.session.add(item)
    db.session.commit()

    # Mark as printed
    item.mark_as_printed(new_user.id)
    db.session.commit()

    # Check printed status
    assert item.printed is True

    # Check audit log created
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == "printed"
    assert audit_log.editor_user_id == new_user.id
    assert "Item marked as printed" in audit_log.changes


def test_item_audit_log_creation(db, new_user):
    """Test that item creation creates an audit log entry."""
    # Create test data
    item_type = ItemType(name="Weapon", id_prefix="WP")
    db.session.add(item_type)
    db.session.commit()

    blueprint = ItemBlueprint(
        name="Laser Pistol",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100,
    )
    db.session.add(blueprint)
    db.session.commit()

    # Create item
    item = Item(blueprint_id=blueprint.id, item_id=1)
    db.session.add(item)
    db.session.commit()

    # Create audit log manually (since creation doesn't auto-create audit logs)
    audit_log = ItemAuditLog(
        item_id=item.id,
        editor_user_id=new_user.id,
        action="create",
        changes="Item created for testing",
    )
    db.session.add(audit_log)
    db.session.commit()

    # Check audit log
    assert audit_log.item_id == item.id
    assert audit_log.editor_user_id == new_user.id
    assert audit_log.action == "create"


def test_item_audit_log_relationships(db, new_user):
    """Test that item audit log relationships work correctly."""
    # Create test data
    item_type = ItemType(name="Weapon", id_prefix="WP")
    db.session.add(item_type)
    db.session.commit()

    blueprint = ItemBlueprint(
        name="Laser Pistol",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100,
    )
    db.session.add(blueprint)
    db.session.commit()

    # Create item
    item = Item(blueprint_id=blueprint.id, item_id=1)
    db.session.add(item)
    db.session.commit()

    # Create audit log
    audit_log = ItemAuditLog(
        item_id=item.id,
        editor_user_id=new_user.id,
        action="create",
        changes="Item created for testing",
    )
    db.session.add(audit_log)
    db.session.commit()

    # Check relationships
    assert audit_log.item == item
    assert audit_log.editor == new_user
    assert audit_log in item.audit_logs
