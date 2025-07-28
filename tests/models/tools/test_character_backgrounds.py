from datetime import datetime

import pytest

from models.enums import CharacterStatus
from models.tools.character import Character, CharacterBackground
from models.tools.user import User


class TestCharacterBackground:
    """Test the CharacterBackground model"""

    def test_character_background_creation(self, db_session):
        """Test creating a character background"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
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

        assert background.id is not None
        assert background.character_id == character.id
        assert background.background == "Test background"
        assert background.goals == "Test goals"
        assert background.concept == "Test concept"
        assert background.needs_review is True
        assert background.reviewed_at is None
        assert background.reviewed_by_user_id is None

    def test_get_or_create_for_character_new(self, db_session):
        """Test get_or_create_for_character when no background exists"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground.get_or_create_for_character(character.id)
        assert background.character_id == character.id
        # The object is created but not saved to database, so it won't have an ID yet
        assert background.id is None
        # Default values aren't applied until saved to database
        assert background.needs_review is None
        assert background.background is None
        assert background.goals is None
        assert background.concept is None

    def test_get_or_create_for_character_existing(self, db_session):
        """Test get_or_create_for_character when background exists"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        # Create initial background
        background1 = CharacterBackground(
            character_id=character.id,
            background="Original background",
            goals="Original goals",
            concept="Original concept",
            needs_review=True,
        )
        db_session.add(background1)
        db_session.commit()

        # Get the same background
        background2 = CharacterBackground.get_or_create_for_character(character.id)
        assert background2.id == background1.id
        assert background2.background == "Original background"
        assert background2.goals == "Original goals"
        assert background2.concept == "Original concept"

    def test_mark_for_review(self, db_session):
        """Test marking a background for review"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
        )
        db_session.add(character)
        db_session.commit()

        background = CharacterBackground(
            character_id=character.id,
            background="Test background",
            goals="Test goals",
            concept="Test concept",
            needs_review=False,
            reviewed_at=datetime.utcnow(),
            reviewed_by_user_id=user.id,
        )
        db_session.add(background)
        db_session.commit()

        background.mark_for_review()
        db_session.commit()

        assert background.needs_review is True
        assert background.reviewed_at is None
        assert background.reviewed_by_user_id is None

    def test_mark_as_reviewed(self, db_session):
        """Test marking a background as reviewed"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
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

        background.mark_as_reviewed(user.id)
        db_session.commit()

        assert background.needs_review is False
        assert background.reviewed_at is not None
        assert background.reviewed_by_user_id == user.id

    def test_character_background_relationships(self, db_session):
        """Test character background relationships"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
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

        # Test character relationship
        assert background.character.id == character.id
        assert background.character.name == "Test Character"

        # Test reviewed_by relationship
        background.mark_as_reviewed(user.id)
        db_session.commit()
        assert background.reviewed_by.id == user.id
        assert background.reviewed_by.email == "test@example.com"

    def test_character_background_repr(self, db_session):
        """Test the string representation of CharacterBackground"""
        user = User(
            email="test@example.com", first_name="Test", surname="User", email_verified=True
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        character = Character(
            user_id=user.id, name="Test Character", status=CharacterStatus.ACTIVE.value
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

        expected_repr = "<CharacterBackground Test Character - Review: True>"
        assert str(background) == expected_repr
