import pytest
from models.database.faction import Faction

def test_new_faction(db):
    """Test creation of a new Faction."""
    name = "Test Faction"
    wiki_slug = "test-faction"
    
    faction = Faction(
        name=name,
        wiki_slug=wiki_slug,
        allow_player_characters=True
    )
    
    db.session.add(faction)
    db.session.commit()
    
    # Retrieve the faction from the database
    retrieved_faction = Faction.query.filter_by(name=name).first()
    
    assert retrieved_faction is not None
    assert retrieved_faction.name == name
    assert retrieved_faction.wiki_slug == wiki_slug
    assert retrieved_faction.allow_player_characters is True
    assert retrieved_faction.id is not None 