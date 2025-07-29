import pytest

from models.database.item import Item, ItemAuditLog
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.enums import ItemAuditAction, Role
from models.tools.user import User


def test_item_view_with_version_warning(test_client, item, print_template_obj):
    """Test that item view shows version mismatch warning."""
    # Test with version parameter that doesn't match
    response = test_client.get(f"/db/items/{item.id}/999/view")
    assert response.status_code == 200
    assert b"version you provided is no longer current" in response.data


def test_item_view_with_printed_warning(test_client, item, print_template_obj, db):
    """Test that item view shows printed warning for unprinted items."""
    # Ensure item is not printed
    item.printed = False
    db.session.commit()

    response = test_client.get(f"/db/items/{item.id}/1/view")
    assert response.status_code == 200
    assert b"has updated and has not yet been printed" in response.data


def test_item_edit_increments_version(test_client, rules_team_user, item, item_blueprint, db):
    """Test that editing an item increments its version when non-ownership fields change."""
    initial_version = item.version

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    # Edit the item (change expiry)
    response = test_client.post(
        f"/db/items/{item.id}/edit",
        data={"blueprint_id": item_blueprint.id, "expiry": "5", "mods_applied[]": []},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Check that version was incremented
    db.session.refresh(item)
    assert item.version == initial_version + 1
    assert item.printed is False

    # Check audit log was created
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == ItemAuditAction.VERSION_INCREMENT.value


def test_item_edit_no_version_increment(test_client, rules_team_user, item, item_blueprint, db):
    """Test that editing an item without changes doesn't increment version."""
    initial_version = item.version

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    # Edit the item with same values (no actual changes)
    response = test_client.post(
        f"/db/items/{item.id}/edit",
        data={
            "blueprint_id": item_blueprint.id,
            "expiry": str(item.expiry) if item.expiry else "",
            "mods_applied[]": [],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Check that version was not incremented
    db.session.refresh(item)
    assert item.version == initial_version

    # Check audit log was created for edit without version increment
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == ItemAuditAction.EDIT.value


def test_item_creation_creates_audit_log(test_client, rules_team_user, item_blueprint, db):
    """Test that creating an item creates an audit log entry."""
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    # Create a new item
    response = test_client.post(
        "/db/items/create",
        data={"blueprint_id": item_blueprint.id, "expiry": "10", "mods_applied[]": []},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Check that audit log was created
    item = (
        Item.query.filter_by(blueprint_id=item_blueprint.id).order_by(Item.item_id.desc()).first()
    )
    assert item is not None

    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == ItemAuditAction.CREATE.value


def test_print_unprinted_items_route(test_client, rules_team_user, item, print_template_obj, db):
    """Test the print unprinted items route."""
    # Ensure item is not printed
    item.printed = False
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/print_unprinted")

    # Should return PDF
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"

    # Check that item was marked as printed
    db.session.refresh(item)
    assert item.printed is True

    # Check audit log was created
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == ItemAuditAction.PRINTED.value


def test_print_unprinted_items_no_items(test_client, rules_team_user, item, print_template_obj, db):
    """Test print unprinted items when no unprinted items exist."""
    # Ensure item is printed
    item.printed = True
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/print_unprinted", follow_redirects=True)

    # Should redirect with flash message
    assert response.status_code == 200
    assert b"No unprinted items found" in response.data


def test_item_list_shows_version_and_printed_status(test_client, rules_team_user, item, db):
    """Test that item list shows version and printed status."""
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/")
    assert response.status_code == 200

    # Check that version and printed status are displayed
    # Version is now part of the Item ID column
    assert str(item.version).encode() in response.data
    assert b"Unprinted" in response.data or b"Printed" in response.data


def test_item_list_has_print_button(test_client, rules_team_user, item, db):
    """Test that item list has the print unprinted items button."""
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/")
    assert response.status_code == 200

    # Check that print button is present
    assert b"Print Unprinted Items" in response.data


def test_mark_item_printed_route(test_client, rules_team_user, item, db):
    """Test the mark item printed route."""
    # Ensure item is not printed
    item.printed = False
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(f"/db/items/{item.id}/mark_printed", follow_redirects=True)

    # Should redirect with success message
    assert response.status_code == 200
    assert b"has been marked as printed" in response.data

    # Check that item was marked as printed
    db.session.refresh(item)
    assert item.printed is True

    # Check audit log was created
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == ItemAuditAction.PRINTED.value


def test_mark_item_printed_already_printed(test_client, rules_team_user, item, db):
    """Test marking an already printed item as printed."""
    # Ensure item is printed
    item.printed = True
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(f"/db/items/{item.id}/mark_printed", follow_redirects=True)

    # Should redirect with info message
    assert response.status_code == 200
    assert b"already marked as printed" in response.data


def test_item_list_has_mark_printed_button(test_client, rules_team_user, item, db):
    """Test that item list has the mark printed button for unprinted items."""
    # Ensure item is not printed
    item.printed = False
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/")
    assert response.status_code == 200

    # Check that mark printed button is present
    assert b"Mark Printed" in response.data


def test_item_list_no_mark_printed_button_for_printed_items(test_client, rules_team_user, item, db):
    """Test that item list doesn't show mark printed button for already printed items."""
    # Ensure item is printed
    item.printed = True
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/")
    assert response.status_code == 200

    # Check that mark printed button is not present
    assert b"Mark Printed" not in response.data


def test_mark_item_unprinted_route(test_client, rules_team_user, item, db):
    """Test the mark item unprinted route."""
    # Ensure item is printed
    item.printed = True
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(f"/db/items/{item.id}/mark_unprinted", follow_redirects=True)

    # Should redirect with success message
    assert response.status_code == 200
    assert b"has been marked as unprinted" in response.data

    # Check that item was marked as unprinted
    db.session.refresh(item)
    assert item.printed is False

    # Check audit log was created
    audit_log = ItemAuditLog.query.filter_by(item_id=item.id).first()
    assert audit_log is not None
    assert audit_log.action == ItemAuditAction.PRINTED.value


def test_mark_item_unprinted_already_unprinted(test_client, rules_team_user, item, db):
    """Test marking an already unprinted item as unprinted."""
    # Ensure item is not printed
    item.printed = False
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(f"/db/items/{item.id}/mark_unprinted", follow_redirects=True)

    # Should redirect with info message
    assert response.status_code == 200
    assert b"already marked as unprinted" in response.data


def test_item_list_has_mark_unprinted_button(test_client, rules_team_user, item, db):
    """Test that item list has the mark unprinted button for printed items."""
    # Ensure item is printed
    item.printed = True
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/")
    assert response.status_code == 200

    # Check that mark unprinted button is present
    assert b"Mark Unprinted" in response.data


def test_item_list_no_mark_unprinted_button_for_unprinted_items(
    test_client, rules_team_user, item, db
):
    """Test that item list doesn't show mark unprinted button for already unprinted items."""
    # Ensure item is not printed
    item.printed = False
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/items/")
    assert response.status_code == 200

    # Check that mark unprinted button is not present
    assert b"Mark Unprinted" not in response.data
