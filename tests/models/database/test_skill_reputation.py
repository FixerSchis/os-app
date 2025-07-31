"""Test reputation functionality for skills."""

import pytest

from models.database.faction import Faction
from models.database.skills import Skill
from models.enums import ScienceType


class TestSkillReputation:
    """Test the reputation functionality for skills."""

    def test_skill_with_reputation(self, db):
        """Test creating a skill with reputation."""
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
        db.session.commit()

        # Verify the skill was created correctly
        assert skill.adds_reputation_faction_id == faction.id
        assert skill.adds_reputation_value == 10
        assert skill.adds_reputation_faction == faction

    def test_skill_without_reputation(self, db):
        """Test creating a skill without reputation."""
        skill = Skill(
            name="Test Skill",
            description="A test skill without reputation",
            skill_type="TEST",
            base_cost=5,
        )
        db.session.add(skill)
        db.session.commit()

        # Verify the skill was created correctly
        assert skill.adds_reputation_faction_id is None
        assert skill.adds_reputation_value == 0
        assert skill.adds_reputation_faction is None
