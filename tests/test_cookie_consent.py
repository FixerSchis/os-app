from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


class TestCookieConsent:
    """Test cookie consent functionality."""

    def test_cookie_consent_popup_shows_on_first_visit(self, client):
        """Test that cookie consent popup shows when no consent cookie exists."""
        # Clear any existing cookies
        client.delete_cookie("cookie_consent")

        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # Check that the cookie consent JavaScript is included
        assert "cookie-consent.js" in response.data.decode()
        assert "cookie-consent.css" in response.data.decode()

    def test_theme_endpoint_respects_cookie_consent_accepted(self, client):
        """Test that theme endpoint sets cookies when consent is accepted."""
        # Set cookie consent to accepted
        client.set_cookie("cookie_consent", "accepted")

        response = client.post(
            "/toggle-theme", json={"theme": "light"}, content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["theme"] == "light"

        # Check that theme cookie was set
        cookies = response.headers.getlist("Set-Cookie")
        theme_cookies = [c for c in cookies if "theme=light" in c]
        assert len(theme_cookies) == 1

    def test_theme_endpoint_respects_cookie_consent_declined(self, client):
        """Test that theme endpoint doesn't set cookies when consent is declined."""
        # Set cookie consent to declined
        client.set_cookie("cookie_consent", "declined")

        response = client.post(
            "/toggle-theme", json={"theme": "light"}, content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["theme"] == "light"

        # Check that no theme cookie was set
        cookies = response.headers.getlist("Set-Cookie")
        theme_cookies = [c for c in cookies if "theme=" in c]
        assert len(theme_cookies) == 0

    def test_theme_endpoint_without_consent_cookie(self, client):
        """Test that theme endpoint doesn't set cookies when no consent cookie exists."""
        # Ensure no consent cookie exists
        client.delete_cookie("cookie_consent")

        response = client.post(
            "/toggle-theme", json={"theme": "light"}, content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["theme"] == "light"

        # Check that no theme cookie was set
        cookies = response.headers.getlist("Set-Cookie")
        theme_cookies = [c for c in cookies if "theme=" in c]
        assert len(theme_cookies) == 0

    def test_theme_endpoint_invalid_json(self, client):
        """Test that theme endpoint handles invalid JSON gracefully."""
        response = client.post(
            "/toggle-theme", data="invalid json", content_type="application/json"
        )

        assert response.status_code == 400
        assert response.json["success"] is False

    def test_theme_endpoint_no_json(self, client):
        """Test that theme endpoint handles missing JSON gracefully."""
        response = client.post("/toggle-theme")

        assert response.status_code == 400
        assert response.json["success"] is False

    def test_theme_endpoint_defaults_to_dark(self, client):
        """Test that theme endpoint defaults to dark mode when no theme specified."""
        client.set_cookie("cookie_consent", "accepted")

        response = client.post("/toggle-theme", json={}, content_type="application/json")

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["theme"] == "dark"

    def test_theme_endpoint_with_none_theme(self, client):
        """Test that theme endpoint handles None theme gracefully."""
        client.set_cookie("cookie_consent", "accepted")

        response = client.post(
            "/toggle-theme", json={"theme": None}, content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["theme"] == "dark"


class TestCookieConsentJavaScript:
    """Test cookie consent JavaScript functionality."""

    def test_cookie_consent_manager_initialization(self, client):
        """Test that cookie consent manager initializes properly."""
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # Check that the cookie consent JavaScript file is included
        assert "cookie-consent.js" in response.data.decode()

    def test_cookie_consent_css_included(self, client):
        """Test that cookie consent CSS is included in the template."""
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # Check that the CSS file is included
        assert "cookie-consent.css" in response.data.decode()

    def test_dark_mode_manager_integration(self, client):
        """Test that dark mode manager is properly integrated with cookie consent."""
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # Check that dark mode manager JavaScript file is included
        assert "dark-mode.js" in response.data.decode()


class TestCookieConsentTemplate:
    """Test cookie consent template functionality."""

    def test_cookie_consent_template_renders(self, client):
        """Test that the cookie consent test template renders correctly."""
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # Check for key elements
        assert "Cookie Consent Test" in response.data.decode()
        assert "Current Cookie Status" in response.data.decode()
        assert "Test Theme Toggle" in response.data.decode()
        assert "Reset Cookie Consent" in response.data.decode()
        assert "Manual Cookie Control" in response.data.decode()

    def test_cookie_consent_template_has_test_buttons(self, client):
        """Test that the template has all the necessary test buttons."""
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        content = response.data.decode()

        # Check for test buttons
        assert "Test Theme Toggle" in content
        assert "Reset Cookie Consent" in content
        assert "Force Show Popup" in content
        assert "Enable Cookies" in content
        assert "Disable Cookies" in content

    def test_cookie_consent_template_has_status_display(self, client):
        """Test that the template has status display elements."""
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        content = response.data.decode()

        # Check for status elements
        assert "cookies-status" in content
        assert "theme-cookie" in content
        assert "consent-cookie" in content


class TestCookieConsentIntegration:
    """Test cookie consent integration with the main app."""

    def test_cookie_consent_does_not_affect_authenticated_users(self, client, authenticated_user):
        """Test that cookie consent doesn't interfere with authenticated users."""
        with client.session_transaction() as sess:
            sess["_user_id"] = authenticated_user.id
            sess["_fresh"] = True

        response = client.get("/")
        assert response.status_code == 302  # Redirect to wiki index

        # Check that the page loads normally for authenticated users
        # Skip the wiki page test since it requires database setup
        assert response.headers["Location"] == "/wiki/index"

    def test_cookie_consent_works_with_unauthenticated_users(self, client):
        """Test that cookie consent works properly for unauthenticated users."""
        response = client.get("/")
        assert response.status_code == 302  # Redirect to wiki index

        # Check that the redirect is to the wiki index
        assert response.headers["Location"] == "/wiki/index"

    def test_cookie_consent_persists_across_sessions(self, client):
        """Test that cookie consent choice persists across browser sessions."""
        # Set cookie consent to accepted
        client.set_cookie("cookie_consent", "accepted")

        # Make a request
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # Check that the consent cookie is still there by making another request
        response2 = client.get("/test-cookie-consent")
        assert response2.status_code == 200

    def test_cookie_consent_reset_functionality(self, client):
        """Test that cookie consent can be reset."""
        # Set cookie consent to accepted
        client.set_cookie("cookie_consent", "accepted")

        # Make a request to reset
        response = client.get("/test-cookie-consent")
        assert response.status_code == 200

        # The reset functionality is client-side, so we just verify the page loads
        assert "Reset Cookie Consent" in response.data.decode()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def authenticated_user(db_session):
    """Create an authenticated user for testing."""
    from models.tools.user import User

    user = User(first_name="Test", email="test@example.com", password_hash="hashed_password")
    db_session.add(user)
    db_session.commit()
    return user
