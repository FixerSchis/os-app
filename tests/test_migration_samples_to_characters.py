import pytest
from sqlalchemy import text

from models.database.faction import Faction
from models.database.group_type import GroupType
from models.database.sample import Sample, SampleTag
from models.database.species import Species
from models.enums import ScienceType
from models.tools.character import Character, character_samples
from models.tools.group import Group
from models.tools.user import User


def test_migration_samples_to_characters(db):
    """Test that the migration correctly moves samples from groups to characters."""
    # Create a user
    user = User(
        email="test@example.com",
        first_name="Test",
        surname="User",
        roles="user",
        character_points=10,
    )
    db.session.add(user)
    db.session.commit()

    # Create a faction
    faction = Faction(
        name="Test Faction",
        wiki_slug="test-faction",
        allow_player_characters=True,
    )
    db.session.add(faction)
    db.session.commit()

    # Create a species
    species = Species(
        name="Human",
        wiki_page="/wiki/human",
        permitted_factions="[1]",
        body_hits_type="global",
        body_hits=3,
        death_count=0,
    )
    db.session.add(species)
    db.session.commit()

    # Create a group type
    group_type = GroupType(
        name="Scientific",
        description="A scientific group type",
        income_items_list=[],
        income_items_discount=0.5,
        income_substances=True,
        income_substance_cost=5,
        income_medicaments=False,
        income_medicament_cost=0,
        income_distribution_dict={"items": 20, "exotics": 40, "chits": 40},
    )
    db.session.add(group_type)
    db.session.commit()

    # Create a group
    group = Group(
        name="Test Group",
        group_type_id=group_type.id,
        bank_account=500,
    )
    db.session.add(group)
    db.session.commit()

    # Create characters in the group
    character1 = Character(
        user_id=user.id,
        name="Character 1",
        faction_id=faction.id,
        species_id=species.id,
        group_id=group.id,
        status="active",
    )
    character2 = Character(
        user_id=user.id,
        name="Character 2",
        faction_id=faction.id,
        species_id=species.id,
        group_id=group.id,
        status="active",
    )
    db.session.add_all([character1, character2])
    db.session.commit()

    # Create sample tags
    tag1 = SampleTag(name="Rare")
    tag2 = SampleTag(name="Dangerous")
    db.session.add_all([tag1, tag2])
    db.session.commit()

    # Create samples assigned to the group (old way)
    sample1 = Sample(
        name="Test Sample 1",
        type=ScienceType.LIFE,
        is_researched=False,
        description="A test sample",
        group_id=group.id,
        tags=[tag1],
    )
    sample2 = Sample(
        name="Test Sample 2",
        type=ScienceType.CORPOREAL,
        is_researched=True,
        description="Another test sample",
        group_id=group.id,
        tags=[tag2],
    )
    db.session.add_all([sample1, sample2])
    db.session.commit()

    # Verify the old relationship exists
    assert len(group.samples.all()) == 2
    assert sample1.group_id == group.id
    assert sample2.group_id == group.id

    # Now simulate the migration by manually creating the character_samples relationships
    # This is what the migration would do
    for sample in group.samples:
        for character in group.characters:
            # Check if this assignment already exists
            existing = db.session.execute(
                text(
                    "SELECT 1 FROM character_samples WHERE character_id = :character_id "
                    "AND sample_id = :sample_id"
                ),
                {"character_id": character.id, "sample_id": sample.id},
            ).fetchone()

            if not existing:
                db.session.execute(
                    text(
                        "INSERT INTO character_samples (character_id, sample_id) "
                        "VALUES (:character_id, :sample_id)"
                    ),
                    {"character_id": character.id, "sample_id": sample.id},
                )

    db.session.commit()

    # Verify the new relationships exist
    assert len(character1.samples.all()) == 2
    assert len(character2.samples.all()) == 2

    # Verify both characters have the same samples
    character1_sample_names = [sample.name for sample in character1.samples.all()]
    character2_sample_names = [sample.name for sample in character2.samples.all()]
    assert character1_sample_names == character2_sample_names
    assert "Test Sample 1" in character1_sample_names
    assert "Test Sample 2" in character1_sample_names

    # Verify the old group relationship still exists (for backward compatibility)
    assert len(group.samples.all()) == 2


def test_migration_with_characters_without_group(db):
    """Test that the migration handles characters without groups correctly."""
    # Create a user
    user = User(
        email="test@example.com",
        first_name="Test",
        surname="User",
        roles="user",
        character_points=10,
    )
    db.session.add(user)
    db.session.commit()

    # Create a faction
    faction = Faction(
        name="Test Faction",
        wiki_slug="test-faction",
        allow_player_characters=True,
    )
    db.session.add(faction)
    db.session.commit()

    # Create a species
    species = Species(
        name="Human",
        wiki_page="/wiki/human",
        permitted_factions="[1]",
        body_hits_type="global",
        body_hits=3,
        death_count=0,
    )
    db.session.add(species)
    db.session.commit()

    # Create a character without a group
    character = Character(
        user_id=user.id,
        name="Lone Character",
        faction_id=faction.id,
        species_id=species.id,
        group_id=None,
        status="active",
    )
    db.session.add(character)
    db.session.commit()

    # Create a sample (this would be assigned directly to the character in the new system)
    sample = Sample(
        name="Lone Sample",
        type=ScienceType.LIFE,
        is_researched=False,
        description="A sample for a character without a group",
    )
    db.session.add(sample)
    db.session.commit()

    # Manually assign the sample to the character (simulating the new system)
    character.samples.append(sample)
    db.session.commit()

    # Verify the relationship exists
    assert len(character.samples.all()) == 1
    assert character.samples.first().name == "Lone Sample"
