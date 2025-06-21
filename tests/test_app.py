from unittest import mock

from flask import url_for


def test_index_redirect(app, test_client, db, wiki_index_page):
    """Test that the index page redirects to the wiki."""
    with app.test_request_context():
        response = test_client.get("/")
        assert response.status_code == 302
        assert response.location == url_for("wiki.wiki_view", slug="index", _external=False)


def test_500_error_handler(app, test_client, db, wiki_index_page):
    """Test the 500 error handler."""
    original_testing_config = app.config["TESTING"]
    app.config["TESTING"] = False

    with app.test_request_context(), mock.patch(
        "routes.wiki.render_template", side_effect=Exception("mocked error")
    ):
        response = test_client.get(url_for("wiki.wiki_view", slug="index"))
        assert response.status_code == 500
        assert b"Server Error" in response.data

    app.config["TESTING"] = original_testing_config


def test_has_enter_downtime_packs_context_processor_no_packs(
    app, test_client, authenticated_user, db
):
    """Test the has_enter_downtime_packs context processor when there are no packs."""
    with app.test_request_context():
        response = test_client.get(url_for("test_page"))
        assert b'data-has-downtime-packs="False"' in response.data


def test_has_enter_downtime_packs_context_processor_with_pack(
    app, test_client, authenticated_user, downtime_pack, db
):
    """Test the has_enter_downtime_packs context processor when a pack exists."""
    with app.test_request_context():
        response = test_client.get(url_for("test_page"))
        assert b'data-has-downtime-packs="True"' in response.data


def test_has_research_projects_context_processor_no_projects(
    app, test_client, authenticated_user, db
):
    """Test the has_research_projects context processor when there are no projects."""
    with app.test_request_context():
        response = test_client.get(url_for("test_page"))
        assert b'data-has-research-projects="False"' in response.data


def test_has_research_projects_context_processor_with_project(
    app, test_client, authenticated_user, character_research, db
):
    """Test the has_research_projects context processor when a project exists."""
    with app.test_request_context():
        response = test_client.get(url_for("test_page"))
        assert b'data-has-research-projects="True"' in response.data


def test_chrome_devtools_json(app, test_client, db):
    """Test the Chrome DevTools JSON route."""
    with app.test_request_context():
        response = test_client.get("/.well-known/appspecific/com.chrome.devtools.json")
        assert response.status_code == 204
