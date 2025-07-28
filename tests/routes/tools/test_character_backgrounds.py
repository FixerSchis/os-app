import pytest
from flask import url_for

from models.enums import CharacterStatus, Role
from models.tools.character import Character, CharacterBackground
from models.tools.user import User


class TestCharacterBackgroundsRoutes:
    """Test character backgrounds routes"""

    def test_list_backgrounds_requires_user_admin(self, test_client, regular_user, db_session):
        """Test that list backgrounds requires user_admin role"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/character-backgrounds/")
        assert response.status_code == 403

    def test_list_backgrounds_user_admin_access(self, test_client, user_admin, db_session):
        """Test that user_admin can access list backgrounds"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get("/tools/character-backgrounds/")
        assert response.status_code == 200
        assert b"Character Backgrounds" in response.data

    def test_list_backgrounds_empty(self, test_client, user_admin, db_session):
        """Test list backgrounds when no backgrounds need review"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get("/tools/character-backgrounds/")
        assert response.status_code == 200
        assert b"No character backgrounds currently need review" in response.data

    def test_list_backgrounds_with_backgrounds(self, test_client, user_admin, db_session):
        """Test list backgrounds with backgrounds needing review"""
        # Create a character and background
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=True,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get("/tools/character-backgrounds/")
        assert response.status_code == 200
        assert b"Test Character" in response.data
        assert b"Test background" in response.data
        assert b"Test goals" in response.data
        assert b"Test concept" in response.data

    def test_review_background_requires_user_admin(self, test_client, regular_user, db_session):
        """Test that review background requires user_admin role"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/character-backgrounds/1/review")
        assert response.status_code == 403

    def test_review_background_not_found(self, test_client, user_admin, db_session):
        """Test review background with non-existent background"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get("/tools/character-backgrounds/999/review")
        assert response.status_code == 404

    def test_review_background_already_reviewed(self, test_client, user_admin, db_session):
        """Test review background that has already been reviewed"""
        # Create a character and background that's already reviewed
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=False,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get(f"/tools/character-backgrounds/{background.id}/review")
        assert response.status_code == 302  # Redirect
        # Should redirect to list with flash message

    def test_review_background_get(self, test_client, user_admin, db_session):
        """Test review background GET request"""
        # Create a character and background
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=True,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get(f"/tools/character-backgrounds/{background.id}/review")
        assert response.status_code == 200
        assert b"Test Character" in response.data
        assert b"Test background" in response.data
        assert b"Test goals" in response.data
        assert b"Test concept" in response.data

    def test_review_background_post_not_marked_done(self, test_client, user_admin, db_session):
        """Test review background POST without marking as done"""
        # Create a character and background
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=True,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        data = {
            "character_name": "Updated Character",
            "background": "Updated background",
            "goals": "Updated goals",
            "concept": "Updated concept",
        }

        response = test_client.post(
            f"/tools/character-backgrounds/{background.id}/review", data=data
        )
        assert response.status_code == 302  # Redirect

        # Check that the background was updated but still needs review
        db_session.refresh(background)
        assert background.background == "Updated background"
        assert background.goals == "Updated goals"
        assert background.concept == "Updated concept"
        assert background.needs_review is True

        # Check that character was also updated
        db_session.refresh(character)
        assert character.name == "Updated Character"
        assert character.background == "Updated background"
        assert character.goals == "Updated goals"
        assert character.concept == "Updated concept"

    def test_review_background_post_marked_done(self, test_client, user_admin, db_session):
        """Test review background POST with marking as done"""
        # Create a character and background
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=True,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        data = {
            "character_name": "Updated Character",
            "background": "Updated background",
            "goals": "Updated goals",
            "concept": "Updated concept",
            "mark_done": "on",
        }

        response = test_client.post(
            f"/tools/character-backgrounds/{background.id}/review", data=data
        )
        assert response.status_code == 302  # Redirect

        # Check that the background was updated and marked as reviewed
        db_session.refresh(background)
        assert background.background == "Updated background"
        assert background.goals == "Updated goals"
        assert background.concept == "Updated concept"
        assert background.needs_review is False
        assert background.reviewed_at is not None
        assert background.reviewed_by_user_id == user_admin.id

        # Check that character was also updated
        db_session.refresh(character)
        assert character.name == "Updated Character"
        assert character.background == "Updated background"
        assert character.goals == "Updated goals"
        assert character.concept == "Updated concept"

    def test_review_background_post_already_reviewed(self, test_client, user_admin, db_session):
        """Test review background POST on already reviewed background"""
        # Create a character and background that's already reviewed
        character = Character(
            user_id=user_admin.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=False,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        data = {
            "character_name": "Updated Character",
            "background": "Updated background",
            "goals": "Updated goals",
            "concept": "Updated concept",
            "mark_done": "on",
        }

        response = test_client.post(
            f"/tools/character-backgrounds/{background.id}/review", data=data
        )
        assert response.status_code == 302  # Redirect
        # Should redirect to list with flash message about already reviewed
