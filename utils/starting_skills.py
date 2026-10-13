"""Grant species starting skills without counting them as paid purchases."""

from datetime import datetime, timezone

from models.database.skills import Skill
from models.database.species import Ability
from models.enums import AbilityType
from models.extensions import db
from models.tools.character import CharacterSkill


def choice_catalogue():
    """Species whose players pick a quota of skills at creation."""
    catalogue = []
    abilities = Ability.query.filter_by(type=AbilityType.STARTING_SKILL_CHOICES.value).all()
    for ability in abilities:
        groups = []
        for choice in ability.starting_skill_choices_list:
            skill_type = choice.get("skill_type")
            count = int(choice.get("count") or 0)
            if not skill_type or count <= 0:
                continue
            groups.append(
                {
                    "skill_type": skill_type,
                    "count": count,
                    "label": skill_type.replace("_", " ").title(),
                    "skills": _skills_for_species(ability.species_id, skill_type),
                }
            )
        if groups:
            catalogue.append({"species_id": ability.species_id, "groups": groups})
    return catalogue


def validate_starting_skill_picks(species, picked_ids):
    """Return an error message when the picks do not match the species quotas."""
    groups = _choice_groups(species)
    picked = []
    for raw_id in picked_ids or []:
        if str(raw_id).isdigit():
            picked.append(int(raw_id))
    if not groups:
        return None
    skills = {skill.id: skill for skill in Skill.query.filter(Skill.id.in_(picked)).all()}
    if len(skills) != len(picked):
        return "Choose starting skills from the lists for this species."
    for group in groups:
        allowed = {skill["id"] for skill in group["skills"]}
        chosen = [skill_id for skill_id in picked if skill_id in allowed]
        if len(chosen) != group["count"] or len(set(chosen)) != group["count"]:
            label = group["label"]
            return f"Choose {group['count']} {label} skills."
    allowed_ids = {skill["id"] for group in groups for skill in group["skills"]}
    if any(skill_id not in allowed_ids for skill_id in picked):
        return "Choose starting skills from the lists for this species."
    return None


def apply_starting_skills(character, species, user, picked_ids):
    """Give the species its free ranks, and remove grants that no longer apply."""
    desired = set(_fixed_skill_ids(species))
    if _choice_groups(species):
        for raw_id in picked_ids or []:
            if str(raw_id).isdigit():
                desired.add(int(raw_id))
    managed = _managed_skill_ids()
    owned = CharacterSkill.query.filter_by(character_id=character.id).all()
    for character_skill in owned:
        if character_skill.free_ranks and character_skill.skill_id not in desired:
            if character_skill.skill_id in managed:
                _remove_free_rank(character_skill)
    for skill_id in desired:
        _ensure_free_rank(character, skill_id, user)


def _choice_groups(species):
    if species is None:
        return []
    groups = []
    for ability in species.abilities:
        if _ability_type(ability) != AbilityType.STARTING_SKILL_CHOICES.value:
            continue
        for choice in ability.starting_skill_choices_list:
            skill_type = choice.get("skill_type")
            count = int(choice.get("count") or 0)
            if not skill_type or count <= 0:
                continue
            groups.append(
                {
                    "skill_type": skill_type,
                    "count": count,
                    "label": skill_type.replace("_", " ").title(),
                    "skills": _skills_for_species(species.id, skill_type),
                }
            )
    return groups


def _fixed_skill_ids(species):
    if species is None:
        return []
    skill_ids = []
    for ability in species.abilities:
        if _ability_type(ability) != AbilityType.STARTING_SKILLS.value:
            continue
        skill_ids.extend(int(skill_id) for skill_id in ability.starting_skills_list)
    return skill_ids


def _managed_skill_ids():
    """Skill ids a starting-skill ability can grant, across every species."""
    skill_ids = set()
    choice_types = set()
    for ability in Ability.query.all():
        ability_type = _ability_type(ability)
        if ability_type == AbilityType.STARTING_SKILLS.value:
            skill_ids.update(int(skill_id) for skill_id in ability.starting_skills_list)
        elif ability_type == AbilityType.STARTING_SKILL_CHOICES.value:
            for choice in ability.starting_skill_choices_list:
                if choice.get("skill_type"):
                    choice_types.add(choice["skill_type"])
    if choice_types:
        rows = Skill.query.filter(Skill.skill_type.in_(choice_types)).all()
        skill_ids.update(skill.id for skill in rows)
    return skill_ids


def _skills_for_species(species_id, skill_type):
    skills = []
    for skill in Skill.query.filter_by(skill_type=skill_type).order_by(Skill.name).all():
        required = [int(item) for item in skill.required_species_list]
        if required and int(species_id) not in required:
            continue
        skills.append(
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.format_applied(1),
            }
        )
    return skills


def _ensure_free_rank(character, skill_id, user):
    character_skill = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=skill_id
    ).first()
    if character_skill is None:
        db.session.add(
            CharacterSkill(
                character_id=character.id,
                skill_id=skill_id,
                times_purchased=1,
                free_ranks=1,
                purchased_by_user_id=user.id,
                purchased_at=datetime.now(timezone.utc),
            )
        )
        return
    if character_skill.free_ranks:
        return
    character_skill.times_purchased += 1
    character_skill.free_ranks = (character_skill.free_ranks or 0) + 1


def _remove_free_rank(character_skill):
    character_skill.free_ranks = max(0, (character_skill.free_ranks or 0) - 1)
    character_skill.times_purchased -= 1
    if character_skill.times_purchased <= 0:
        db.session.delete(character_skill)


def _ability_type(ability):
    ability_type = ability.type
    return ability_type.value if hasattr(ability_type, "value") else ability_type
