#!/usr/bin/env python3
"""
Script to populate default data after migrations.
"""

import html
import importlib.util
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta

# Add the project root to the Python path BEFORE any other imports.
# This file lives in scripts/<name>/, so the root is two directories up.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# flake8: noqa: E402
from app import create_app
from models import db
from models.database.conditions import Condition, ConditionStage
from models.database.cybernetic import Cybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.global_settings import GlobalSettings
from models.database.group_type import GroupType
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.medicaments import Medicament
from models.database.mods import Mod
from models.database.rule_tag import RuleTag
from models.database.sample import Sample, SampleTag
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.enums import (
    AbilityType,
    BodyHitsType,
    EventType,
    PrintTemplateType,
    ScienceType,
    WikiPageVersionStatus,
)
from models.event import Event
from models.tools.character import Character, CharacterSkill
from models.tools.print_template import PrintTemplate
from models.wiki import WikiPage, WikiPageVersion, WikiSection, WikiTag


def create_default_global_settings():
    """Create default global settings if none exist."""
    if not GlobalSettings.query.first():
        logging.info("Creating default global settings")
        settings = GlobalSettings(character_income_ec=30, group_income_contribution=30)
        db.session.add(settings)
        db.session.commit()


def create_default_wiki_pages():
    if not WikiPage.query.filter_by(slug="index").first():
        logging.info("Creating default wiki page")
        wiki_page = WikiPage(slug="index", title="Welcome to Orion Sphere LRP")
        db.session.add(wiki_page)
        db.session.commit()
        wiki_page_version = WikiPageVersion(
            page_slug="index",
            version_number=1,
            status=WikiPageVersionStatus.PUBLISHED,
        )
        db.session.add(wiki_page_version)
        db.session.commit()
        wiki_section = WikiSection(
            id=str(uuid.uuid4()),
            version_id=wiki_page_version.id,
            order=0,
            title="Welcome!",
            content=(
                "<p>This is Orion Sphere LRP, a live roleplaying game for the "
                "Orion Sphere universe.</p>"
            ),
        )
        db.session.add(wiki_section)
        db.session.commit()


# Playable factions, then the MegaCorps characters can hold reputation with.
# allow_player_characters is False for a reputation-only organisation.
DEFAULT_FACTIONS = (
    ("Terran Ascendancy", "faction/terran-ascendancy", True),
    ("Free Union", "faction/free-union", True),
    ("Elysian Commonality", "faction/elysian-commonality", True),
    ("Tulaki Dominion", "faction/tulaki-dominion", True),
    ("Advanced Armaments", "faction/advanced-armaments", False),
    ("Spacer Collective", "faction/spacer-collective", False),
    ("Galactic Energy Supplies", "faction/galactic-energy-supplies", False),
    ("Clearance Organisation", "faction/clearance-organisation", False),
    ("Corporeal Perfection Syndicate", "faction/corporeal-perfection-syndicate", False),
    ("Lazarus Corporation", "faction/lazarus-corporation", False),
    ("Galactic Continental", "faction/galactic-continental", False),
)

_ASCENDANCY = ("Terran Ascendancy",)
_COMMONALITY = ("Elysian Commonality",)
_DOMINION = ("Tulaki Dominion",)
_FREE_UNION = ("Free Union",)
_ANY_FACTION = ("Terran Ascendancy", "Free Union", "Elysian Commonality", "Tulaki Dominion")

# death is the wiki death-count duration in seconds. hits is the number on each
# location, or the global total when hits_type is global. Unpublished species
# have no rules page, so their hit totals stay at 0.
DEFAULT_SPECIES = (
    {
        "name": "Arctonyx",
        "slug": "species/arctonyx",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 250,
        "factions": _DOMINION,
        "keywords": ("mammalian",),
    },
    {
        "name": "Ascendancy Terran",
        "slug": "species/ascendancy-terran",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _ASCENDANCY,
        "keywords": ("human", "terran"),
    },
    {
        "name": "Beaupecian",
        "slug": "species/beaupecian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 0,
        "death": 0,
        "factions": (),
        "keywords": ("unpublished", "unaligned"),
        "unpublished": True,
    },
    {
        "name": "Borean",
        "slug": "species/borean",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 300,
        "factions": _COMMONALITY,
        "keywords": ("humanoid",),
    },
    {
        "name": "Coronite",
        "slug": "species/coronite",
        "hits_type": BodyHitsType.GLOBAL,
        "hits": 2,
        "death": 300,
        "factions": _ASCENDANCY,
        "keywords": ("energy",),
    },
    {
        "name": "Cradian",
        "slug": "species/cradian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _DOMINION,
        "keywords": ("reptilian",),
    },
    {
        "name": "Elysian",
        "slug": "species/elysian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 1,
        "death": 200,
        "factions": _COMMONALITY,
        "keywords": ("humanoid", "psionic"),
    },
    {
        "name": "Etherna",
        "slug": "species/etherna",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _FREE_UNION,
        "keywords": ("humanoid",),
    },
    {
        "name": "Felani",
        "slug": "species/felani",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 150,
        "factions": _COMMONALITY,
        "keywords": ("mammalian", "psionic"),
    },
    {
        "name": "Free Union Terran",
        "slug": "species/free-union-terran",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _FREE_UNION,
        "keywords": ("human", "terran"),
    },
    {
        "name": "Gardener",
        "slug": "species/gardener",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 4,
        "death": 100,
        "factions": _FREE_UNION,
        "keywords": ("plant", "parasitic", "undead"),
    },
    {
        "name": "Garvian",
        "slug": "species/garvian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 0,
        "death": 0,
        "factions": (),
        "keywords": ("unpublished", "unaligned"),
        "unpublished": True,
    },
    {
        "name": "Gharial",
        "slug": "species/gharial",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 0,
        "death": 0,
        "factions": (),
        "keywords": ("unpublished", "unaligned"),
        "unpublished": True,
    },
    {
        "name": "Ikunkuma",
        "slug": "species/ikunkuma",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 400,
        "factions": _FREE_UNION,
        "keywords": ("mammalian",),
    },
    {
        "name": "Kelki",
        "slug": "species/kelki",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _DOMINION,
        "keywords": ("mammalian", "psionic"),
    },
    {
        "name": "Kordai",
        "slug": "species/kordai",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 3,
        "death": 120,
        "factions": ("Elysian Commonality", "Free Union"),
        "keywords": ("psionic",),
    },
    {
        "name": "Kulkani",
        "slug": "species/kulkani",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 0,
        "death": 0,
        "factions": (),
        "keywords": ("unpublished", "unaligned"),
        "unpublished": True,
    },
    {
        "name": "Lithos",
        "slug": "species/lithos",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 4,
        "death": 300,
        "factions": _COMMONALITY,
        "keywords": ("mineral", "psionic"),
    },
    {
        "name": "N-DAX",
        "slug": "species/n-dax",
        "hits_type": BodyHitsType.GLOBAL,
        "hits": 3,
        "death": 200,
        "factions": _ANY_FACTION,
        "keywords": ("avian", "xenobiological"),
    },
    {
        "name": "Notumi Cerebri",
        "slug": "species/notumi-cerebri",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 1,
        "death": 180,
        "factions": _ASCENDANCY,
        "keywords": ("humanoid",),
    },
    {
        "name": "Notumi Corpori",
        "slug": "species/notumi-corpori",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 1,
        "death": 180,
        "factions": _ASCENDANCY,
        "keywords": ("humanoid",),
    },
    {
        "name": "Olm",
        "slug": "species/olm",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 0,
        "death": 0,
        "factions": (),
        "keywords": ("unpublished", "unaligned"),
        "unpublished": True,
    },
    {
        "name": "Raegar",
        "slug": "species/raegar",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 300,
        "factions": _ASCENDANCY,
        "keywords": ("mammalian",),
    },
    {
        "name": "Reskan",
        "slug": "species/reskan",
        "hits_type": BodyHitsType.GLOBAL,
        "hits": 10,
        "death": 200,
        "factions": _COMMONALITY,
        "keywords": ("hive",),
    },
    {
        "name": "Sollen",
        "slug": "species/sollen",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 1,
        "death": 200,
        "factions": _ASCENDANCY,
        "keywords": ("reptilian",),
    },
    {
        "name": "Thrah'Kah",
        "slug": "species/thrah-kah",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 3,
        "death": 150,
        "factions": _ANY_FACTION,
        "keywords": ("humanoid",),
    },
    {
        "name": "Tulaki Megasaurian",
        "slug": "species/tulaki-megasaurian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 4,
        "death": 200,
        "factions": _DOMINION,
        "keywords": ("reptilian", "tulaki"),
    },
    {
        "name": "Tulaki Saurian",
        "slug": "species/tulaki-saurian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 3,
        "death": 200,
        "factions": _DOMINION,
        "keywords": ("reptilian", "tulaki"),
    },
    {
        "name": "Tulaki Serpentine",
        "slug": "species/tulaki-serpentine",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _DOMINION,
        "keywords": ("reptilian", "tulaki"),
    },
    {
        "name": "Urg",
        "slug": "species/urg",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 4,
        "death": 300,
        "factions": _ASCENDANCY,
        "keywords": ("humanoid",),
    },
    {
        "name": "Vikaas Aquerna",
        "slug": "species/vikaas-aquerna",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 3,
        "death": 200,
        "factions": _FREE_UNION,
        "keywords": ("aquatic", "psionic"),
    },
    {
        "name": "Wrathian",
        "slug": "species/wrathian",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 1,
        "death": 400,
        "factions": _ASCENDANCY,
        "keywords": ("humanoid",),
    },
    {
        "name": "Xak'Noth",
        "slug": "species/xak-noth",
        "hits_type": BodyHitsType.LOCATIONAL,
        "hits": 2,
        "death": 200,
        "factions": _DOMINION,
        "keywords": ("arthropoid",),
    },
    {
        "name": "Yelk",
        "slug": "species/yelk",
        "hits_type": BodyHitsType.GLOBAL,
        "hits": 6,
        "death": 200,
        "factions": _FREE_UNION,
        "keywords": ("fungoid",),
    },
)


def _wiki_tag(name):
    tag = WikiTag.query.filter_by(name=name).first()
    if tag is None:
        tag = WikiTag(name=name)
        db.session.add(tag)
        db.session.flush()
    return tag


def _ensure_stub_wiki_page(slug, title, tag_name, section_title, content):
    if WikiPage.query.filter_by(slug=slug).first():
        return
    wiki_page = WikiPage(slug=slug, title=title, tags=[_wiki_tag(tag_name)])
    db.session.add(wiki_page)
    db.session.flush()
    wiki_version = WikiPageVersion(
        page_slug=slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
    )
    db.session.add(wiki_version)
    db.session.flush()
    wiki_section = WikiSection(
        id=str(uuid.uuid4()),
        version_id=wiki_version.id,
        order=0,
        title=section_title,
        content=content,
    )
    db.session.add(wiki_section)
    db.session.flush()


def _faction_ids(names):
    factions = {faction.name: faction.id for faction in Faction.query.all()}
    missing = [name for name in names if name not in factions]
    if missing:
        raise ValueError(f"Species seed references unknown factions: {missing}")
    return [factions[name] for name in names]


def create_default_factions():
    """Create any wiki factions that are not already present."""
    for name, slug, allow_players in DEFAULT_FACTIONS:
        if Faction.query.filter_by(name=name).first():
            continue
        logging.info(f"Creating faction: {name}")
        faction = Faction(name=name, wiki_slug=slug, allow_player_characters=allow_players)
        db.session.add(faction)
        role = "Playable faction" if allow_players else "Reputation organisation"
        _ensure_stub_wiki_page(
            slug,
            f"{name} - Faction",
            "faction",
            name,
            f"<p>{role}. Description for {name}.</p>",
        )
    db.session.commit()


def _load_skill_definitions():
    """Load the wiki skill catalogue from the sibling module."""
    path = os.path.join(os.path.dirname(__file__), "default_skill_definitions.py")
    spec = importlib.util.spec_from_file_location("default_skill_definitions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SKILL_DEFINITIONS


def _skill_description(spec):
    description = spec["description"]
    required_name = spec.get("requires")
    if not required_name:
        return description
    requirement = f"Requires {required_name}"
    if spec.get("requires_rank"):
        requirement += f" rank {spec['requires_rank']}"
    return f"{description} {requirement}."


def _seed_sheet_values(spec):
    values = []
    if spec.get("will"):
        values.append({"id": "will", "description": "Will Points", "value": spec["will"]})
    if spec.get("psi"):
        values.append({"id": "psi", "description": "Psi Points", "value": spec["psi"]})
    return values


_STARTING_PSI = (
    ("Elysian", 2),
    ("Felani", 1),
    ("Kelki", 1),
    ("Kordai", 2),
    ("Lithos", 1),
    ("Vikaas Aquerna", 2),
)


def _has_sheet_value(owner, value_id):
    return any(value.get("id") == value_id for value in owner.character_sheet_values_list)


def _has_psi_sheet_value(owner):
    return _has_sheet_value(owner, "psi")


def link_default_skill_sheet_values():
    """Add seeded will and psi sheet values to existing skills that lack them."""
    for spec in _load_skill_definitions():
        values = _seed_sheet_values(spec)
        if not values:
            continue
        skill = Skill.query.filter_by(name=spec["name"]).first()
        if skill is None:
            continue
        missing = [value for value in values if not _has_sheet_value(skill, value["id"])]
        if missing:
            skill.character_sheet_values_list = skill.character_sheet_values_list + missing
    db.session.commit()


def link_default_psi_points():
    """Add sheet values to seeded skills and each psionic species' starting psi."""
    link_default_skill_sheet_values()
    for species_name, points in _STARTING_PSI:
        species = Species.query.filter_by(name=species_name).first()
        if species is None or any(_has_psi_sheet_value(row) for row in species.abilities):
            continue
        plural = "Point" if points == 1 else "Points"
        ability = Ability(
            species_id=species.id,
            name="Starting psi",
            description=f"Start with {points} Psi {plural}.",
            type=AbilityType.GENERIC,
        )
        ability.character_sheet_values_list = [
            {"id": "psi", "description": "Psi Points", "value": points}
        ]
        db.session.add(ability)
    db.session.commit()


_BLACK_FROST_STAGES = 10


def link_default_black_frost():
    """Seed the trigger-only Black Frost condition and give it to Raegar at a chosen stage."""
    condition = Condition.query.filter_by(name="Black Frost").first()
    if condition is None:
        condition = Condition(name="Black Frost", progresses_naturally=False)
        condition.stage_sheet_values_list = [
            {"id": "will", "description": "Will Points", "value": 1}
        ]
        condition.tags = RuleTag.resolve_list(["disease"])
        db.session.add(condition)
        db.session.flush()
        for stage_number in range(1, _BLACK_FROST_STAGES + 1):
            final = stage_number == _BLACK_FROST_STAGES
            db.session.add(
                ConditionStage(
                    condition_id=condition.id,
                    stage_number=stage_number,
                    rp_effect=(
                        "Black boils spread and pain grows. When this stage completes, "
                        "the character dies."
                        if final
                        else "Black boils spread further across the skin, with growing pain."
                    ),
                    diagnosis="Clusters of black boils. Genetic, and present in every Raegar.",
                    cure="Incurable. Medication eases the pain but does not stop it.",
                    duration=0,
                )
            )
    raegar = Species.query.filter_by(name="Raegar").first()
    has_ability = raegar is not None and any(
        ability.starting_condition_id == condition.id for ability in raegar.abilities
    )
    if raegar is not None and not has_ability:
        db.session.add(
            Ability(
                species_id=raegar.id,
                name="Black Frost",
                description=(
                    "Every Raegar has the Black Frost, an incurable condition with 10 stages. "
                    "Choose the starting stage when you create the character. A referee "
                    "advances it at most one stage per event, after a trigger. The character "
                    "dies when stage 10 completes. Each stage gives 1 Will Point. Spend 1 to "
                    "RESIST an EFFECT call or roleplay effect, gain 1 Steel Viscera rank for "
                    "one surgery, ignore a Medicament or Condition's roleplay effects for an "
                    "hour, act normally for 1 minute while Walking Wounded, or become Walking "
                    "Wounded after 1 minute Unconscious or Badly Injured. Regain 1 per 5 "
                    "minutes of meditative work with another Raegar."
                ),
                type=AbilityType.STARTING_CONDITION,
                starting_condition_id=condition.id,
            )
        )
    db.session.commit()


def _load_species_abilities():
    path = os.path.join(os.path.dirname(__file__), "default_species_abilities.py")
    spec = importlib.util.spec_from_file_location("default_species_abilities", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SPECIES_ABILITIES


def link_default_species_abilities():
    """Add each wiki ability a species lacks, matched by name, as printed text."""
    for species_name, abilities in _load_species_abilities().items():
        species = Species.query.filter_by(name=species_name).first()
        if species is None:
            logging.warning(f"Species {species_name} is missing; skipped its abilities")
            continue
        existing = {ability.name for ability in species.abilities}
        for name, description in abilities:
            if name in existing:
                continue
            db.session.add(
                Ability(
                    species_id=species.id,
                    name=name,
                    description=description,
                    type=AbilityType.GENERIC,
                )
            )
    db.session.commit()


def create_default_skills():
    """Create wiki skills if none exist."""
    if Skill.query.first():
        return

    definitions = _load_skill_definitions()
    names = [spec["name"] for spec in definitions]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        raise ValueError(f"Duplicate seeded skill names: {sorted(duplicates)}")

    factions = {faction.name: faction for faction in Faction.query.all()}
    created = {}
    for spec in definitions:
        skill = Skill(
            name=spec["name"],
            description=_skill_description(spec),
            skill_type=spec["skill_type"],
            group_name=spec.get("group"),
            base_cost=spec["base_cost"],
            can_purchase_multiple=spec.get("multiple", False),
            cost_increases=spec.get("increases", False),
            earned_points_only=spec.get("earned_only", False),
            max_ranks=spec.get("max_ranks"),
            adds_engineering_mods=spec.get("mods", 0),
            adds_engineering_downtime=spec.get("eng_slots", 0),
            adds_science_downtime=spec.get("sci_slots", 0),
            science_type=spec.get("science"),
        )
        skill.character_sheet_values_list = _seed_sheet_values(spec)
        required_faction = factions.get(spec.get("faction"))
        if required_faction is not None:
            skill.required_factions_list = [required_faction.id]
        reputation_name = spec.get("reputation_faction", spec.get("faction"))
        reputation_faction = factions.get(reputation_name) if spec.get("reputation") else None
        if reputation_faction is not None:
            skill.adds_reputation_faction_id = reputation_faction.id
            skill.adds_reputation_value = spec["reputation"]
        logging.info(f"Adding skill: {skill.name}")
        db.session.add(skill)
        created[spec["name"]] = skill

    db.session.flush()
    for spec in definitions:
        required_name = spec.get("requires")
        if required_name:
            created[spec["name"]].required_skill_id = created[required_name].id
        _assign_named_skill_lists(created[spec["name"]], spec, created)
    db.session.commit()


def _species_names(spec):
    species_name = spec.get("species")
    if not species_name:
        return []
    if isinstance(species_name, str):
        return [species_name]
    return list(species_name)


def link_default_skill_types():
    """Move seeded skills that are still marked professional into spaceflight."""
    definitions = _load_skill_definitions()
    changed = False
    for spec in definitions:
        if spec.get("skill_type") != "spaceflight":
            continue
        skill = Skill.query.filter_by(name=spec["name"]).first()
        if skill is None or skill.skill_type != "professional":
            continue
        skill.skill_type = "spaceflight"
        changed = True
    if changed:
        db.session.commit()


def link_default_skill_groups():
    """Fill an empty catalogue group name from the seed, leaving admin edits in place."""
    definitions = _load_skill_definitions()
    changed = False
    for spec in definitions:
        group_name = spec.get("group")
        if not group_name:
            continue
        skill = Skill.query.filter_by(name=spec["name"]).first()
        if skill is None or skill.group_name:
            continue
        skill.group_name = group_name
        changed = True
    if changed:
        db.session.commit()


_RETIRED_MUTATION_SKILLS = (
    "Mutate Claws",
    "Mutate Musculature",
    "Mutate Rapid Recovery",
)


def ensure_ranked_mutation_skills():
    """Add one skill per mutation rank, and drop the old unsplit rows when unused."""
    definitions = [
        spec for spec in _load_skill_definitions() if spec.get("skill_type") == "mutation"
    ]
    rows, added = _mutation_rank_rows(definitions)
    linked = _link_mutation_prerequisites(definitions, rows)
    removed = _remove_retired_mutation_skills()
    if added or linked or removed:
        db.session.commit()


def _mutation_rank_rows(definitions):
    rows = {}
    added = False
    for spec in definitions:
        skill = Skill.query.filter_by(name=spec["name"]).first()
        if skill is None:
            skill = Skill(
                name=spec["name"],
                description=_skill_description(spec),
                skill_type=spec["skill_type"],
                base_cost=spec["base_cost"],
                earned_points_only=spec.get("earned_only", False),
            )
            db.session.add(skill)
            added = True
        rows[spec["name"]] = skill
    if added:
        db.session.flush()
    return rows, added


def _link_mutation_prerequisites(definitions, rows):
    changed = False
    for spec in definitions:
        required_name = spec.get("requires")
        skill = rows[spec["name"]]
        if not required_name or skill.required_skill_id:
            continue
        skill.required_skill_id = rows[required_name].id
        changed = True
    return changed


def _remove_retired_mutation_skills():
    removed = False
    for name in _RETIRED_MUTATION_SKILLS:
        skill = Skill.query.filter_by(name=name).first()
        if skill is None or _mutation_skill_in_use(skill):
            continue
        db.session.delete(skill)
        removed = True
    return removed


def _mutation_skill_in_use(skill):
    return CharacterSkill.query.filter_by(skill_id=skill.id).first() is not None


def link_default_skill_reputation():
    """Point a seeded skill at its reputation faction once that faction exists."""
    definitions = _load_skill_definitions()
    factions = {faction.name: faction for faction in Faction.query.all()}
    changed = False
    for spec in definitions:
        if not spec.get("reputation"):
            continue
        reputation_name = spec.get("reputation_faction", spec.get("faction"))
        faction = factions.get(reputation_name)
        skill = Skill.query.filter_by(name=spec["name"]).first()
        if skill is None or faction is None or skill.adds_reputation_faction_id:
            continue
        skill.adds_reputation_faction_id = faction.id
        skill.adds_reputation_value = spec["reputation"]
        changed = True
    if changed:
        db.session.commit()


def link_default_captain_requirements():
    """Fill empty captain any-of and distinct-console lists from the catalogue."""
    definitions = _load_skill_definitions()
    skills = {skill.name: skill for skill in Skill.query.all()}
    changed = False
    for spec in definitions:
        skill = skills.get(spec["name"])
        if skill is None:
            continue
        if spec.get("any_of") and not skill.required_any_skills:
            skill_ids = _ids_for_names(spec["any_of"], skills)
            if skill_ids:
                skill.required_any_skills_list = skill_ids
                changed = True
        if spec.get("distinct_of") and not skill.distinct_requirements:
            skill_ids = _ids_for_names(spec["distinct_of"], skills)
            if skill_ids:
                skill.distinct_requirements_list = skill_ids
                changed = True
    if changed:
        db.session.commit()


def _assign_named_skill_lists(skill, spec, skills):
    if spec.get("any_of") and not skill.required_any_skills:
        skill_ids = _ids_for_names(spec["any_of"], skills)
        if skill_ids:
            skill.required_any_skills_list = skill_ids
    if spec.get("distinct_of") and not skill.distinct_requirements:
        skill_ids = _ids_for_names(spec["distinct_of"], skills)
        if skill_ids:
            skill.distinct_requirements_list = skill_ids


def _ids_for_names(names, skills):
    ids = []
    for name in names:
        skill = skills.get(name)
        if skill is None:
            logging.warning(f"Requirement skill {name} is missing")
            return []
        ids.append(skill.id)
    return ids


def link_default_skill_species():
    """Restrict seeded skills to a species once that species record exists."""
    definitions = _load_skill_definitions()
    changed = False
    for spec in definitions:
        names = _species_names(spec)
        if not names:
            continue
        skill = Skill.query.filter_by(name=spec["name"]).first()
        species = [Species.query.filter_by(name=name).first() for name in names]
        if skill is None or any(row is None for row in species) or skill.required_species:
            continue
        skill.required_species_list = [row.id for row in species]
        changed = True
    if changed:
        db.session.commit()


def link_default_starting_skills():
    """Grant named creation skills, and Corpori program choices, on existing species."""
    grants = (
        (
            "Arctonyx",
            "Free Steel Viscera",
            "One rank of Steel Viscera at character creation.",
            ("Steel Viscera",),
        ),
        (
            "Notumi Cerebri",
            "Technocratic culture",
            "Scientist and one rank of Corporeal Science at character creation.",
            ("Scientist", "Corporeal Science"),
        ),
        (
            "Sollen",
            "Technical aptitude",
            "One rank of Engineer and one rank of Extra Mods at character creation.",
            ("Engineer", "Extra Mods"),
        ),
    )
    for species_name, ability_name, description, skill_names in grants:
        _add_fixed_starting_skills(species_name, ability_name, description, skill_names)
    _add_corpori_program_choices()
    _add_arctonyx_console_pairs()
    _move_etherna_science_to_pair()
    db.session.commit()


def _add_fixed_starting_skills(species_name, ability_name, description, skill_names):
    species = Species.query.filter_by(name=species_name).first()
    if species is None or _species_has_ability(species, AbilityType.STARTING_SKILLS):
        return
    skill_ids = []
    for skill_name in skill_names:
        skill = Skill.query.filter_by(name=skill_name).first()
        if skill is None:
            logging.warning(f"Starting skill {skill_name} is missing; skipped {species_name}")
            return
        skill_ids.append(str(skill.id))
    ability = Ability(
        species_id=species.id,
        name=ability_name,
        description=description,
        type=AbilityType.STARTING_SKILLS,
    )
    ability.starting_skills_list = skill_ids
    db.session.add(ability)


def _add_corpori_program_choices():
    species = Species.query.filter_by(name="Notumi Corpori").first()
    if species is None or _species_has_ability(species, AbilityType.STARTING_SKILL_CHOICES):
        return
    ability = Ability(
        species_id=species.id,
        name="Known programs",
        description="Choose two standard programs and one advanced program at creation.",
        type=AbilityType.STARTING_SKILL_CHOICES,
    )
    ability.starting_skill_choices_list = [
        {"skill_type": "standard_program", "count": 2},
        {"skill_type": "advanced_program", "count": 1},
    ]
    db.session.add(ability)


def _add_arctonyx_console_pairs():
    """The first Basic console an Arctonyx buys grants that console's Advanced skill."""
    species = Species.query.filter_by(name="Arctonyx").first()
    if species is None or _species_has_ability(species, AbilityType.FIRST_SKILL_PAIR):
        return
    consoles = ("Helm", "Weapons", "Engineering", "Science", "Relay")
    pairs = []
    for console in consoles:
        basic = Skill.query.filter_by(name=f"{console} Console [Basic]").first()
        advanced = Skill.query.filter_by(name=f"{console} Console [Advanced]").first()
        if basic is None or advanced is None:
            logging.warning(f"Console pair for {console} is missing; skipped Arctonyx")
            return
        pairs.append({"trigger_skill_id": basic.id, "granted_skill_id": advanced.id})
    ability = Ability(
        species_id=species.id,
        name="Spaceflight aptitude",
        description=("The first Basic console skill also grants that console's Advanced skill."),
        type=AbilityType.FIRST_SKILL_PAIR,
    )
    ability.skill_pairs_list = pairs
    db.session.add(ability)


def _move_etherna_science_to_pair():
    """Buying Scientist grants one Etheric Science rank. Creation no longer grants it."""
    species = Species.query.filter_by(name="Etherna").first()
    scientist = Skill.query.filter_by(name="Scientist").first()
    science = Skill.query.filter_by(name="Etheric Science").first()
    if species is None or scientist is None or science is None:
        return
    for ability in list(species.abilities):
        current = ability.type.value if hasattr(ability.type, "value") else ability.type
        if ability.name == "Scientist training" and current == AbilityType.STARTING_SKILLS.value:
            db.session.delete(ability)
    db.session.flush()
    if not _species_has_ability(species, AbilityType.FIRST_SKILL_PAIR):
        ability = Ability(
            species_id=species.id,
            name="Scientist training",
            description="Buying Scientist grants one rank of Etheric Science.",
            type=AbilityType.FIRST_SKILL_PAIR,
        )
        ability.skill_pairs_list = [
            {"trigger_skill_id": scientist.id, "granted_skill_id": science.id}
        ]
        db.session.add(ability)
    for character in Character.query.filter_by(species_id=species.id).all():
        _align_etherna_science_grant(character, scientist.id, science.id)


def _align_etherna_science_grant(character, scientist_id, science_id):
    """Keep a free Etheric Science rank only when the character owns Scientist."""
    science_row = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=science_id
    ).first()
    owns_scientist = (
        CharacterSkill.query.filter_by(character_id=character.id, skill_id=scientist_id).first()
        is not None
    )
    if owns_scientist:
        if not character.skill_pair_grants_list:
            character.skill_pair_grants_list = [
                {"trigger_skill_id": scientist_id, "granted_skill_id": science_id}
            ]
        return
    if science_row is None or not science_row.free_ranks:
        return
    science_row.free_ranks = max(0, (science_row.free_ranks or 0) - 1)
    science_row.times_purchased -= 1
    if science_row.times_purchased <= 0:
        db.session.delete(science_row)


_STATUS_DISCOUNTS = (
    ("Ascendancy Terran", "Ascendancy Status"),
    ("Elysian", "Commonality Status"),
    ("Free Union Terran", "Free Union Status"),
    ("Tulaki Megasaurian", "Dominion Status"),
    ("Tulaki Saurian", "Dominion Status"),
    ("Tulaki Serpentine", "Dominion Status"),
)


_TOUGHNESS_EXTRA_HITS = {
    "Yelk": 3,
    "Reskan": 3,
    "N-DAX": 2,
}
_PASSPORT_BODY_HITS = "{{ character.species.body_hits }}"
_PASSPORT_BODY_HITS_WITH_TOUGHNESS = (
    "{% if character.toughness_hit_bonus() %}"
    "{{ character.species.body_hits }} + {{ character.toughness_hit_bonus() }}"
    "{% else %}{{ character.species.body_hits if character.species else 0 }}{% endif %}"
)


_PASSPORT_SPECIES_ABILITIES = "{% for ability in character.species.abilities %}"
_PASSPORT_PRINTED_ABILITIES = "{% for ability in character.printed_abilities() %}"


def link_default_character_sheet_abilities():
    """Print abilities stored on the character beside the species abilities."""
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CHARACTER_SHEET).first()
    if (
        template is None
        or not template.front_html
        or "printed_abilities" in template.front_html
        or _PASSPORT_SPECIES_ABILITIES not in template.front_html
    ):
        return
    template.front_html = template.front_html.replace(
        _PASSPORT_SPECIES_ABILITIES, _PASSPORT_PRINTED_ABILITIES, 1
    )
    db.session.commit()


_GROUP_INCOME_BONUS = 30
_GROUP_INCOME_DESCRIPTION = "Adds 30 EC to group income for each attending character."


def link_default_group_income():
    """Keep Ascendancy Terran group income as a flat 30 EC bonus."""
    species = Species.query.filter_by(name="Ascendancy Terran").first()
    if species is None:
        return
    changed = False
    for ability in species.abilities:
        current = ability.type.value if hasattr(ability.type, "value") else ability.type
        if current != AbilityType.GROUP_INCOME.value:
            continue
        if ability.additional_group_income == 6:
            ability.additional_group_income = _GROUP_INCOME_BONUS
            changed = True
        if ability.description in (
            "Increases the amount of income a group receives.",
            "Adds 6 EC to group income for each attending character.",
        ):
            ability.description = _GROUP_INCOME_DESCRIPTION
            changed = True
    if changed:
        db.session.commit()


def link_default_toughness_hits():
    """Set Toughness hit conversions, and print them on the character sheet."""
    changed = False
    for species_name, extra in _TOUGHNESS_EXTRA_HITS.items():
        species = Species.query.filter_by(name=species_name).first()
        if species is None or species.extra_hits_per_toughness not in (None, 1):
            continue
        species.extra_hits_per_toughness = extra
        changed = True
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CHARACTER_SHEET).first()
    if (
        template
        and template.front_html
        and "toughness_hit_bonus" not in template.front_html
        and _PASSPORT_BODY_HITS in template.front_html
    ):
        template.front_html = template.front_html.replace(
            _PASSPORT_BODY_HITS, _PASSPORT_BODY_HITS_WITH_TOUGHNESS, 1
        )
        changed = True
    if changed:
        db.session.commit()


def link_default_status_discounts():
    """Give each faction's core species a 1-point discount on its status skill."""
    changed = False
    for species_name, skill_name in _STATUS_DISCOUNTS:
        if _add_status_discount(species_name, skill_name):
            changed = True
    if changed:
        db.session.commit()


def _add_status_discount(species_name, skill_name):
    species = Species.query.filter_by(name=species_name).first()
    skill = Skill.query.filter_by(name=skill_name).first()
    if species is None or skill is None:
        logging.warning(f"Status discount for {species_name} / {skill_name} is missing")
        return False
    if _species_discounts_skill(species, skill.id):
        return False
    ability = Ability(
        species_id=species.id,
        name="Status discount",
        description=f"{skill_name} costs 1 character point less per rank.",
        type=AbilityType.SKILL_DISCOUNTS,
    )
    ability.skill_discounts_dict = {str(skill.id): 1}
    db.session.add(ability)
    return True


def _species_discounts_skill(species, skill_id):
    for ability in species.abilities:
        if _ability_type_value(ability) != AbilityType.SKILL_DISCOUNTS.value:
            continue
        if str(skill_id) in ability.skill_discounts_dict:
            return True
    return False


def _ability_type_value(ability):
    ability_type = ability.type
    return ability_type.value if hasattr(ability_type, "value") else ability_type


_FELANI_BANNED_SKILLS = (
    "Heavy Armour Training",
    "Heavy Energy Weapon Training",
    "Large Melee Weapon Training",
)


def link_default_skill_bans():
    """Stop Felani buying heavy armour, heavy energy weapons, and large melee weapons."""
    if _add_felani_skill_bans():
        db.session.commit()


def _add_felani_skill_bans():
    species = Species.query.filter_by(name="Felani").first()
    if species is None or _species_has_ability(species, AbilityType.SKILL_BANS):
        return False
    skill_ids = []
    for skill_name in _FELANI_BANNED_SKILLS:
        skill = Skill.query.filter_by(name=skill_name).first()
        if skill is None:
            logging.warning(f"Banned skill {skill_name} is missing; skipped Felani")
            return False
        skill_ids.append(str(skill.id))
    ability = Ability(
        species_id=species.id,
        name="Skill bans",
        description=(
            "Cannot buy Heavy Armour Training, Heavy Energy Weapon Training, "
            "or Large Melee Weapon Training."
        ),
        type=AbilityType.SKILL_BANS,
    )
    ability.banned_skills_list = skill_ids
    db.session.add(ability)
    return True


def link_default_rank_limits():
    """Set catalogue rank limits, and Felani's lower caps, when they are still empty."""
    changed = False
    for spec in _load_skill_definitions():
        if spec.get("max_ranks") is None:
            continue
        skill = Skill.query.filter_by(name=spec["name"]).first()
        if skill is None or skill.max_ranks is not None:
            continue
        skill.max_ranks = spec["max_ranks"]
        changed = True
    if _add_felani_rank_caps():
        changed = True
    if changed:
        db.session.commit()


def _add_felani_rank_caps():
    """Felani stop at 2 ranks of Toughness and the three Steel skills."""
    species = Species.query.filter_by(name="Felani").first()
    if species is None or _species_has_ability(species, AbilityType.SKILL_RANK_CAPS):
        return False
    caps = []
    for skill_name in ("Toughness", "Steel Head", "Steel Nerves", "Steel Viscera"):
        skill = Skill.query.filter_by(name=skill_name).first()
        if skill is None:
            logging.warning(f"Rank cap skill {skill_name} is missing; skipped Felani")
            return False
        caps.append({"skill_id": skill.id, "max_ranks": 2})
    ability = Ability(
        species_id=species.id,
        name="Rank cap",
        description=("At most 2 ranks of Toughness, Steel Head, Steel Nerves, or Steel Viscera."),
        type=AbilityType.SKILL_RANK_CAPS,
    )
    ability.rank_caps_list = caps
    db.session.add(ability)
    return True


_POROUS_HIDE_DESCRIPTION = (
    "Radiation, toxic, and disease conditions are acquired in half the time and "
    "progress in half the stated time. Breathing gear is required to function and speak."
)
_HIVE_PHYSIOLOGY_DESCRIPTION = (
    "Cannot wear armour. Regenerates 1 global hit per minute in the same area. "
    "Immune to LETHAL. DISRUPT causes a 30 second knockout, or starts the death count "
    "at 0 hits. Environmental toxins progress in a quarter of the usual time. "
    "Medicaments need specialist delivery."
)
_CONDITION_TAG_NAMES = ("radiation", "toxic", "disease")


def _ensure_rule_tag(name):
    tag = RuleTag.query.filter(RuleTag.name.ilike(name)).first()
    if tag is not None:
        return tag
    tag = RuleTag(name=name)
    db.session.add(tag)
    db.session.flush()
    return tag


def _add_condition_timing(species_name, name, description, rate, tag_names, tags):
    species = Species.query.filter_by(name=species_name).first()
    if species is None or _species_has_ability(species, AbilityType.CONDITION_TIMING):
        return False
    ability = Ability(
        species_id=species.id,
        name=name,
        description=description,
        type=AbilityType.CONDITION_TIMING,
        condition_progress_rate=rate,
    )
    ability.tags = [tags[tag_name] for tag_name in tag_names]
    db.session.add(ability)
    return True


def link_default_condition_timing():
    """Tag radiation, toxic, and disease, and set Vikaas and Reskan progress rates."""
    tags = {name: _ensure_rule_tag(name) for name in _CONDITION_TAG_NAMES}
    _add_condition_timing(
        "Vikaas Aquerna",
        "Porous hide",
        _POROUS_HIDE_DESCRIPTION,
        2,
        ("radiation", "toxic", "disease"),
        tags,
    )
    _add_condition_timing(
        "Reskan",
        "Hive physiology",
        _HIVE_PHYSIOLOGY_DESCRIPTION,
        4,
        ("toxic",),
        tags,
    )
    steel_viscera = Skill.query.filter_by(name="Steel Viscera").first()
    if steel_viscera is not None and steel_viscera.condition_progress_rate is None:
        steel_viscera.condition_progress_rate = 0.5
        steel_viscera.condition_tags = [tags["toxic"], tags["disease"]]
    db.session.commit()


def _species_has_ability(species, ability_type):
    for ability in species.abilities:
        current = ability.type.value if hasattr(ability.type, "value") else ability.type
        if current == ability_type.value:
            return True
    return False


def _species_wiki_content(species, unpublished):
    hit_type = species.body_hits_type
    hit_key = hit_type.value if isinstance(hit_type, BodyHitsType) else hit_type
    body_hits_desc = BodyHitsType.descriptions()[hit_key]
    factions = Faction.query.filter(Faction.id.in_(species.permitted_factions_list)).all()
    faction_names = [faction.name for faction in factions] or ["None published"]
    faction_list = "".join(f"<li>{name}</li>" for name in faction_names)
    note = ""
    if unpublished:
        note = "<p>The official wiki topic for this species does not exist yet.</p>"
    return f"""
                <h2>Species Information</h2>
                {note}
                <p>Body Hits: {species.body_hits}</p>
                <p>Death Count: {species.death_count} seconds</p>
                <p>Body Hits Type: {body_hits_desc}</p>
                <h3>Permitted Factions</h3>
                <ul>
                    {faction_list}
                </ul>
                """


def create_default_species():
    """Create any wiki species that are not already present."""
    for spec in DEFAULT_SPECIES:
        if Species.query.filter_by(name=spec["name"]).first():
            continue
        logging.info(f"Adding species: {spec['name']}")
        species = Species(
            name=spec["name"],
            wiki_page=spec["slug"],
            permitted_factions_list=_faction_ids(spec["factions"]),
            body_hits_type=spec["hits_type"],
            body_hits=spec["hits"],
            death_count=spec["death"],
            keywords_list=list(spec["keywords"]),
        )
        db.session.add(species)
        db.session.flush()
        if spec["name"] == "Ascendancy Terran":
            db.session.add(
                Ability(
                    species_id=species.id,
                    name="Additional Group Income",
                    description=_GROUP_INCOME_DESCRIPTION,
                    type=AbilityType.GROUP_INCOME,
                    additional_group_income=_GROUP_INCOME_BONUS,
                )
            )
        _ensure_stub_wiki_page(
            spec["slug"],
            f"{spec['name']} - Species",
            "species",
            spec["name"],
            _species_wiki_content(species, spec.get("unpublished", False)),
        )
    db.session.commit()


def _load_exotic_definitions():
    """Return (name, type, used on, effect, duration) for each wiki exotic substance."""
    path = os.path.join(os.path.dirname(__file__), "default_exotic_substances.py")
    spec = importlib.util.spec_from_file_location("default_exotic_substances", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lists = (
        (module.EXOTIC_PARTICLES, ScienceType.ETHERIC),
        (module.EXOTIC_REAGENTS, ScienceType.CORPOREAL),
        (module.EXOTIC_BIOTICS, ScienceType.LIFE),
    )
    return [(row[0], science_type, *row[1:]) for rows, science_type in lists for row in rows]


_RETIRED_EXOTICS = ("Bioplasma",)


def _exotic_slug(name):
    return "exotic/" + name.lower().replace(" ", "-")


def _exotic_wiki_content(used_on, effect, duration):
    return (
        f"<p><strong>Used on:</strong> {html.escape(used_on)}</p>"
        f"<p>{html.escape(effect)}</p>"
        f"<p><strong>Duration:</strong> {html.escape(duration)}</p>"
    )


def _exotic_in_use(exotic_id):
    from models.tools.downtime import DowntimePack
    from models.tools.group import Group
    from models.tools.research import ResearchStageRequirement

    for owner in Character.query.all() + Group.query.all():
        if exotic_id in owner.pack.exotics:
            return True
    for pack in DowntimePack.query.all():
        if any(str(entry.get("id")) == str(exotic_id) for entry in pack.exotic_substances or []):
            return True
    return (
        ResearchStageRequirement.query.filter_by(exotic_substance_id=exotic_id).first() is not None
    )


def _retire_placeholder_exotics():
    for name in _RETIRED_EXOTICS:
        substance = ExoticSubstance.query.filter_by(name=name).first()
        if substance is None or _exotic_in_use(substance.id):
            continue
        logging.info(f"Removing placeholder exotic: {name}")
        db.session.delete(substance)
    db.session.flush()


def create_default_exotics():
    """Create each wiki exotic substance, and fill in rules on rows that have none."""
    _retire_placeholder_exotics()
    for name, science_type, used_on, effect, duration in _load_exotic_definitions():
        substance = ExoticSubstance.query.filter_by(name=name).first()
        if substance is None:
            logging.info(f"Adding exotic: {name}")
            substance = ExoticSubstance(name=name, type=science_type, wiki_slug=_exotic_slug(name))
            db.session.add(substance)
        if not (substance.used_on or substance.effect or substance.duration):
            substance.used_on = used_on
            substance.effect = effect
            substance.duration = duration
        _ensure_stub_wiki_page(
            substance.wiki_slug,
            f"{name} - Exotic Substance",
            "exotic",
            name,
            _exotic_wiki_content(used_on, effect, duration),
        )
    db.session.commit()


_PLACEHOLDER_EXOTIC_LABEL = "{{ substance.name }}"


def link_default_exotic_label():
    """Replace the placeholder exotic label with one that prints the substance's rules."""
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.EXOTIC_SUBSTANCE_LABEL).first()
    if template is None or (template.front_html or "").strip() != _PLACEHOLDER_EXOTIC_LABEL:
        return
    folder = os.path.join("data", "templates", PrintTemplateType.EXOTIC_SUBSTANCE_LABEL.value)
    with open(os.path.join(folder, "front.html"), "r", encoding="utf-8") as handle:
        template.front_html = handle.read()
    if not (template.css_styles or "").strip():
        with open(os.path.join(folder, "styles.css"), "r", encoding="utf-8") as handle:
            template.css_styles = handle.read()
    db.session.commit()


def _load_medicament_definitions():
    path = os.path.join(os.path.dirname(__file__), "default_medicaments.py")
    spec = importlib.util.spec_from_file_location("default_medicaments", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MEDICAMENT_DEFINITIONS


_RENAMED_MEDICAMENTS = {"Radiation Nano-sponges": "Radiation Nanosponges"}
_RETIRED_MEDICAMENTS = ("Wound Sealant", "Bloodfire Antivirals")


def _medicament_slug(name):
    return "medicament/" + name.lower().replace(" ", "-")


def _medicament_modes(spec):
    return [{"name": name, "effect": effect} for name, effect in spec["modes"]]


def _medicament_wiki_content(spec):
    parts = [f"<p><strong>{html.escape(spec['summary'])}</strong></p>"]
    if spec["effect"]:
        parts.append(f"<p>{html.escape(spec['effect'])}</p>")
    if spec["modes"]:
        rows = "".join(
            f"<li><strong>{html.escape(name)}</strong> - {html.escape(effect)}</li>"
            for name, effect in spec["modes"]
        )
        parts.append(f"<h3>Modes</h3><ul>{rows}</ul>")
    return "".join(parts)


def _medicament_in_pack(medicament_id):
    from models.tools.group import Group

    for owner in Character.query.all() + Group.query.all():
        if medicament_id in owner.pack.medicaments:
            return True
    return False


def _rename_and_retire_medicaments():
    for old_name, new_name in _RENAMED_MEDICAMENTS.items():
        medicament = Medicament.query.filter_by(name=old_name).first()
        if medicament is None or Medicament.query.filter_by(name=new_name).first():
            continue
        logging.info(f"Renaming medicament {old_name} to {new_name}")
        medicament.name = new_name
        medicament.wiki_slug = _medicament_slug(new_name)
    for name in _RETIRED_MEDICAMENTS:
        medicament = Medicament.query.filter_by(name=name).first()
        if medicament is None or _medicament_in_pack(medicament.id):
            continue
        logging.info(f"Removing placeholder medicament: {name}")
        db.session.delete(medicament)
    db.session.flush()


def create_default_medicaments():
    """Create each wiki medicament, and fill in rules on rows that have none."""
    _rename_and_retire_medicaments()
    for spec in _load_medicament_definitions():
        name = spec["name"]
        medicament = Medicament.query.filter_by(name=name).first()
        if medicament is None:
            logging.info(f"Adding medicament: {name}")
            medicament = Medicament(name=name, wiki_slug=_medicament_slug(name))
            db.session.add(medicament)
        if not (medicament.summary or medicament.effect or medicament.modes):
            medicament.summary = spec["summary"]
            medicament.effect = spec["effect"]
            medicament.modes_list = _medicament_modes(spec)
        _ensure_stub_wiki_page(
            medicament.wiki_slug,
            f"{name} - Medicament",
            "medicament",
            name,
            _medicament_wiki_content(spec),
        )
    db.session.commit()


_PLACEHOLDER_MEDICAMENT_CARD = ("{{ medicament.name }} Front", "{{ medicament.name }} Back")


def link_default_medicament_card():
    """Replace the placeholder medicament card with one that prints the rules."""
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.MEDICAMENT_CARD).first()
    if template is None:
        return
    current = ((template.front_html or "").strip(), (template.back_html or "").strip())
    if current != _PLACEHOLDER_MEDICAMENT_CARD:
        return
    folder = os.path.join("data", "templates", PrintTemplateType.MEDICAMENT_CARD.value)
    contents = {}
    for filename in ("front.html", "back.html", "styles.css"):
        with open(os.path.join(folder, filename), "r", encoding="utf-8") as handle:
            contents[filename] = handle.read()
    template.front_html = contents["front.html"]
    template.back_html = contents["back.html"]
    if not (template.css_styles or "").strip():
        template.css_styles = contents["styles.css"]
    db.session.commit()


_BROKEN_CONDITION_CARD_BACK = "{{ character.name }} Back"


def link_default_condition_card():
    """Replace the condition card back that named a character, which conditions don't have."""
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CONDITION_CARD).first()
    if template is None or (template.back_html or "").strip() != _BROKEN_CONDITION_CARD_BACK:
        return
    path = os.path.join("data", "templates", PrintTemplateType.CONDITION_CARD.value, "back.html")
    with open(path, "r", encoding="utf-8") as handle:
        template.back_html = handle.read()
    db.session.commit()


def create_default_item_types():
    if not ItemType.query.first():
        default_types = [
            ("Small Melee Weapon", "MW"),
            ("Medium Melee Weapon", "MW"),
            ("Large Melee Weapon", "MW"),
            ("Light Energy Weapon", "EW"),
            ("Medium Energy Weapon", "EW"),
            ("Heavy Energy Weapon", "EW"),
            ("Projectile", "PJ"),
            ("Shield", "SH"),
            ("Light Armour", "AR"),
            ("Medium Armour", "AR"),
            ("Heavy Armour", "AR"),
            ("Assault Armour", "AR"),
            ("Energy Field", "EF"),
            ("Scanner", "DV"),
            ("Charge Pack", "DV"),
            ("Engineering Device", "DV"),
            ("Engineering Tools", "DV"),
            ("Medical Device", "DV"),
            ("Breathing Mask", "DV"),
            ("Artefact", "AX"),
        ]
        for name, prefix in default_types:
            logging.info(f"Adding item type: {name}")
            db.session.add(ItemType(name=name, id_prefix=prefix))
        db.session.commit()


def _load_mod_definitions():
    path = os.path.join(os.path.dirname(__file__), "default_mods.py")
    spec = importlib.util.spec_from_file_location("default_mods", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MOD_DEFINITIONS


def _rows_for_names(model, names, label):
    rows = model.query.filter(model.name.in_(names)).all()
    missing = sorted(set(names) - {row.name for row in rows})
    if missing:
        raise ValueError(f"Seed references unknown {label}: {missing}")
    return rows


def create_default_mods():
    if Mod.query.first():
        return
    for spec in _load_mod_definitions():
        name = spec["name"]
        logging.info(f"Adding mod: {name}")
        wiki_slug = "mod/" + name.lower().replace(" ", "-")
        _ensure_stub_wiki_page(
            wiki_slug,
            f"{name} - Mod",
            "mod",
            name,
            f"<p>{html.escape(spec['description'])}</p>",
        )
        mod = Mod(name=name, wiki_slug=wiki_slug, description=spec["description"])
        db.session.add(mod)
        mod.item_types = _rows_for_names(ItemType, spec["item_types"], "item types")
        mod.required_skills_list = [
            skill.id for skill in _rows_for_names(Skill, spec["requires"], "skills")
        ]
        mod.granted_by_skills_list = [
            skill.id for skill in _rows_for_names(Skill, spec["granted_by"], "skills")
        ]
    db.session.commit()


def _load_blueprint_definitions():
    path = os.path.join(os.path.dirname(__file__), "default_item_blueprints.py")
    spec = importlib.util.spec_from_file_location("default_item_blueprints", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BLUEPRINT_DEFINITIONS


def _blueprint_mods(name, item_type, mod_names):
    mods = {mod.name: mod for mod in _rows_for_names(Mod, mod_names, "mods")}
    for mod_name in mod_names:
        allowed = mods[mod_name].item_types
        if allowed and item_type not in allowed:
            raise ValueError(f"Mod {mod_name} cannot be applied to {name} ({item_type.name})")
    return [mods[mod_name] for mod_name in mod_names]


def create_default_item_blueprints():
    """Create the Downtime Equipment List blueprints if none exist."""
    if ItemBlueprint.query.first():
        return
    item_types = {item_type.name: item_type for item_type in ItemType.query.all()}
    prefix_counters = {}
    for spec in _load_blueprint_definitions():
        name = spec["name"]
        item_type = item_types.get(spec["item_type"])
        if item_type is None:
            raise ValueError(f"Blueprint seed references unknown item type: {spec['item_type']}")
        prefix = item_type.id_prefix
        prefix_counters[prefix] = prefix_counters.get(prefix, 0) + 1
        logging.info(f"Adding blueprint: {name}")
        blueprint = ItemBlueprint(
            name=name,
            item_type_id=item_type.id,
            blueprint_id=prefix_counters[prefix],
            base_cost=spec["base_cost"],
            ability=spec["ability"],
            purchaseable=True,
        )
        db.session.add(blueprint)
        blueprint.mods_applied = _blueprint_mods(name, item_type, spec["mods"])
        db.session.flush()
    db.session.commit()


def create_default_items():
    if not Item.query.first():
        items = (
            "AA Blaster Pistol",
            "AA Blaster Rifle",
            "AA PowerSkin",
            "AA Power Blade",
        )
        for name in items:
            blueprint = ItemBlueprint.query.filter_by(name=name).first()
            if blueprint is None:
                continue
            logging.info(f"Adding item: {name}")
            db.session.add(Item(item_id=1, blueprint_id=blueprint.id))
        db.session.commit()


def create_default_group_types():
    """Create default group types if none exist."""
    if not GroupType.query.first():
        logging.info("Creating default group types")

        def blueprints_for_types(type_names):
            return ItemBlueprint.query.join(ItemType).filter(ItemType.name.in_(type_names)).all()

        # Get some item blueprints for the group types
        weapons_blueprints = blueprints_for_types(
            [
                "Small Melee Weapon",
                "Medium Melee Weapon",
                "Large Melee Weapon",
                "Light Energy Weapon",
                "Medium Energy Weapon",
                "Heavy Energy Weapon",
            ]
        )
        armor_blueprints = blueprints_for_types(
            ["Light Armour", "Medium Armour", "Heavy Armour", "Assault Armour"]
        )
        device_blueprints = blueprints_for_types(
            ["Scanner", "Engineering Device", "Engineering Tools", "Medical Device"]
        )

        group_types = [
            GroupType(
                name="Military",
                description=(
                    "Military groups focus on combat and defense. They receive weapons and "
                    "armor with a 50-50 ratio of items to energy chits."
                ),
                income_items_list=[weapon.id for weapon in weapons_blueprints]
                + [armor.id for armor in armor_blueprints],
                income_items_discount=15,
                income_substances=False,
                income_substance_cost=0,
                income_medicaments=False,
                income_medicament_cost=0,
                income_distribution_dict={"items": 50, "chits": 50},
            ),
            GroupType(
                name="Scientific",
                description=(
                    "Scientific groups focus on research and development. They receive "
                    "exotics and devices with a 20-40-40 ratio of items/exotics/chits."
                ),
                income_items_list=[device.id for device in device_blueprints],
                income_items_discount=15,
                income_substances=True,
                income_substance_cost=5,
                income_medicaments=False,
                income_medicament_cost=0,
                income_distribution_dict={"items": 20, "exotics": 40, "chits": 40},
            ),
            GroupType(
                name="Medical",
                description=(
                    "Medical groups focus on healing and healthcare. They receive "
                    "medicaments with a 50-50 ratio of medicaments to energy chits."
                ),
                income_items_list=[],
                income_items_discount=0,
                income_substances=False,
                income_substance_cost=0,
                income_medicaments=True,
                income_medicament_cost=20,
                income_distribution_dict={"medicaments": 50, "chits": 50},
            ),
            GroupType(
                name="Corporate",
                description=(
                    "Corporate groups focus on business and trade. They receive 100% "
                    "energy chits with no items, exotics, or medicaments."
                ),
                income_items_list=[],
                income_items_discount=0,
                income_substances=False,
                income_substance_cost=0,
                income_medicaments=False,
                income_medicament_cost=0,
                income_distribution_dict={"chits": 100},
            ),
        ]

        for group_type in group_types:
            db.session.add(group_type)

        db.session.commit()


def create_default_conditions():
    if not Condition.query.first():
        # Generic science-sounding default conditions
        conditions_data = [
            {
                "name": "Quantum Flux Syndrome",
                "stages": [
                    {
                        "stage_number": 1,
                        "rp_effect": "Mild disorientation and temporal afterimages.",
                        "diagnosis": "Detected by quantum resonance scan.",
                        "cure": "Stabilize with a phase modulator.",
                        "duration": 2,
                    },
                    {
                        "stage_number": 2,
                        "rp_effect": "Severe time slips and memory loss.",
                        "diagnosis": "Temporal field instability observed.",
                        "cure": "Quantum field recalibration.",
                        "duration": 1,
                    },
                ],
            },
            {
                "name": "Nanite Contamination",
                "stages": [
                    {
                        "stage_number": 1,
                        "rp_effect": "Tingling sensation and metallic taste.",
                        "diagnosis": "Microscopic nanite scan.",
                        "cure": "Administer nanite purge serum.",
                        "duration": 3,
                    }
                ],
            },
            {
                "name": "Plasma Burn Fever",
                "stages": [
                    {
                        "stage_number": 1,
                        "rp_effect": "Elevated temperature and skin irritation.",
                        "diagnosis": "Thermal scan reveals plasma residue.",
                        "cure": "Apply plasma-neutralizing gel.",
                        "duration": 2,
                    }
                ],
            },
            {
                "name": "Synthetic Antibody Rejection",
                "stages": [
                    {
                        "stage_number": 1,
                        "rp_effect": "Fatigue and joint pain.",
                        "diagnosis": "Blood test for synthetic antibody markers.",
                        "cure": "Immunosuppressant therapy.",
                        "duration": 2,
                    },
                    {
                        "stage_number": 2,
                        "rp_effect": "Severe immune response and rash.",
                        "diagnosis": "Elevated white cell count.",
                        "cure": "Plasma exchange procedure.",
                        "duration": 1,
                    },
                ],
            },
            {
                "name": "Graviton Sickness",
                "stages": [
                    {
                        "stage_number": 1,
                        "rp_effect": "Dizziness and sense of heaviness.",
                        "diagnosis": "Graviton field analysis.",
                        "cure": "Field dampener application.",
                        "duration": 1,
                    }
                ],
            },
        ]
        for cond in conditions_data:
            logging.info(f"Adding condition: {cond['name']}")
            condition = Condition(name=cond["name"])
            db.session.add(condition)
            db.session.flush()  # Get condition.id
            for stage in cond["stages"]:
                stage_obj = ConditionStage(
                    condition_id=condition.id,
                    stage_number=stage["stage_number"],
                    rp_effect=stage["rp_effect"],
                    diagnosis=stage["diagnosis"],
                    cure=stage["cure"],
                    duration=stage["duration"],
                )
                db.session.add(stage_obj)
        db.session.commit()


def create_default_cybernetics():
    if not Cybernetic.query.first():
        tag = WikiTag(name="cybernetic")
        cybernetics = [
            {
                "name": "Cybernetic Limb",
                "wiki_slug": "cybernetic/cybernetic-limb",
                "neural_shock_value": 10,
                "implant_type": "Cybernetic",
                "slot": "Limb",
                "description": "Description for Cybernetic Limb.",
            },
            {
                "name": "Neural Interface",
                "wiki_slug": "cybernetic/neural-interface",
                "neural_shock_value": 15,
                "adds_science_downtime": 1,
                "science_type": ScienceType.GENERIC,
                "implant_type": "Cybernetic",
                "slot": "Brain",
                "description": "Description for Neural Interface.",
            },
            {
                "name": "Neural Catalogue Uplink",
                "wiki_slug": "cybernetic/neural-catalogue-uplink",
                "neural_shock_value": 10,
                "adds_science_downtime": 1,
                "science_type": ScienceType.GENERIC,
                "implant_type": "Cybernetic",
                "slot": "Brain",
                "description": "Adds a generic science downtime point. +10 seconds neural shock.",
            },
            {
                "name": "Hephaestus Implant",
                "wiki_slug": "cybernetic/hephaestus-implant",
                "neural_shock_value": 10,
                "adds_engineering_downtime": 1,
                "implant_type": "Cybernetic",
                "slot": "Hands",
                "description": "Adds an engineering downtime point. +10 seconds neural shock.",
            },
            {
                "name": "Nano Claws",
                "wiki_slug": "cybernetic/nano-claws",
                "neural_shock_value": 10,
                "implant_type": "Cybernetic",
                "slot": "Hands",
                "description": (
                    "Allows the user to use clawed weapon physreps. +10 seconds neural shock."
                ),
            },
            {
                "name": "Integrated Backup Coil",
                "wiki_slug": "cybernetic/integrated-backup-coil",
                "neural_shock_value": 0,
                "implant_type": "Cybernetic",
                "slot": "Spine",
                "description": "Limits neural shock to 10 seconds.",
            },
            {
                "name": "Plasma Infuser",
                "wiki_slug": "cybernetic/plasma-infuser",
                "neural_shock_value": 0,
                "implant_type": "Cybernetic",
                "slot": "Liver",
                "description": (
                    "Allows the user to spend a minute with an unresisting character to "
                    "inflict a Global Through to that character and restore one hit to "
                    "all of their own locations."
                ),
            },
            {
                "name": "Med-glands",
                "wiki_slug": "cybernetic/med-glands",
                "neural_shock_value": 0,
                "implant_type": "Bioware",
                "slot": "Neck",
                "description": (
                    "Allows the user to store up to 5 doses of medicament for self "
                    "administration at will."
                ),
            },
            {
                "name": "Amplified Filtration",
                "wiki_slug": "cybernetic/amplified-filtration",
                "neural_shock_value": 0,
                "implant_type": "Bioware",
                "slot": "Liver",
                "description": (
                    "The user restores one locational or global hit point every 30 minutes."
                ),
            },
            {
                "name": "Fake Bioware",
                "wiki_slug": "cybernetic/fake-bioware",
                "neural_shock_value": 0,
                "implant_type": "Bioware",
                "slot": "Spine",
                "description": (
                    "This is a test item. It identifies itself as a test item to let the "
                    "players know that none of these implants are necessarily real."
                ),
            },
        ]
        for implant in cybernetics:
            name = implant["name"]
            wiki_slug = implant["wiki_slug"]
            logging.info(f"Adding implant: {name}")
            cybernetic = Cybernetic(
                name=name,
                wiki_slug=wiki_slug,
                neural_shock_value=implant["neural_shock_value"],
                adds_engineering_mods=implant.get("adds_engineering_mods", 0),
                adds_engineering_downtime=implant.get("adds_engineering_downtime", 0),
                adds_science_downtime=implant.get("adds_science_downtime", 0),
                science_type=implant.get("science_type"),
                implant_type=implant["implant_type"],
                slot=implant["slot"],
            )
            db.session.add(cybernetic)
            db.session.flush()
            wiki_page = WikiPage(slug=wiki_slug, title=f"{name} - Implant", tags=[tag])
            db.session.add(wiki_page)
            db.session.flush()
            wiki_version = WikiPageVersion(
                page_slug=wiki_slug,
                version_number=1,
                status=WikiPageVersionStatus.PUBLISHED,
            )
            db.session.add(wiki_version)
            db.session.flush()
            wiki_section = WikiSection(
                id=str(uuid.uuid4()),
                version_id=wiki_version.id,
                order=0,
                title=name,
                content=f"<p>{html.escape(implant['description'])}</p>",
            )
            db.session.add(wiki_section)
            db.session.flush()
        db.session.commit()


def create_default_samples():
    if not Sample.query.first():
        tag = SampleTag(name="sample")
        samples = [
            ("Blood Sample", ScienceType.LIFE),
            ("Tissue Sample", ScienceType.LIFE),
            ("Energy Residue", ScienceType.ETHERIC),
        ]
        for name, sample_type in samples:
            logging.info(f"Adding sample: {name}")
            sample = Sample(name=name, type=sample_type, tags=[tag])
            db.session.add(sample)
        db.session.commit()


def create_default_events():
    if not Event.query.first():
        logging.info("Creating default events")
        prev_event = Event(
            event_number="1",
            event_type=EventType.MAINLINE.value,
            name="Test Previous Event",
            description="This is a test event",
            early_booking_deadline=datetime.now() + timedelta(days=-8),
            booking_deadline=datetime.now() + timedelta(days=-7),
            start_date=datetime.now() + timedelta(days=-6),
            end_date=datetime.now() + timedelta(days=-4),
            location="Test Location",
            google_maps_link="https://www.google.com/maps/place/Test+Location",
            meal_ticket_available=True,
            meal_ticket_price=20,
            bunks_available=True,
            standard_ticket_price=100,
            early_booking_ticket_price=80,
            child_ticket_price_12_15=20,
            child_ticket_price_7_11=15,
            child_ticket_price_under_7=0,
        )
        db.session.add(prev_event)

        next_event = Event(
            event_number="2",
            event_type=EventType.MAINLINE.value,
            name="Test Next Event",
            description="This is a test event",
            early_booking_deadline=datetime.now() + timedelta(days=1),
            booking_deadline=datetime.now() + timedelta(days=2),
            start_date=datetime.now() + timedelta(days=3),
            end_date=datetime.now() + timedelta(days=5),
            location="Test Location",
            google_maps_link="https://www.google.com/maps/place/Test+Location",
            meal_ticket_available=True,
            meal_ticket_price=20,
            bunks_available=True,
            standard_ticket_price=100,
            early_booking_ticket_price=80,
            child_ticket_price_12_15=20,
            child_ticket_price_7_11=15,
            child_ticket_price_under_7=0,
        )
        db.session.add(next_event)
        db.session.commit()


def create_default_templates():
    """Create default print templates if they don't exist."""
    # Define default templates with their specifications
    default_templates = [
        {
            "type": PrintTemplateType.CHARACTER_SHEET,
            "type_name": "Character Sheet",
            "width_mm": 148.0,
            "height_mm": 210.0,
            "has_back_side": True,
            "is_landscape": True,
            "items_per_row": 2,
            "items_per_column": 1,
            "margin_top_mm": 0.0,
            "margin_bottom_mm": 0.0,
            "margin_left_mm": 0.0,
            "margin_right_mm": 0.0,
            "gap_horizontal_mm": 0.0,
            "gap_vertical_mm": 0.0,
        },
        {
            "type": PrintTemplateType.CHARACTER_ID,
            "type_name": "Character ID",
            "width_mm": 63.5,
            "height_mm": 88.9,
            "has_back_side": False,
            "is_landscape": False,
            "items_per_row": 3,
            "items_per_column": 3,
            "margin_top_mm": 10.0,
            "margin_bottom_mm": 10.0,
            "margin_left_mm": 6.75,
            "margin_right_mm": 6.75,
            "gap_horizontal_mm": 2.0,
            "gap_vertical_mm": 2.0,
        },
        {
            "type": PrintTemplateType.ITEM_CARD,
            "type_name": "Item Card",
            "width_mm": 85.6,
            "height_mm": 53.98,
            "has_back_side": True,
            "is_landscape": False,
            "items_per_row": 2,
            "items_per_column": 4,
            "margin_top_mm": 10.0,
            "margin_bottom_mm": 10.0,
            "margin_left_mm": 17.4,
            "margin_right_mm": 17.4,
            "gap_horizontal_mm": 2.0,
            "gap_vertical_mm": 2.0,
        },
        {
            "type": PrintTemplateType.MEDICAMENT_CARD,
            "type_name": "Medicament Card",
            "width_mm": 63.5,
            "height_mm": 88.9,
            "has_back_side": True,
            "is_landscape": False,
            "items_per_row": 3,
            "items_per_column": 3,
            "margin_top_mm": 10.0,
            "margin_bottom_mm": 10.0,
            "margin_left_mm": 6.75,
            "margin_right_mm": 6.75,
            "gap_horizontal_mm": 2.0,
            "gap_vertical_mm": 2.0,
        },
        {
            "type": PrintTemplateType.CONDITION_CARD,
            "type_name": "Condition Card",
            "width_mm": 63.5,
            "height_mm": 88.9,
            "has_back_side": True,
            "is_landscape": False,
            "items_per_row": 3,
            "items_per_column": 3,
            "margin_top_mm": 10.0,
            "margin_bottom_mm": 10.0,
            "margin_left_mm": 6.75,
            "margin_right_mm": 6.75,
            "gap_horizontal_mm": 2.0,
            "gap_vertical_mm": 2.0,
        },
        {
            "type": PrintTemplateType.EXOTIC_SUBSTANCE_LABEL,
            "type_name": "Exotic Substance Label",
            "width_mm": 25.0,
            "height_mm": 10.0,
            "has_back_side": False,
            "is_landscape": False,
            "items_per_row": 7,
            "items_per_column": 24,
            "margin_top_mm": 13.0,
            "margin_bottom_mm": 13.0,
            "margin_left_mm": 10.0,
            "margin_right_mm": 10.0,
            "gap_horizontal_mm": 2.0,
            "gap_vertical_mm": 2.0,
        },
    ]

    def load_template_file(template_type, filename):
        """Load template file content, return empty string if file doesn't exist."""
        import os

        file_path = os.path.join("data", "templates", template_type.value, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    # Check for each template type and create if missing
    for template_data in default_templates:
        logging.info(f"Creating default template: {template_data['type_name']}")
        existing_template = PrintTemplate.query.filter_by(type=template_data["type"]).first()
        if not existing_template:
            # Load template content from files
            front_html = load_template_file(template_data["type"], "front.html")
            back_html = (
                load_template_file(template_data["type"], "back.html")
                if template_data["has_back_side"]
                else ""
            )
            css_styles = load_template_file(template_data["type"], "styles.css")

            template = PrintTemplate(
                type=template_data["type"],
                type_name=template_data["type_name"],
                width_mm=template_data["width_mm"],
                height_mm=template_data["height_mm"],
                front_html=front_html,
                back_html=back_html,
                css_styles=css_styles,
                has_back_side=template_data["has_back_side"],
                is_landscape=template_data["is_landscape"],
                items_per_row=template_data["items_per_row"],
                items_per_column=template_data["items_per_column"],
                margin_top_mm=template_data["margin_top_mm"],
                margin_bottom_mm=template_data["margin_bottom_mm"],
                margin_left_mm=template_data["margin_left_mm"],
                margin_right_mm=template_data["margin_right_mm"],
                gap_horizontal_mm=template_data["gap_horizontal_mm"],
                gap_vertical_mm=template_data["gap_vertical_mm"],
                created_by_user_id=1,  # Use user ID 1 as default
            )
            db.session.add(template)

    db.session.commit()


def create_default_data():
    """Create all default data in the correct order."""
    create_default_global_settings()
    create_default_wiki_pages()
    create_default_factions()
    create_default_skills()
    link_default_captain_requirements()
    link_default_skill_types()
    link_default_skill_groups()
    link_default_skill_reputation()
    create_default_species()
    ensure_ranked_mutation_skills()
    link_default_skill_species()
    link_default_starting_skills()
    link_default_rank_limits()
    link_default_skill_bans()
    link_default_status_discounts()
    link_default_group_income()
    link_default_toughness_hits()
    link_default_condition_timing()
    link_default_psi_points()
    create_default_exotics()
    create_default_medicaments()
    create_default_item_types()
    create_default_mods()
    create_default_item_blueprints()
    create_default_items()
    create_default_group_types()
    create_default_conditions()
    link_default_black_frost()
    link_default_species_abilities()
    create_default_cybernetics()
    create_default_samples()
    create_default_events()
    create_default_templates()
    link_default_character_sheet_abilities()
    link_default_medicament_card()
    link_default_condition_card()
    link_default_exotic_label()


def main():
    app = create_app()
    with app.app_context():
        # Ensure database is initialized first
        from utils.database_init import initialize_database

        initialize_database()

        # Now create default data
        create_default_data()
        print("Default data populated successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
