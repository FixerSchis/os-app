import pytest
from models.database.species import Species, Ability
from models.enums import BodyHitsType, AbilityType
import json

def test_new_species_with_ability(db):
    """Test creation of a new Species with an associated Ability."""
    species_name = "Test Species"
    wiki_page = "test-species"
    permitted_factions = [1, 2, 3]
    keywords = ["test", "species"]
    
    # Create an ability
    ability = Ability(
        name="Test Ability",
        description="An ability for testing.",
        type=AbilityType.GENERIC.value
    )
    
    # Create the species
    species = Species(
        name=species_name,
        wiki_page=wiki_page,
        permitted_factions_list=permitted_factions,
        body_hits_type=BodyHitsType.GLOBAL.value,
        body_hits=10,
        death_count=3,
        keywords_list=keywords,
        abilities=[ability]
    )
    
    db.session.add(species)
    db.session.commit()
    
    # Retrieve the species from the database
    retrieved_species = Species.query.filter_by(name=species_name).first()
    
    assert retrieved_species is not None
    assert retrieved_species.name == species_name
    assert retrieved_species.wiki_page == wiki_page
    assert retrieved_species.body_hits_type_enum == BodyHitsType.GLOBAL
    assert retrieved_species.body_hits == 10
    assert retrieved_species.death_count == 3
    
    # Check JSON-encoded fields
    assert retrieved_species.permitted_factions_list == permitted_factions
    assert retrieved_species.keywords_list == keywords
    
    # Check relationship
    assert len(retrieved_species.abilities) == 1
    retrieved_ability = retrieved_species.abilities[0]
    assert retrieved_ability.name == "Test Ability"
    assert retrieved_ability.type == AbilityType.GENERIC 