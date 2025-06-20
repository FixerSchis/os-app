import pytest
from models.database.exotic_substances import ExoticSubstance
from models.enums import ScienceType

def test_new_exotic_substance(db):
    """Test creation of a new ExoticSubstance."""
    substance_name = "Test Substance"
    wiki_slug = "test-substance"
    
    substance = ExoticSubstance(
        name=substance_name,
        wiki_slug=wiki_slug,
        type=ScienceType.LIFE
    )
    
    db.session.add(substance)
    db.session.commit()
    
    # Retrieve and assert
    retrieved_substance = ExoticSubstance.query.filter_by(name=substance_name).first()
    
    assert retrieved_substance is not None
    assert retrieved_substance.name == substance_name
    assert retrieved_substance.wiki_slug == wiki_slug
    assert retrieved_substance.type == ScienceType.LIFE
    assert retrieved_substance.id is not None 