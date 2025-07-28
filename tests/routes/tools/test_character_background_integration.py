import pytest
from flask import url_for

from models.enums import CharacterStatus, Role
from models.tools.character import Character, CharacterBackground
from models.tools.user import User


class TestCharacterBackgroundIntegration:
    """Test character background integration with character editing"""

    def test_character_edit_with_background_fields(
        self, test_client, regular_user, faction, species, db_session
    ):
        """Test that character edit form includes background fields"""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get(f"/characters/{character.id}/edit")
        assert response.status_code == 200
        assert b"Character Background" in response.data
        assert b"Background" in response.data
        assert b"Goals" in response.data
        assert b"Concept" in response.data

    def test_character_edit_save_background_fields(
        self, test_client, regular_user, faction, species, db_session
    ):
        """Test saving character with background fields"""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Get the edit form to get required fields
        response = test_client.get(f"/characters/{character.id}/edit")
        assert response.status_code == 200

        # Submit the form with background data
        data = {
            "name": "Updated Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "Test background content",
            "goals": "Test goals content",
            "concept": "Test concept content",
        }

        response = test_client.post(f"/characters/{character.id}/edit", data=data)
        assert response.status_code == 302  # Redirect

        # Check that character was updated
        db_session.refresh(character)
        assert character.name == "Updated Character"
        assert character.background == "Test background content"
        assert character.goals == "Test goals content"
        assert character.concept == "Test concept content"

        # Check that background was created and flagged for review
        background = CharacterBackground.query.filter_by(character_id=character.id).first()
        assert background is not None
        assert background.background == "Test background content"
        assert background.goals == "Test goals content"
        assert background.concept == "Test concept content"
        assert background.needs_review is True

    def test_character_edit_background_review_for_admin(
        self, test_client, user_admin, faction, species, db_session
    ):
        """Test that user_admin editing background flags for review"""
        # Create a character for the admin
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Submit the form with background data
        data = {
            "name": "Updated Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "Admin background content",
            "goals": "Admin goals content",
            "concept": "Admin concept content",
        }

        response = test_client.post(f"/characters/{character.id}/edit", data=data)
        assert response.status_code == 302  # Redirect

        # Check that character was updated
        db_session.refresh(character)
        assert character.name == "Updated Character"
        assert character.background == "Admin background content"
        assert character.goals == "Admin goals content"
        assert character.concept == "Admin concept content"

        # Check that background review was created for admin
        background = CharacterBackground.query.filter_by(character_id=character.id).first()
        assert background is not None
        assert background.background == "Admin background content"
        assert background.goals == "Admin goals content"
        assert background.concept == "Admin concept content"
        assert background.needs_review is True

    def test_character_edit_background_audit_logging(
        self, test_client, regular_user, faction, species, db_session
    ):
        """Test that background changes are logged in audit log"""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Submit the form with background data
        data = {
            "name": "Test Character",  # Keep same name
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "Test background content",
            "goals": "Test goals content",
            "concept": "Test concept content",
        }

        response = test_client.post(f"/characters/{character.id}/edit", data=data)
        assert response.status_code == 302  # Redirect

        # Check that audit log was created for background changes
        from models.tools.character import CharacterAuditLog

        audit_logs = CharacterAuditLog.query.filter_by(character_id=character.id).all()
        background_changes = [
            log
            for log in audit_logs
            if "Background updated" in log.changes
            or "Goals updated" in log.changes
            or "Concept updated" in log.changes
        ]
        assert len(background_changes) > 0

    def test_character_edit_background_fields_persistence(
        self, test_client, regular_user, db_session
    ):
        """Test that background fields persist after editing"""
        # Create a character with background data
        character = Character(
            user_id=regular_user.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
            background="Original background",
            goals="Original goals",
            concept="Original concept",
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Get the edit form
        response = test_client.get(f"/characters/{character.id}/edit")
        assert response.status_code == 200
        assert b"Original background" in response.data
        assert b"Original goals" in response.data
        assert b"Original concept" in response.data

    def test_character_edit_background_fields_optional(
        self, test_client, regular_user, faction, species, db_session
    ):
        """Test that background fields are optional"""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Submit the form without background data
        data = {
            "name": "Updated Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "",
            "goals": "",
            "concept": "",
        }

        response = test_client.post(f"/characters/{character.id}/edit", data=data)
        assert response.status_code == 302  # Redirect

        # Check that character was updated with empty background fields
        db_session.refresh(character)
        assert character.name == "Updated Character"
        assert character.background == ""
        assert character.goals == ""
        assert character.concept == ""

    def test_character_edit_background_review_flagging(
        self, test_client, regular_user, faction, species, db_session
    ):
        """Test that background changes flag for review when not user_admin"""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Submit the form with background data
        data = {
            "name": "Test Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "New background content",
            "goals": "New goals content",
            "concept": "New concept content",
        }

        response = test_client.post(f"/characters/{character.id}/edit", data=data)
        assert response.status_code == 302  # Redirect

        # Check that background was created and flagged for review
        background = CharacterBackground.query.filter_by(character_id=character.id).first()
        assert background is not None
        assert background.needs_review is True
        assert background.background == "New background content"
        assert background.goals == "New goals content"
        assert background.concept == "New concept content"
