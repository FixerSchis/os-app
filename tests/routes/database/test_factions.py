import uuid

from werkzeug.datastructures import MultiDict

from models.database.faction import Faction


def test_factions_list_unauthorized(test_client, db):
    response = test_client.get("/db/factions/")
    assert response.status_code == 200
    assert b"Faction" in response.data or b"faction" in response.data
    assert b"New Faction" not in response.data


def test_factions_list_authorized(test_client, rules_team_user, db):
    with test_client as c:
        c.post(
            "/auth/login",
            data={
                "email": rules_team_user.email,
                "password": "password123",
            },
            follow_redirects=True,
        )
        response = c.get("/db/factions/")
        assert response.status_code == 200
        assert b"Faction" in response.data or b"faction" in response.data
        # Optionally, check for edit controls


def login_rules_team_user(test_client, rules_team_user):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True


def test_factions_create_get_authorized(test_client, rules_team_user, db):
    login_rules_team_user(test_client, rules_team_user)
    response = test_client.get("/db/factions/new")
    assert response.status_code == 200
    assert b"Faction" in response.data or b"faction" in response.data


def test_factions_create_post_authorized(test_client, rules_team_user, db):
    login_rules_team_user(test_client, rules_team_user)
    unique_name = f"Faction {uuid.uuid4()}"
    unique_slug = f"faction-{uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("wiki_page", unique_slug),
            ("allow_player_characters", "on"),
        ]
    )
    response = test_client.post(
        "/db/factions/new",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Faction created successfully" in response.data
    faction = Faction.query.filter_by(name=unique_name).first()
    assert faction is not None
    assert faction.allow_player_characters is True


def test_factions_create_missing_fields(test_client, rules_team_user, db):
    login_rules_team_user(test_client, rules_team_user)
    post_data = MultiDict(
        [
            ("name", ""),
            ("wiki_page", ""),
        ]
    )
    response = test_client.post(
        "/db/factions/new",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_factions_create_unauthorized(test_client, db):
    response = test_client.get("/db/factions/new")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_factions_edit_get_authorized(test_client, rules_team_user, faction, db):
    login_rules_team_user(test_client, rules_team_user)
    response = test_client.get(f"/db/factions/{faction.id}/edit")
    assert response.status_code == 200
    assert bytes(faction.name, "utf-8") in response.data


def test_factions_edit_post_authorized(test_client, rules_team_user, faction, db):
    login_rules_team_user(test_client, rules_team_user)
    new_name = f"Updated Faction {uuid.uuid4()}"
    new_slug = f"updated-faction-{uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", new_name),
            ("wiki_page", new_slug),
            ("allow_player_characters", "on"),
        ]
    )
    response = test_client.post(
        f"/db/factions/{faction.id}/edit",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Faction updated successfully" in response.data
    db.session.expire_all()
    updated = Faction.query.get(faction.id)
    assert updated.name == new_name
    assert updated.wiki_slug == new_slug
    assert updated.allow_player_characters is True


def test_factions_edit_missing_fields(test_client, rules_team_user, faction, db):
    login_rules_team_user(test_client, rules_team_user)
    post_data = MultiDict(
        [
            ("name", ""),
            ("wiki_page", ""),
        ]
    )
    response = test_client.post(
        f"/db/factions/{faction.id}/edit",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_factions_edit_unauthorized(test_client, faction, db):
    response = test_client.get(f"/db/factions/{faction.id}/edit")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_factions_edit_not_found(test_client, rules_team_user, db):
    login_rules_team_user(test_client, rules_team_user)
    response = test_client.get("/db/factions/99999/edit")
    assert response.status_code == 404
