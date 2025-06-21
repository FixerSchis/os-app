from flask import url_for


def test_unauthenticated_access_redirects_to_login(app, test_client, db):
    """Test that accessing a protected page redirects to login for an unauthenticated
    user."""
    with app.test_request_context():
        response = test_client.get(url_for("protected_route"))
        assert response.status_code == 302
        assert response.location.startswith(url_for("auth.login", _external=False))


def test_403_for_authenticated_user_without_role(app, test_client, authenticated_user, db):
    """Test that a 403 is returned for an authenticated user without the correct
    role."""
    with app.test_request_context():
        response = test_client.get(url_for("admin_only_route"))
        assert response.status_code == 403
        assert b"Access Denied" in response.data


def test_admin_access_for_admin_user(app, test_client, admin_user, db):
    """Test that an admin user can access an admin-only route."""
    with app.test_request_context():
        response = test_client.get(url_for("admin_only_route"))
        assert response.status_code == 200
        assert b"Admin content" in response.data
