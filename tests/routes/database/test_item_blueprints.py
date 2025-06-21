import uuid

from werkzeug.datastructures import MultiDict

from models.database.item_blueprint import ItemBlueprint


def test_item_blueprints_list_unauthorized(test_client, db):
    response = test_client.get("/db/item-blueprints/")
    assert response.status_code == 200
    assert b"Blueprint" in response.data or b"blueprint" in response.data
    assert b"New Blueprint" not in response.data


def test_item_blueprints_list_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get("/db/item-blueprints/")
    assert response.status_code == 200
    assert b"Blueprint" in response.data or b"blueprint" in response.data


def test_item_blueprints_create_get_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get("/db/item-blueprints/create")
    assert response.status_code == 200
    assert b"Blueprint" in response.data or b"blueprint" in response.data


def test_item_blueprints_create_post_authorized(
    test_client, rules_team_user, item_type, mod_obj, db
):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    unique_name = f"Blueprint {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("item_type_id", str(item_type.id)),
            ("base_cost", "150"),
            ("mods_applied[]", str(mod_obj.id)),
        ]
    )
    response = test_client.post(
        "/db/item-blueprints/create",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Item blueprint created successfully" in response.data
    blueprint = ItemBlueprint.query.filter_by(name=unique_name).first()
    assert blueprint is not None
    assert blueprint.base_cost == 150


def test_item_blueprints_create_missing_fields(test_client, rules_team_user, item_type, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    post_data = MultiDict(
        [
            ("name", ""),
            ("item_type_id", ""),
            ("base_cost", ""),
        ]
    )
    response = test_client.post(
        "/db/item-blueprints/create",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_item_blueprints_create_invalid_type(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    unique_name = f"Blueprint {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("item_type_id", "99999"),
            ("base_cost", "100"),
        ]
    )
    response = test_client.post(
        "/db/item-blueprints/create",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Invalid item type" in response.data


def test_item_blueprints_create_unauthorized(test_client, db):
    response = test_client.get("/db/item-blueprints/create")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_item_blueprints_edit_get_authorized(test_client, rules_team_user, item_blueprint_obj, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get(f"/db/item-blueprints/{item_blueprint_obj.id}/edit")
    assert response.status_code == 200
    assert bytes(item_blueprint_obj.name, "utf-8") in response.data


def test_item_blueprints_edit_post_authorized(
    test_client, rules_team_user, item_blueprint_obj, item_type, mod_obj, db
):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    new_name = f"Updated Blueprint {uuid.uuid4()}"
    new_blueprint_id = item_blueprint_obj.blueprint_id + 1000  # ensure uniqueness
    post_data = MultiDict(
        [
            ("name", new_name),
            ("item_type_id", str(item_type.id)),
            ("blueprint_id", new_blueprint_id),
            ("base_cost", "200"),
            ("mods_applied[]", str(mod_obj.id)),
        ]
    )
    response = test_client.post(
        f"/db/item-blueprints/{item_blueprint_obj.id}/edit",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    if b"Item blueprint updated successfully" not in response.data:
        print(response.data.decode())
    assert response.status_code == 200
    assert b"Item blueprint updated successfully" in response.data
    db.session.expire_all()
    updated = db.session.get(ItemBlueprint, item_blueprint_obj.id)
    assert updated.name == new_name
    assert updated.base_cost == 200
    assert updated.blueprint_id == new_blueprint_id


def test_item_blueprints_edit_missing_fields(
    test_client, rules_team_user, item_blueprint_obj, item_type, db
):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    post_data = MultiDict(
        [
            ("name", ""),
            ("item_type_id", ""),
            ("blueprint_id", ""),
            ("base_cost", ""),
        ]
    )
    response = test_client.post(
        f"/db/item-blueprints/{item_blueprint_obj.id}/edit",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_item_blueprints_edit_unauthorized(test_client, item_blueprint_obj, db):
    response = test_client.get(f"/db/item-blueprints/{item_blueprint_obj.id}/edit")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_item_blueprints_edit_not_found(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.get("/db/item-blueprints/99999/edit")
    assert response.status_code == 404


def test_item_blueprints_delete_authorized(test_client, rules_team_user, item_blueprint_obj, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.post(
        f"/db/item-blueprints/{item_blueprint_obj.id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Item blueprint deleted successfully" in response.data
    deleted = db.session.get(ItemBlueprint, item_blueprint_obj.id)
    assert deleted is None


def test_item_blueprints_delete_unauthorized(test_client, item_blueprint_obj, db):
    response = test_client.post(f"/db/item-blueprints/{item_blueprint_obj.id}/delete")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_item_blueprints_delete_not_found(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    response = test_client.post("/db/item-blueprints/99999/delete", follow_redirects=True)
    assert response.status_code == 404
