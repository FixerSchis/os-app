import uuid

from werkzeug.datastructures import MultiDict

from models.database.medicaments import Medicament
from models.wiki import WikiPage


def test_medicaments_list_unauthorized(test_client, db):
    response = test_client.get("/db/medicaments/")
    assert response.status_code == 200
    assert b"Medicament" in response.data or b"medicament" in response.data
    assert b"New Medicament" not in response.data


def test_medicaments_list_authorized(test_client, verified_login, db):
    response = test_client.get("/db/medicaments/")
    assert response.status_code == 200
    assert b"Medicament" in response.data or b"medicament" in response.data
    assert b"Create Medicament" in response.data


def test_medicaments_create_get_authorized(test_client, verified_login, db):
    response = test_client.get("/db/medicaments/new")
    assert response.status_code == 200
    assert b"Medicament" in response.data or b"medicament" in response.data


def test_medicaments_create_post_authorized(test_client, verified_login, db):
    unique_name = f"Medicament {uuid.uuid4()}"
    unique_slug = f"medicament-{uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("wiki_slug", unique_slug),
        ]
    )
    response = test_client.post(
        "/db/medicaments/new",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Medicament created successfully" in response.data
    medicament = Medicament.query.filter_by(name=unique_name).first()
    assert medicament is not None
    wiki_page = WikiPage.query.filter_by(slug=unique_slug).first()
    assert wiki_page is not None
    assert wiki_page.title.startswith(unique_name)


def test_medicaments_create_missing_fields(test_client, verified_login, db):
    post_data = MultiDict(
        [
            ("name", ""),
            ("wiki_slug", ""),
        ]
    )
    response = test_client.post(
        "/db/medicaments/new",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Name and wiki page are required" in response.data


def test_medicaments_create_unauthorized(test_client, db):
    response = test_client.get("/db/medicaments/new")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_medicaments_edit_get_authorized(test_client, verified_login, medicament, db):
    response = test_client.get(f"/db/medicaments/{medicament.id}/edit")
    assert response.status_code == 200
    assert bytes(medicament.name, "utf-8") in response.data


def test_medicaments_edit_post_authorized(test_client, verified_login, medicament, db):
    new_name = f"Updated Medicament {uuid.uuid4()}"
    new_slug = f"updated-medicament-{uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", new_name),
            ("wiki_slug", new_slug),
        ]
    )
    response = test_client.post(
        f"/db/medicaments/{medicament.id}/edit",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Medicament updated successfully" in response.data
    db.session.expire_all()
    updated = db.session.get(Medicament, medicament.id)
    assert updated.name == new_name
    assert updated.wiki_slug == new_slug
    wiki_page = WikiPage.query.filter_by(slug=new_slug).first()
    assert wiki_page is not None
    assert wiki_page.title.startswith(new_name)


def test_medicaments_edit_missing_fields(test_client, verified_login, medicament, db):
    post_data = MultiDict(
        [
            ("name", ""),
            ("wiki_slug", ""),
        ]
    )
    response = test_client.post(
        f"/db/medicaments/{medicament.id}/edit",
        data=post_data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Name and wiki page are required" in response.data


def test_medicaments_edit_unauthorized(test_client, medicament, db):
    response = test_client.get(f"/db/medicaments/{medicament.id}/edit")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_medicaments_edit_not_found(test_client, verified_login, db):
    response = test_client.get("/db/medicaments/99999/edit")
    assert response.status_code == 404
