import pytest

from models.database.global_settings import GlobalSettings
from models.extensions import db


class TestGlobalSettingsRoutes:
    def test_list_global_settings_authenticated(self, test_client, authenticated_user):
        """Test that authenticated users can view global settings."""
        response = test_client.get("/db/global-settings/")
        assert response.status_code == 200
        assert b"Global Settings" in response.data

    def test_list_global_settings_unauthenticated(self, test_client):
        """Test that unauthenticated users are redirected to login."""
        response = test_client.get("/db/global-settings/")
        assert response.status_code == 302  # Redirect to login

    def test_edit_global_settings_rules_team_required(self, test_client, authenticated_user):
        """Test that non-rules-team users cannot access edit page."""
        response = test_client.get("/db/global-settings/edit")
        assert response.status_code == 403  # Forbidden

    def test_edit_global_settings_rules_team_allowed(self, test_client, rules_team_user):
        """Test that rules team users can access edit page."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = rules_team_user.id
            sess["_fresh"] = True

        response = test_client.get("/db/global-settings/edit")
        assert response.status_code == 200
        assert b"Edit Global Settings" in response.data

    def test_edit_global_settings_post_success(self, test_client, rules_team_user):
        """Test successful global settings update."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = rules_team_user.id
            sess["_fresh"] = True

        data = {"character_income_ec": "50", "group_income_contribution": "25"}
        response = test_client.post("/db/global-settings/edit", data=data)
        assert response.status_code == 302  # Redirect after success

        # Verify the settings were updated
        settings = GlobalSettings.query.first()
        assert settings is not None
        assert settings.character_income_ec == 50
        assert settings.group_income_contribution == 25

    def test_edit_global_settings_invalid_input(self, test_client, rules_team_user):
        """Test that invalid input is handled properly."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = rules_team_user.id
            sess["_fresh"] = True

        data = {"character_income_ec": "invalid", "group_income_contribution": "also_invalid"}
        response = test_client.post("/db/global-settings/edit", data=data)
        assert response.status_code == 302  # Redirect after error

        # Verify settings were not changed (should use defaults)
        settings = GlobalSettings.query.first()
        if settings:
            # If settings exist, they should have default values
            assert settings.character_income_ec == 30  # Default value
            assert settings.group_income_contribution == 30  # Default value

    def test_edit_global_settings_creates_default(self, test_client, rules_team_user):
        """Test that default settings are created if none exist."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = rules_team_user.id
            sess["_fresh"] = True

        # Delete any existing settings
        GlobalSettings.query.delete()
        db.session.commit()

        data = {"character_income_ec": "100", "group_income_contribution": "75"}
        response = test_client.post("/db/global-settings/edit", data=data)
        assert response.status_code == 302  # Redirect after success

        # Verify new settings were created
        settings = GlobalSettings.query.first()
        assert settings is not None
        assert settings.character_income_ec == 100
        assert settings.group_income_contribution == 75

    def test_edit_global_settings_page_creates_default(self, test_client, rules_team_user):
        """Test that edit page creates default settings if none exist."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = rules_team_user.id
            sess["_fresh"] = True

        # Delete any existing settings
        GlobalSettings.query.delete()
        db.session.commit()

        response = test_client.get("/db/global-settings/edit")
        assert response.status_code == 200

        # Verify default settings were created
        settings = GlobalSettings.query.first()
        assert settings is not None
        assert settings.character_income_ec == 30  # Default value
        assert settings.group_income_contribution == 30  # Default value
