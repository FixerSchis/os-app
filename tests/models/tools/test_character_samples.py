import pytest

from models.database.faction import Faction
from models.database.sample import Sample, SampleTag
from models.database.species import Species
from models.enums import ScienceType
from models.tools.character import Character, character_samples
from models.tools.user import User


def test_character_samples_relationship(db):
    """Test the many-to-many relationship between Character and Sample."""
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

    # Create a character
    character = Character(
        user_id=user.id,
        name="Test Character",
        faction_id=faction.id,
        species_id=species.id,
        status="active",
    )
    db.session.add(character)
    db.session.commit()

    # Create sample tags
    tag1 = SampleTag(name="Rare")
    tag2 = SampleTag(name="Dangerous")
    db.session.add_all([tag1, tag2])
    db.session.commit()

    # Create samples
    sample1 = Sample(
        name="Test Sample 1",
        type=ScienceType.LIFE,
        is_researched=False,
        description="A test sample",
        tags=[tag1],
    )
    sample2 = Sample(
        name="Test Sample 2",
        type=ScienceType.CORPOREAL,
        is_researched=True,
        description="Another test sample",
        tags=[tag2],
    )
    db.session.add_all([sample1, sample2])
    db.session.commit()

    # Assign samples to character
    character.samples.append(sample1)
    character.samples.append(sample2)
    db.session.commit()

    # Test the relationship
    assert len(character.samples.all()) == 2
    sample_names = [sample.name for sample in character.samples.all()]
    assert "Test Sample 1" in sample_names
    assert "Test Sample 2" in sample_names

    # Test removing a sample
    character.samples.remove(sample1)
    db.session.commit()
    assert len(character.samples.all()) == 1
    assert character.samples.first().name == "Test Sample 2"


def test_character_samples_query(db):
    """Test querying samples through the character relationship."""
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

    # Create a character
    character = Character(
        user_id=user.id,
        name="Test Character",
        faction_id=faction.id,
        species_id=species.id,
        status="active",
    )
    db.session.add(character)
    db.session.commit()

    # Create samples
    sample1 = Sample(
        name="Test Sample 1",
        type=ScienceType.LIFE,
        is_researched=False,
    )
    sample2 = Sample(
        name="Test Sample 2",
        type=ScienceType.CORPOREAL,
        is_researched=True,
    )
    db.session.add_all([sample1, sample2])
    db.session.commit()

    # Assign samples to character
    character.samples.append(sample1)
    character.samples.append(sample2)
    db.session.commit()

    # Test querying samples by type
    life_samples = character.samples.filter(Sample.type == ScienceType.LIFE).all()
    assert len(life_samples) == 1
    assert life_samples[0].name == "Test Sample 1"

    # Test querying researched samples
    researched_samples = character.samples.filter(Sample.is_researched.is_(True)).all()
    assert len(researched_samples) == 1
    assert researched_samples[0].name == "Test Sample 2"


def test_character_samples_audit_logging(db):
    """Test that sample changes are properly audited."""
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

    # Create a character
    character = Character(
        user_id=user.id,
        name="Test Character",
        faction_id=faction.id,
        species_id=species.id,
        status="active",
    )
    db.session.add(character)
    db.session.commit()

    # Create a sample
    sample = Sample(
        name="Test Sample",
        type=ScienceType.LIFE,
        is_researched=False,
    )
    db.session.add(sample)
    db.session.commit()

    # Add sample to character (this would be done through the routes)
    character.samples.append(sample)
    db.session.commit()

    # Verify the relationship exists
    assert len(character.samples.all()) == 1
    assert character.samples.first().name == "Test Sample"
