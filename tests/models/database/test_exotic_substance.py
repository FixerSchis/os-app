from models.database.exotic_substances import ExoticSubstance
from models.enums import ScienceType


def test_new_exotic_substance(db):
    """Test creation of a new ExoticSubstance."""
    substance_name = "Test Substance"
    wiki_slug = "test-substance"

    substance = ExoticSubstance(name=substance_name, wiki_slug=wiki_slug, type=ScienceType.LIFE)

    db.session.add(substance)
    db.session.commit()

    # Retrieve and assert
    retrieved_substance = ExoticSubstance.query.filter_by(name=substance_name).first()

    assert retrieved_substance is not None
    assert retrieved_substance.name == substance_name
    assert retrieved_substance.wiki_slug == wiki_slug
    assert retrieved_substance.type == ScienceType.LIFE
    assert retrieved_substance.id is not None
    assert retrieved_substance.effect is None


def test_exotic_substance_rules(db):
    substance = ExoticSubstance(
        name="Rules Substance",
        wiki_slug="exotic/rules-substance",
        type=ScienceType.ETHERIC,
        used_on="Energy Fields",
        effect="Protects from Minor Heat Environments",
        duration="1 hour/all Hits lost",
    )
    db.session.add(substance)
    db.session.commit()

    db.session.expire_all()
    retrieved = ExoticSubstance.query.filter_by(name="Rules Substance").first()
    assert retrieved.used_on == "Energy Fields"
    assert retrieved.effect == "Protects from Minor Heat Environments"
    assert retrieved.duration == "1 hour/all Hits lost"
