import uuid

from werkzeug.datastructures import MultiDict

from models.database.item_type import ItemType


def test_item_types_list_unauthorized(test_client, db):
    response = test_client.get("/db/item-types/")
    assert response.status_code == 200
    assert b"Item Type" in response.data or b"item type" in response.data
    assert b"New Item Type" not in response.data


def test_item_types_list_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get("/db/item-types/")
    assert response.status_code == 200
    assert b"Item Type" in response.data or b"item type" in response.data


def test_item_types_create_get_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get("/db/item-types/create")
    assert response.status_code == 200
    assert b"Item Type" in response.data or b"item type" in response.data


def test_item_types_create_post_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    unique_name = f"ItemType {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("id_prefix", "AB"),
        ]
    )
    response = test_client.post(
        "/db/item-types/create",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Item type created successfully" in response.data
    item_type = ItemType.query.filter_by(name=unique_name).first()
    assert item_type is not None
    assert item_type.id_prefix == "AB"


def test_item_types_create_missing_fields(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    post_data = MultiDict(
        [
            ("name", ""),
            ("id_prefix", ""),
        ]
    )
    response = test_client.post(
        "/db/item-types/create",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Name and ID prefix are required" in response.data


def test_item_types_create_invalid_id_prefix(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    unique_name = f"ItemType {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("id_prefix", "A"),  # Too short
        ]
    )
    response = test_client.post(
        "/db/item-types/create",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"ID prefix must be exactly 2 characters" in response.data


def test_item_types_create_unauthorized(test_client, db):
    response = test_client.get("/db/item-types/create")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_item_types_edit_get_authorized(test_client, rules_team_user, item_type, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get(f"/db/item-types/{item_type.id}/edit")
    assert response.status_code == 200
    assert bytes(item_type.name, "utf-8") in response.data


def test_item_types_edit_post_authorized(test_client, rules_team_user, item_type, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    new_name = f"Updated ItemType {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", new_name),
            ("id_prefix", "CD"),
        ]
    )
    response = test_client.post(
        f"/db/item-types/{item_type.id}/edit",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Item type updated successfully" in response.data
    db.session.expire_all()
    updated = db.session.get(ItemType, item_type.id)
    assert updated.name == new_name
    assert updated.id_prefix == "CD"


def test_item_types_edit_missing_fields(test_client, rules_team_user, item_type, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    post_data = MultiDict(
        [
            ("name", ""),
            ("id_prefix", ""),
        ]
    )
    response = test_client.post(
        f"/db/item-types/{item_type.id}/edit",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Name and ID prefix are required" in response.data


def test_item_types_edit_unauthorized(test_client, item_type, db):
    response = test_client.get(f"/db/item-types/{item_type.id}/edit")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_item_types_edit_not_found(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get("/db/item-types/99999/edit")
    assert response.status_code == 404


def test_item_types_delete_authorized(test_client, rules_team_user, item_type, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.post(f"/db/item-types/{item_type.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Item type deleted successfully" in response.data
    deleted = db.session.get(ItemType, item_type.id)
    assert deleted is None


def test_item_types_delete_with_blueprints(test_client, rules_team_user, item_blueprint_obj, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.post(
        f"/db/item-types/{item_blueprint_obj.item_type_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Cannot delete item type with associated blueprints" in response.data
    item_type = db.session.get(ItemType, item_blueprint_obj.item_type_id)
    assert item_type is not None


def test_item_types_delete_unauthorized(test_client, item_type, db):
    response = test_client.post(f"/db/item-types/{item_type.id}/delete")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_item_types_delete_not_found(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.post("/db/item-types/99999/delete", follow_redirects=True)
    assert response.status_code == 404
