"""Give species starting conditions at the stage the player chooses."""

from models.database.species import Ability
from models.enums import AbilityType
from models.extensions import db
from models.tools.character import CharacterCondition


def stage_field(condition_id):
    return f"starting_condition_stage_{condition_id}"


def _ability_type(ability):
    ability_type = ability.type
    return ability_type.value if hasattr(ability_type, "value") else ability_type


def _starting_conditions(species):
    if species is None:
        return []
    conditions = []
    for ability in species.abilities:
        if _ability_type(ability) != AbilityType.STARTING_CONDITION.value:
            continue
        condition = ability.starting_condition
        if condition is not None and condition.max_stage > 0:
            conditions.append(condition)
    return conditions


def _sheet_text(condition):
    parts = []
    for value in condition.stage_sheet_values_list:
        amount = value.get("value") or 0
        description = value.get("description") or value.get("id")
        if amount == 1 and description.endswith("s"):
            description = description[:-1]
        parts.append(f"{amount} {description}")
    if not parts:
        return ""
    return f"Each stage gives {' and '.join(parts)}."


def starting_condition_catalogue():
    """Species whose players choose a starting stage for a condition."""
    catalogue = []
    abilities = Ability.query.filter_by(type=AbilityType.STARTING_CONDITION.value).all()
    for ability in abilities:
        if ability.species_id is None:
            continue
        condition = ability.starting_condition
        if condition is None or condition.max_stage <= 0:
            continue
        catalogue.append(
            {
                "species_id": ability.species_id,
                "condition_id": condition.id,
                "name": condition.name,
                "max_stage": condition.max_stage,
                "sheet_text": _sheet_text(condition),
                "field": stage_field(condition.id),
            }
        )
    return catalogue


def managed_condition_ids(species):
    return {condition.id for condition in _starting_conditions(species)}


def _posted_stage(form, condition):
    raw = str(form.get(stage_field(condition.id)) or "").strip()
    if not raw.isdigit():
        return None
    stage = int(raw)
    if stage < 1 or stage > condition.max_stage:
        return None
    return stage


def validate_starting_condition_stages(species, form):
    """Return an error message when a required starting stage is missing or out of range."""
    for condition in _starting_conditions(species):
        if _posted_stage(form, condition) is None:
            return f"Choose a {condition.name} starting stage from 1 to {condition.max_stage}."
    return None


def apply_starting_conditions(character, species, form):
    """Set each species starting condition to the chosen stage, and drop stale ones.

    Returns a list of change descriptions for the audit log.
    """
    changes = []
    desired = {condition.id: condition for condition in _starting_conditions(species)}
    all_managed = {
        ability.starting_condition_id
        for ability in Ability.query.filter_by(type=AbilityType.STARTING_CONDITION.value).all()
        if ability.starting_condition_id
    }
    owned = {
        active.condition_id: active
        for active in CharacterCondition.query.filter_by(character_id=character.id).all()
    }
    for condition_id, active in owned.items():
        if condition_id in all_managed and condition_id not in desired:
            changes.append(f"Starting condition removed: {active.condition.name}")
            db.session.delete(active)
    for condition_id, condition in desired.items():
        stage = _posted_stage(form, condition)
        if stage is None:
            continue
        duration = next(
            (row.duration for row in condition.stages if row.stage_number == stage),
            0,
        )
        active = owned.get(condition_id)
        if active is None:
            db.session.add(
                CharacterCondition(
                    character_id=character.id,
                    condition_id=condition_id,
                    current_stage=stage,
                    current_duration=duration,
                )
            )
            changes.append(f"Starting condition: {condition.name} stage {stage}")
        elif active.current_stage != stage:
            changes.append(
                f"Starting condition {condition.name} stage changed from "
                f"{active.current_stage} to {stage}"
            )
            active.current_stage = stage
            active.current_duration = duration
    return changes
