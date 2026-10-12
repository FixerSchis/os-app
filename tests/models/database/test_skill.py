from models.database.faction import Faction
from models.database.skills import Skill
from models.database.species import Species
from models.enums import ScienceType
from models.tools.character import CharacterSkill, CharacterTag


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


def test_skill_description_uses_rank_maths():
    """Ranked skill descriptions calculate the effect at the purchased rank."""
    first_aid = Skill(
        name="First Aid",
        description="Stabilise a casualty in {70 - rank * 10} seconds, healing {rank} hits.",
        base_cost=2,
    )
    assert first_aid.format_applied(1) == "Stabilise a casualty in 60 seconds, healing 1 hits."
    assert first_aid.format_applied(3) == "Stabilise a casualty in 40 seconds, healing 3 hits."
    assert first_aid.format_unapplied() == "Stabilise a casualty in 60 seconds, healing 1 hits."

    engineer = Skill(
        name="Engineer",
        description="[{rank * 30}s] and {rank * 2} mod slots.",
        base_cost=2,
    )
    assert engineer.format_applied(1) == "[30s] and 2 mod slots."
    assert engineer.format_applied(2) == "[60s] and 4 mod slots."
    assert engineer.format_unapplied() == "[(30/rank)s] and (2/rank) mod slots."

    charges = Skill(name="Charges", description="[{num} charges]", base_cost=1)
    assert charges.format_applied(3) == "[3 charges]"
    assert charges.format_unapplied() == "[1 charges]"

    plain = Skill(name="Toughness", description="No calculation here.", base_cost=1)
    assert plain.format_applied(4) == "No calculation here."
    assert plain.format_unapplied() == "No calculation here."

    blank = Skill(name="Blank", base_cost=1)
    assert blank.format_applied(1) == ""
    assert blank.format_unapplied() == ""


def test_skill_description_ignores_unsafe_expressions():
    """Placeholders that are not rank maths are left unchanged."""
    skill = Skill(
        name="Unsafe",
        description="Leave {__import__('os').system('echo hi')} and {rank.__class__} alone.",
        base_cost=1,
    )
    assert skill.format_applied(2) == (
        "Leave {__import__('os').system('echo hi')} and {rank.__class__} alone."
    )
    division = Skill(name="Division", description="{rank / 0} stays", base_cost=1)
    assert division.format_applied(2) == "{rank / 0} stays"


def test_character_skill_formats_its_purchased_rank():
    skill = Skill(name="First Aid", description="Time: {70 - rank * 10}s", base_cost=2)
    character_skill = CharacterSkill(times_purchased=4)
    character_skill.skill = skill
    assert character_skill.format_description() == "Time: 30s"
