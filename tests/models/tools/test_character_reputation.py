"""Test character reputation functionality with skills and species abilities."""

import pytest

from models.database.faction import Faction
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.enums import AbilityType, BodyHitsType, CharacterStatus
from models.tools.character import Character, CharacterSkill


class TestCharacterReputation:
    """Test the reputation functionality for characters."""

    def test_character_activation_with_skill_reputation(self, db, new_user):
        """Test that character activation adds reputation from skills."""
        # Create a faction
        faction = Faction(name="Test Faction", wiki_slug="test-faction")
        db.session.add(faction)
        db.session.flush()

        # Create a skill with reputation
        skill = Skill(
            name="Test Skill",
            description="A test skill with reputation",
            skill_type="TEST",
            base_cost=5,
            adds_reputation_faction_id=faction.id,
            adds_reputation_value=10,
        )
        db.session.add(skill)
        db.session.flush()

        # Create a character
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            status=CharacterStatus.DEVELOPING.value,
        )
        db.session.add(character)
        db.session.flush()

        # Add the skill to the character
        character_skill = CharacterSkill(
            character_id=character.id,
            skill_id=skill.id,
            times_purchased=1,
            purchased_by_user_id=new_user.id,
        )
        db.session.add(character_skill)
        db.session.commit()

        # Activate the character
        character.activate(new_user)

        # Check that reputation was added
        assert character.get_reputation(faction.id) == 10

    def test_character_activation_with_species_reputation(self, db, new_user):
        """Test that character activation adds reputation from species abilities."""
        # Create a faction
        faction = Faction(name="Test Faction", wiki_slug="test-faction")
        db.session.add(faction)
        db.session.flush()

        # Create a species with reputation ability
        species = Species(
            name="Test Species",
            wiki_page="test-species",
            permitted_factions_list=[faction.id],
            body_hits_type=BodyHitsType.GLOBAL,
            body_hits=3,
            death_count=3,
        )
        db.session.add(species)
        db.session.flush()

        ability = Ability(
            name="Starting Reputation",
            description="This species starts with reputation",
            type=AbilityType.STARTING_REPUTATION,
            species=species,
            starting_reputation_faction_id=faction.id,
            starting_reputation_value=15,
        )
        db.session.add(ability)
        db.session.commit()

        # Create a character with the species
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status=CharacterStatus.DEVELOPING.value,
        )
        db.session.add(character)
        db.session.commit()

        # Activate the character
        character.activate(new_user)

        # Check that reputation was added
        assert character.get_reputation(faction.id) == 15

    def test_skill_purchase_adds_reputation(self, db, new_user):
        """Test that purchasing a skill adds reputation for active characters."""
        # Create a faction
        faction = Faction(name="Test Faction", wiki_slug="test-faction")
        db.session.add(faction)
        db.session.flush()

        # Create a skill with reputation
        skill = Skill(
            name="Test Skill",
            description="A test skill with reputation",
            skill_type="TEST",
            base_cost=5,
            adds_reputation_faction_id=faction.id,
            adds_reputation_value=10,
        )
        db.session.add(skill)
        db.session.flush()

        # Create an active character
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            status=CharacterStatus.ACTIVE.value,
        )
        db.session.add(character)
        db.session.commit()

        # Purchase the skill
        character.purchase_skill(skill, new_user)

        # Check that reputation was added
        assert character.get_reputation(faction.id) == 10

    def test_skill_refund_removes_reputation(self, db, new_user):
        """Test that refunding a skill removes reputation for active characters."""
        # Create a faction
        faction = Faction(name="Test Faction", wiki_slug="test-faction")
        db.session.add(faction)
        db.session.flush()

        # Create a skill with reputation
        skill = Skill(
            name="Test Skill",
            description="A test skill with reputation",
            skill_type="TEST",
            base_cost=5,
            adds_reputation_faction_id=faction.id,
            adds_reputation_value=10,
        )
        db.session.add(skill)
        db.session.flush()

        # Create an active character
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            status=CharacterStatus.ACTIVE.value,
        )
        db.session.add(character)
        db.session.commit()

        # Purchase the skill
        character.purchase_skill(skill, new_user)

        # Check that reputation was added
        assert character.get_reputation(faction.id) == 10

        # Refund the skill
        character.refund_skill(skill, new_user)

        # Check that reputation was removed
        assert character.get_reputation(faction.id) == 0
