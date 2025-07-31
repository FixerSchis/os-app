"""Test reputation functionality for species abilities."""

import pytest

from models.database.faction import Faction
from models.database.species import Ability, Species
from models.enums import AbilityType, BodyHitsType


class TestSpeciesReputation:
    """Test the reputation functionality for species abilities."""

    def test_ability_with_starting_reputation(self, db):
        """Test creating an ability with starting reputation."""
        # Create a faction
        faction = Faction(name="Test Faction", wiki_slug="test-faction")
        db.session.add(faction)
        db.session.flush()

        # Create a species
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

        # Create an ability with starting reputation
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

        # Verify the ability was created correctly
        assert ability.starting_reputation_faction_id == faction.id
        assert ability.starting_reputation_value == 15
        assert ability.starting_reputation_faction == faction
        assert ability.type == AbilityType.STARTING_REPUTATION

    def test_ability_without_starting_reputation(self, db):
        """Test creating an ability without starting reputation."""
        # Create a species
        species = Species(
            name="Test Species",
            wiki_page="test-species",
            permitted_factions_list=[1],
            body_hits_type=BodyHitsType.GLOBAL,
            body_hits=3,
            death_count=3,
        )
        db.session.add(species)
        db.session.flush()

        # Create an ability without starting reputation
        ability = Ability(
            name="Generic Ability",
            description="A generic ability",
            type=AbilityType.GENERIC,
            species=species,
        )
        db.session.add(ability)
        db.session.commit()

        # Verify the ability was created correctly
        assert ability.starting_reputation_faction_id is None
        assert ability.starting_reputation_value is None
        assert ability.starting_reputation_faction is None
