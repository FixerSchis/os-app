from datetime import datetime

from models.database.faction import Faction
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.tools.character import Character, CharacterSkill, CharacterTag
from models.tools.user import User


def get_sample_character():
    user = User(
        id=1,
        email="admin@example.com",
        first_name="Admin",
        surname="User",
        pronouns_subject="they",
        pronouns_object="them",
        roles="admin",
        character_points=1,
    )
    faction = Faction(
        id=2,
        name="Free Traders",
        wiki_slug="free-traders",
        allow_player_characters=True,
    )
    ability = Ability(id=1, name="Combat", description="Combat ability")
    species = Species(
        id=1,
        name="Human",
        wiki_page="/wiki/human",
        permitted_factions="[2]",
        body_hits_type="standard",
        body_hits=3,
        death_count=0,
        abilities=[ability],
    )
    skill1 = Skill(id=1, name="Engineering", skill_type="ENGINEERING", base_cost=1)
    skill2 = Skill(id=2, name="Pilot", skill_type="GENERAL", base_cost=1)
    skill3 = Skill(id=3, name="Combat", skill_type="COMBAT", base_cost=1)
    skill4 = Skill(
        id=4,
        name="Discipline",
        skill_type="GENERAL",
        base_cost=1,
        character_sheet_values=('[{"id": "will", "description": "Will Points", "value": 1}]'),
    )
    char_skills = [
        CharacterSkill(skill=skill1, times_purchased=1),
        CharacterSkill(skill=skill2, times_purchased=2),
        CharacterSkill(skill=skill3, times_purchased=1),
        CharacterSkill(skill=skill4, times_purchased=1),
    ]
    tags = [CharacterTag(name="Veteran"), CharacterTag(name="Technician")]
    character = Character(
        id=1,
        name="Alex Chen",
        character_id=1,
        pronouns_subject="they",
        pronouns_object="them",
        status="active",
        base_character_points=10,
        bank_account=1500,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 20, 14, 45, 0),
        user=user,
        species=species,
        faction=faction,
    )
    character.skills = char_skills
    character.tags = tags
    return character
