"""The first skill bought from a species group grants its paired skill."""

from datetime import datetime, timezone

from models.database.skills import Skill
from models.enums import AbilityType
from models.extensions import db
from models.tools.character import CharacterSkill


def note_skill_purchase(character, skill, user):
    """Grant the pair when this purchase is the character's first from the group."""
    pairs = _pairs_for_species(character.species)
    granted_id = pairs.get(skill.id)
    if granted_id is None or character.skill_pair_grants_list:
        return
    owned_triggers = _owned_skill_ids(character) & set(pairs)
    if owned_triggers != {skill.id}:
        return
    character.skill_pair_grants_list = [
        {"trigger_skill_id": skill.id, "granted_skill_id": granted_id}
    ]
    _grant_free_skill(character, granted_id, user)


def note_skill_refund(character, skill):
    """Drop a pair grant when its triggering skill is refunded."""
    kept = []
    changed = False
    for record in character.skill_pair_grants_list:
        if int(record["trigger_skill_id"]) == skill.id:
            _revoke_free_skill(character, int(record["granted_skill_id"]))
            changed = True
            continue
        kept.append(record)
    if changed:
        character.skill_pair_grants_list = kept


def apply_skill_pair_grants(character, species, user):
    """Keep a remembered pair while this species still offers it and the trigger is owned."""
    pairs = _pairs_for_species(species)
    kept = []
    for record in character.skill_pair_grants_list:
        trigger_id = int(record["trigger_skill_id"])
        granted_id = int(record["granted_skill_id"])
        if not _owns(character, trigger_id):
            _revoke_free_skill(character, granted_id)
            continue
        kept.append({"trigger_skill_id": trigger_id, "granted_skill_id": granted_id})
        if pairs.get(trigger_id) == granted_id:
            _grant_free_skill(character, granted_id, user)
        else:
            _revoke_free_skill(character, granted_id)
    character.skill_pair_grants_list = kept


def _pairs_for_species(species):
    pairs = {}
    if species is None:
        return pairs
    for ability in species.abilities:
        if _ability_type(ability) != AbilityType.FIRST_SKILL_PAIR.value:
            continue
        for pair in ability.skill_pairs_list:
            trigger_id = pair.get("trigger_skill_id")
            granted_id = pair.get("granted_skill_id")
            if trigger_id and granted_id:
                pairs[int(trigger_id)] = int(granted_id)
    return pairs


def _owned_skill_ids(character):
    rows = CharacterSkill.query.filter_by(character_id=character.id).all()
    return {row.skill_id for row in rows}


def _owns(character, skill_id):
    return skill_id in _owned_skill_ids(character)


def _grant_free_skill(character, skill_id, user):
    """Add one free rank. A skill the character already paid for is left as a paid rank."""
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
    skill = character_skill.skill or db.session.get(Skill, skill_id)
    if skill is None or not skill.can_purchase_multiple:
        return
    character_skill.times_purchased += 1
    character_skill.free_ranks = (character_skill.free_ranks or 0) + 1


def _revoke_free_skill(character, skill_id):
    character_skill = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=skill_id
    ).first()
    if character_skill is None or not character_skill.free_ranks:
        return
    character_skill.free_ranks -= 1
    character_skill.times_purchased -= 1
    if character_skill.times_purchased <= 0:
        db.session.delete(character_skill)


def _ability_type(ability):
    ability_type = ability.type
    return ability_type.value if hasattr(ability_type, "value") else ability_type
