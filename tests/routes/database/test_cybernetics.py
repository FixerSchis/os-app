import uuid

from werkzeug.datastructures import MultiDict

from models.database.cybernetic import Cybernetic
from models.enums import ScienceType


def test_cybernetics_list_unauthorized(test_client):
    response = test_client.get("/db/cybernetics/")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_cybernetics_list_authorized(test_client, rules_team_user):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/cybernetics/")
    assert response.status_code == 200
    assert b"Cybernetic" in response.data or b"cybernetic" in response.data


def test_cybernetics_create_get_authorized(test_client, rules_team_user):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/cybernetics/new")
    assert response.status_code == 200
    assert b"Cybernetic" in response.data or b"cybernetic" in response.data


def test_cybernetics_create_post_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    unique_name = f"Cybernetic {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("neural_shock_value", "7"),
            ("wiki_slug", f"cybernetic-{uuid.uuid4()}"),
            ("adds_engineering_mods", "1"),
            ("adds_engineering_downtime", "2"),
            ("adds_science_downtime", "3"),
            ("science_type", ScienceType.GENERIC.value),
        ]
    )
    response = test_client.post(
        "/db/cybernetics/new",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Cybernetic created" in response.data
    cyber = Cybernetic.query.filter_by(name=unique_name).first()
    assert cyber is not None
    assert cyber.neural_shock_value == 7


def test_cybernetics_edit_get_authorized(test_client, rules_team_user, cybernetic):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get(f"/db/cybernetics/{cybernetic.id}/edit")
    assert response.status_code == 200
    assert bytes(cybernetic.name, "utf-8") in response.data


def test_cybernetics_edit_post_authorized(test_client, rules_team_user, cybernetic, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    new_name = f"Updated Cybernetic {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", new_name),
            ("neural_shock_value", "9"),
            ("wiki_slug", f"cybernetic-{uuid.uuid4()}"),
            ("adds_engineering_mods", "2"),
            ("adds_engineering_downtime", "3"),
            ("adds_science_downtime", "4"),
            ("science_type", ScienceType.GENERIC.value),
        ]
    )
    response = test_client.post(
        f"/db/cybernetics/{cybernetic.id}/edit",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Cybernetic updated" in response.data
    db.session.expire_all()
    updated = db.session.get(Cybernetic, cybernetic.id)
    assert updated.name == new_name
    assert updated.neural_shock_value == 9


def test_cybernetics_delete_authorized(test_client, rules_team_user, cybernetic, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(f"/db/cybernetics/{cybernetic.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    db.session.expire_all()
    deleted = db.session.get(Cybernetic, cybernetic.id)
    assert deleted is None
