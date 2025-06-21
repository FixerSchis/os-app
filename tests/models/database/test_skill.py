from models.database.faction import Faction
from models.database.skills import Skill
from models.database.species import Species
from models.enums import ScienceType
from models.tools.character import CharacterTag


def test_new_skill_with_requirements(db):
    """Test creation of a new Skill with various requirements."""
    # 1. Create requirement objects
    req_skill = Skill(name="Required Skill", base_cost=0)
    req_faction = Faction(name="Required Faction", wiki_slug="req-faction")
    req_species = Species(
        name="Required Species",
        wiki_page="req-species",
        permitted_factions_list=[req_faction.id],
        body_hits_type="global",
        body_hits=1,
    )
    req_tag = CharacterTag(name="Required Tag")

    db.session.add_all([req_skill, req_faction, req_species, req_tag])
    db.session.commit()

    # 2. Create the main skill
    skill_name = "Advanced Skill"
    skill = Skill(
        name=skill_name,
        description="A skill with prerequisites.",
        skill_type="science",
        base_cost=10,
        science_type=ScienceType.ETHERIC,
        required_skill_id=req_skill.id,
        required_factions_list=[req_faction.id],
        required_species_list=[req_species.id],
        required_tags_list=[req_tag.id],
    )

    db.session.add(skill)
    db.session.commit()

    # 3. Retrieve and assert
    retrieved_skill = Skill.query.filter_by(name=skill_name).first()

    assert retrieved_skill is not None
    assert retrieved_skill.name == skill_name
    assert retrieved_skill.science_type == ScienceType.ETHERIC

    # Check requirements via property lists
    assert retrieved_skill.required_skill_id == req_skill.id
    assert retrieved_skill.required_factions_list == [req_faction.id]
    assert retrieved_skill.required_species_list == [req_species.id]
    assert retrieved_skill.required_tags_list == [req_tag.id]

    # Check requirements via relationship getters
    assert retrieved_skill.required_skill == req_skill
    assert retrieved_skill.get_required_factions() == [req_faction]
    assert retrieved_skill.get_required_species() == [req_species]
    assert retrieved_skill.get_required_tags() == [req_tag]
