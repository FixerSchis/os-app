"""Build print template preview objects from the template editor's Data tab.

Each template type starts from a base object, which is the built-in sample or a
copy of a chosen record. Filled-in fields replace the base values, and blank
fields keep them. Nothing built here is added to the database session.
"""

from models.database.conditions import Condition, ConditionStage
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.item_blueprint import ItemBlueprint
from models.database.medicaments import Medicament
from models.database.mods import Mod
from models.database.skills import Skill
from models.database.species import Species
from models.enums import PrintTemplateType, ScienceType
from models.extensions import db
from models.tools.character import (
    CharacterCondition,
    CharacterReputation,
    CharacterSkill,
    CharacterTag,
)
from models.tools.group import Group
from models.tools.samples.character import get_sample_character
from models.tools.samples.condition import get_sample_condition
from models.tools.samples.exotic import get_sample_exotic_substance
from models.tools.samples.item import get_sample_item
from models.tools.samples.medicament import get_sample_medicament

PREVIEW_CONTEXT_KEYS = {
    PrintTemplateType.CHARACTER_SHEET: "character",
    PrintTemplateType.CHARACTER_ID: "character",
    PrintTemplateType.ITEM_CARD: "item",
    PrintTemplateType.MEDICAMENT_CARD: "medicament",
    PrintTemplateType.CONDITION_CARD: "condition",
    PrintTemplateType.EXOTIC_SUBSTANCE_LABEL: "substance",
}


def _text(data, key):
    value = data.get(key)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _int(data, key):
    value = _text(data, key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _record(model, data, key):
    record_id = _int(data, key)
    return db.session.get(model, record_id) if record_id is not None else None


def _rows(data, key):
    rows = data.get(key)
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _apply_text(target, data, fields):
    for field in fields:
        value = _text(data, field)
        if value is not None:
            setattr(target, field, value)


def _apply_int(target, data, fields):
    for field in fields:
        value = _int(data, field)
        if value is not None:
            setattr(target, field, value)


def build_preview_character(data):
    character = get_sample_character()
    user = character.user
    for key, field in (("player_first_name", "first_name"), ("player_surname", "surname")):
        value = _text(data, key)
        if value is not None:
            setattr(user, field, value)
    earned_points = _int(data, "earned_character_points")
    if earned_points is not None:
        user.character_points = earned_points
    user_id = _int(data, "user_id")
    if user_id is not None:
        user.id = user_id
        character.user_id = user_id

    _apply_text(character, data, ("name", "pronouns_subject", "pronouns_object"))
    _apply_int(character, data, ("character_id", "base_character_points", "bank_account"))

    species = _record(Species, data, "species_id")
    if species is not None:
        character.species = species
    faction = _record(Faction, data, "faction_id")
    if faction is not None:
        character.faction = faction
    group_name = _text(data, "group_name")
    if group_name is not None:
        character.group = Group(name=group_name)

    tag_names = [name.strip() for name in (_text(data, "tags") or "").split(",") if name.strip()]
    if tag_names:
        character.tags = [CharacterTag(name=name) for name in tag_names]

    skills = []
    for row in _rows(data, "skills"):
        skill = _record(Skill, row, "skill_id")
        if skill is not None:
            ranks = max(1, _int(row, "ranks") or 1)
            skills.append(CharacterSkill(skill=skill, times_purchased=ranks, free_ranks=0))
    if skills:
        character.skills = skills

    conditions = []
    for row in _rows(data, "conditions"):
        condition = _record(Condition, row, "condition_id")
        if condition is not None:
            stage = max(1, _int(row, "stage") or 1)
            conditions.append(CharacterCondition(condition=condition, current_stage=stage))
    if conditions:
        character.active_conditions = conditions

    reputations = []
    for row in _rows(data, "reputations"):
        faction = _record(Faction, row, "faction_id")
        if faction is not None:
            reputations.append(CharacterReputation(faction=faction, value=_int(row, "value") or 0))
    if reputations:
        character.reputations = reputations
    return character


def build_preview_item(data):
    item = get_sample_item()
    blueprint = _record(ItemBlueprint, data, "blueprint_id")
    if blueprint is not None:
        item.blueprint = blueprint
    _apply_int(item, data, ("item_id", "version", "expiry"))
    mod_ids = data.get("mod_ids")
    if not isinstance(mod_ids, list):
        mod_ids = []
    mod_ids = [int(mod_id) for mod_id in mod_ids if str(mod_id).isdigit()]
    if mod_ids:
        item.mods_applied = Mod.query.filter(Mod.id.in_(mod_ids)).order_by(Mod.name).all()
    return item


def _copy_medicament(source):
    return Medicament(
        id=source.id,
        name=source.name,
        wiki_slug=source.wiki_slug,
        summary=source.summary,
        effect=source.effect,
        modes=source.modes,
    )


def build_preview_medicament(data):
    source = _record(Medicament, data, "source_id")
    medicament = _copy_medicament(source) if source else get_sample_medicament()
    _apply_text(medicament, data, ("name", "summary", "effect"))
    modes = [
        {"name": _text(row, "name") or "", "effect": _text(row, "effect") or ""}
        for row in _rows(data, "modes")
        if _text(row, "name") or _text(row, "effect")
    ]
    if modes:
        medicament.modes_list = modes
    return medicament


def _copy_condition(source):
    condition = Condition(
        id=source.id,
        name=source.name,
        progresses_naturally=source.progresses_naturally,
        stage_sheet_values=source.stage_sheet_values,
    )
    condition.stages = [
        ConditionStage(
            id=stage.id,
            stage_number=stage.stage_number,
            rp_effect=stage.rp_effect,
            diagnosis=stage.diagnosis,
            cure=stage.cure,
            duration=stage.duration,
        )
        for stage in sorted(source.stages, key=lambda stage: stage.stage_number)
    ]
    condition.tags = list(source.tags)
    return condition


def build_preview_condition(data):
    source = _record(Condition, data, "source_id")
    condition = _copy_condition(source) if source else get_sample_condition()
    _apply_text(condition, data, ("name",))
    stage_fields = ("rp_effect", "diagnosis", "cure")
    stage_rows = [
        row
        for row in _rows(data, "stages")
        if any(_text(row, field) for field in stage_fields) or _int(row, "duration") is not None
    ]
    if stage_rows:
        condition.stages = [
            ConditionStage(
                stage_number=number,
                rp_effect=_text(row, "rp_effect") or "",
                diagnosis=_text(row, "diagnosis") or "",
                cure=_text(row, "cure") or "",
                duration=_int(row, "duration") or 0,
            )
            for number, row in enumerate(stage_rows, start=1)
        ]
    return condition


def _copy_exotic(source):
    return ExoticSubstance(
        id=source.id,
        name=source.name,
        type=source.type,
        wiki_slug=source.wiki_slug,
        used_on=source.used_on,
        effect=source.effect,
        duration=source.duration,
    )


def build_preview_exotic(data):
    source = _record(ExoticSubstance, data, "source_id")
    substance = _copy_exotic(source) if source else get_sample_exotic_substance()
    _apply_text(substance, data, ("name", "used_on", "effect", "duration"))
    science_type = _text(data, "type")
    if science_type in ScienceType.values():
        substance.type = ScienceType(science_type)
    return substance


_BUILDERS = {
    PrintTemplateType.CHARACTER_SHEET: build_preview_character,
    PrintTemplateType.CHARACTER_ID: build_preview_character,
    PrintTemplateType.ITEM_CARD: build_preview_item,
    PrintTemplateType.MEDICAMENT_CARD: build_preview_medicament,
    PrintTemplateType.CONDITION_CARD: build_preview_condition,
    PrintTemplateType.EXOTIC_SUBSTANCE_LABEL: build_preview_exotic,
}


def build_preview_object(template_type, data=None):
    """The object a template of this type renders, built from the Data tab values."""
    builder = _BUILDERS.get(template_type)
    if builder is None:
        return None
    return builder(data if isinstance(data, dict) else {})


def get_preview_options(template_type):
    """Records the Data tab offers for this template type."""
    if template_type in (PrintTemplateType.CHARACTER_SHEET, PrintTemplateType.CHARACTER_ID):
        return {
            "species": Species.query.order_by(Species.name).all(),
            "factions": Faction.query.order_by(Faction.name).all(),
            "skills": Skill.query.order_by(Skill.name).all(),
            "conditions": Condition.query.order_by(Condition.name).all(),
        }
    if template_type == PrintTemplateType.ITEM_CARD:
        return {
            "blueprints": ItemBlueprint.query.order_by(ItemBlueprint.name).all(),
            "mods": Mod.query.order_by(Mod.name).all(),
        }
    if template_type == PrintTemplateType.MEDICAMENT_CARD:
        return {"medicaments": Medicament.query.order_by(Medicament.name).all()}
    if template_type == PrintTemplateType.CONDITION_CARD:
        return {"conditions": Condition.query.order_by(Condition.name).all()}
    if template_type == PrintTemplateType.EXOTIC_SUBSTANCE_LABEL:
        return {
            "exotics": ExoticSubstance.query.order_by(ExoticSubstance.name).all(),
            "science_types": ScienceType.descriptions(),
        }
    return {}
