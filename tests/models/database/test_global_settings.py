import pytest

from models.database.global_settings import GlobalSettings


class TestGlobalSettingsModel:
    def test_create_global_settings(self, db):
        settings = GlobalSettings(character_income_ec=50, group_income_contribution=25)
        db.session.add(settings)
        db.session.commit()
        assert settings.id is not None
        assert settings.character_income_ec == 50
        assert settings.group_income_contribution == 25

    def test_global_settings_defaults(self, db):
        """Test that GlobalSettings uses default values when not specified."""
        settings = GlobalSettings()
        db.session.add(settings)
        db.session.commit()
        assert settings.character_income_ec == 30  # Default value
        assert settings.group_income_contribution == 30  # Default value

    def test_global_settings_update(self, db):
        """Test updating global settings."""
        settings = GlobalSettings(character_income_ec=40, group_income_contribution=20)
        db.session.add(settings)
        db.session.commit()

        # Update the settings
        settings.character_income_ec = 60
        settings.group_income_contribution = 35
        db.session.commit()

        # Verify the updates
        db.session.refresh(settings)
        assert settings.character_income_ec == 60
        assert settings.group_income_contribution == 35

    def test_global_settings_repr(self, db):
        """Test the string representation of GlobalSettings."""
        settings = GlobalSettings(character_income_ec=45, group_income_contribution=30)
        db.session.add(settings)
        db.session.commit()

        repr_str = repr(settings)
        assert "GlobalSettings" in repr_str
        assert "character_income_ec=45" in repr_str
        assert "group_contribution=30" in repr_str
