#!/usr/bin/env python3
"""
Script to populate default data after migrations.
"""

import logging
import os
import sys
import uuid
from datetime import datetime, timedelta

# Add the project root to the Python path BEFORE any other imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def create_default_factions():
    """Create default factions if none exist."""
    if Faction.query.first() is None:
        default_factions = [
            ("Terran Ascendancy", "faction/terran-ascendancy", True),
            ("Free Union", "faction/free-union", True),
            ("Elysian Commonality", "faction/elysian-commonality", True),
            ("Tulaki Dominion", "faction/tulaki-dominion", True),
        ]

        tag = WikiTag(name="faction")
        for name, slug, allow_players in default_factions:
            logging.info(f"Creating faction: {name}")
            faction = Faction(name=name, wiki_slug=slug, allow_player_characters=allow_players)
            db.session.add(faction)
            # Create wiki page if it doesn't exist
            wiki_page = WikiPage.query.filter_by(slug=slug).first()
            if not wiki_page:
                wiki_page = WikiPage(slug=slug, title=f"{name} - Faction", tags=[tag])
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
                    title=name,
                    content=f"<p>Description for {name} faction.</p>",
                )
                db.session.add(wiki_section)
                db.session.flush()

        db.session.commit()


def create_default_skills():
    """Create default skills if none exist."""
    if not Skill.query.first():
        # Add skills first since species will reference them
        skills = [
            Skill(
                name="Medium Energy Weapon Training",
                description="Training in the use of medium energy weapons.",
                skill_type="combat",
                base_cost=2,
            ),
            Skill(
                name="Heavy Energy Weapon Training",
                description="Training in the use of heavy energy weapons.",
                skill_type="combat",
                base_cost=2,
            ),
            Skill(
                name="Toughness",
                description=("Increases physical resilience and ability to withstand damage."),
                skill_type="defense",
                base_cost=2,
                can_purchase_multiple=True,
                cost_increases=True,
            ),
            Skill(
                name="Engineering",
                description="Increases the ability to build and repair items.",
                skill_type="engineering",
                base_cost=2,
                can_purchase_multiple=True,
                cost_increases=True,
                adds_engineering_mods=2,
                adds_engineering_downtime=1,
            ),
            Skill(
                name="Additional Mods",
                description="Increases the number of known mods.",
                skill_type="engineering",
                base_cost=1,
                can_purchase_multiple=True,
                cost_increases=True,
                adds_engineering_mods=1,
            ),
            Skill(
                name="Science",
                description="Increases the ability to perform science actions.",
                skill_type="science",
                base_cost=2,
                adds_science_downtime=1,
                science_type=ScienceType.GENERIC.value,
            ),
            Skill(
                name="Life Science",
                description="Increases the ability to perform life science actions.",
                skill_type="science",
                base_cost=1,
                can_purchase_multiple=True,
                cost_increases=True,
                adds_science_downtime=1,
                science_type=ScienceType.LIFE.value,
            ),
            Skill(
                name="Corporeal Science",
                description=("Increases the ability to perform corporeal science actions."),
                skill_type="science",
                base_cost=1,
                can_purchase_multiple=True,
                cost_increases=True,
                adds_science_downtime=1,
                science_type=ScienceType.CORPOREAL.value,
            ),
            Skill(
                name="Etheric Science",
                description="Increases the ability to perform etheric science actions.",
                skill_type="science",
                base_cost=1,
                can_purchase_multiple=True,
                cost_increases=True,
                adds_science_downtime=1,
                science_type=ScienceType.ETHERIC.value,
            ),
            Skill(
                name="Discipline",
                description=(
                    "Increases the ability to perform discipline actions. " "Adds 2 Will Points."
                ),
                skill_type="discipline",
                base_cost=2,
                character_sheet_values_list=[
                    {"id": "will", "description": "Will Points", "value": 2}
                ],
            ),
        ]

        # Add skills to database and get their IDs
        for skill in skills:
            logging.info(f"Adding skill: {skill.name}")
            db.session.add(skill)
        db.session.flush()

        # Set up combat skill requirements
        heavy_weapon = next(s for s in skills if s.name == "Heavy Energy Weapon Training")
        medium_weapon = next(s for s in skills if s.name == "Medium Energy Weapon Training")
        heavy_weapon.required_skill_id = medium_weapon.id

        # Set up science skill requirements
        science = next(s for s in skills if s.name == "Science")
        life_science = next(s for s in skills if s.name == "Life Science")
        corporeal_science = next(s for s in skills if s.name == "Corporeal Science")
        etheric_science = next(s for s in skills if s.name == "Etheric Science")

        life_science.required_skill_id = science.id
        corporeal_science.required_skill_id = science.id
        etheric_science.required_skill_id = science.id

        db.session.commit()


def create_default_species():
    """Create default species if none exist."""
    if not Species.query.first():
        logging.info("Creating default species")
        species_list = [
            Species(
                name="Ascendancy Terran",
                wiki_page="species/ascendancy-terran",
                permitted_factions_list=[1, 2, 3, 4],
                body_hits_type=BodyHitsType.LOCATIONAL,
                body_hits=3,
                death_count=3,
                keywords_list=["human", "terran", "ascendancy"],
            ),
            Species(
                name="Free Union Human",
                wiki_page="species/free-union-human",
                permitted_factions_list=[2],
                body_hits_type=BodyHitsType.LOCATIONAL,
                body_hits=3,
                death_count=3,
                keywords_list=["human", "free union"],
            ),
            Species(
                name="Elysian",
                wiki_page="species/elysian",
                permitted_factions_list=[3],
                body_hits_type=BodyHitsType.GLOBAL,
                body_hits=4,
                death_count=2,
                keywords_list=["elysian", "psionic"],
            ),
            Species(
                name="Tulaki",
                wiki_page="species/tulaki",
                permitted_factions_list=[4],
                body_hits_type=BodyHitsType.LOCATIONAL,
                body_hits=5,
                death_count=4,
                keywords_list=["tulaki", "warrior"],
            ),
        ]

        for species in species_list:
            logging.info(f"Adding species: {species.name}")
            db.session.add(species)
        db.session.flush()

        # Add abilities to species
        for species in species_list:
            if species.name == "Ascendancy Terran":
                ability = Ability(
                    species_id=species.id,
                    name="Additional Group Income",
                    description="Increases the amount of income a group receives.",
                    type=AbilityType.GROUP_INCOME,
                    additional_group_income=30,
                )
                db.session.add(ability)

        # Create wiki pages for each species
        tag = WikiTag(name="species")
        for species in species_list:
            # Create wiki page
            wiki_page = WikiPage(
                slug=species.wiki_page, title=f"{species.name} - Species", tags=[tag]
            )
            db.session.add(wiki_page)
            db.session.flush()

            # Create wiki version
            wiki_version = WikiPageVersion(
                page_slug=species.wiki_page,
                version_number=1,
                status=WikiPageVersionStatus.PUBLISHED,
            )
            db.session.add(wiki_version)
            db.session.flush()

            # Create wiki section with species info
            body_hits_desc = BodyHitsType.descriptions()[species.body_hits_type.value]
            faction_list = "".join(
                f"<li>{faction}</li>" for faction in species.permitted_factions_list
            )
            wiki_section = WikiSection(
                id=str(uuid.uuid4()),
                version_id=wiki_version.id,
                order=0,
                title=f"{species.name}",
                content=f"""
                <h2>Species Information</h2>
                <p>Body Hits: {species.body_hits}</p>
                <p>Death Count: {species.death_count}</p>
                <p>Body Hits Type: {body_hits_desc}</p>
                <h3>Permitted Factions</h3>
                <ul>
                    {faction_list}
                </ul>
                """,
            )
            db.session.add(wiki_section)

        db.session.commit()


def create_default_exotics():
    if not ExoticSubstance.query.first():
        exotics = [
            ("Bioplasma", ScienceType.LIFE, "exotic/bioplasma"),
            ("Notum", ScienceType.CORPOREAL, "exotic/notum"),
            ("Quark Plasma", ScienceType.ETHERIC, "exotic/quark-plasma"),
        ]
        tag = WikiTag(name="exotic")
        for name, exo_type, wiki_slug in exotics:
            logging.info(f"Adding exotic: {name}")
            # Create wiki page if it doesn't exist
            wiki_page = WikiPage.query.filter_by(slug=wiki_slug).first()
            if not wiki_page:
                wiki_page = WikiPage(slug=wiki_slug, title=f"{name} - Exotic Substance", tags=[tag])
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
                    content=(f"<p>Description for {name} ({exo_type}) exotic substance.</p>"),
                )
                db.session.add(wiki_section)
                db.session.flush()
            substance = ExoticSubstance(name=name, type=exo_type, wiki_slug=wiki_slug)
            db.session.add(substance)
        db.session.commit()


def create_default_medicaments():
    if not Medicament.query.first():
        medicaments = [
            ("Wound Sealant", "medicament/wound-sealant"),
            ("Bloodfire Antivirals", "medicament/bloodfire-antivirals"),
            ("Radiation Nano-sponges", "medicament/radiation-nano-sponges"),
        ]
        tag = WikiTag(name="medicament")
        for name, wiki_slug in medicaments:
            logging.info(f"Adding medicament: {name}")
            # Create wiki page if it doesn't exist
            wiki_page = WikiPage.query.filter_by(slug=wiki_slug).first()
            if not wiki_page:
                wiki_page = WikiPage(slug=wiki_slug, title=f"{name} - Medicament", tags=[tag])
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
                    content=f"<p>Description for {name} medicament.</p>",
                )
                db.session.add(wiki_section)
                db.session.flush()
            medicament = Medicament(name=name, wiki_slug=wiki_slug)
            db.session.add(medicament)
        db.session.commit()


def create_default_item_types():
    if not ItemType.query.first():
        default_types = [
            ("Light Energy Weapon", "EW"),
            ("Medium Energy Weapon", "EW"),
            ("Heavy Energy Weapon", "EW"),
            ("Light Armor", "AR"),
            ("Medium Armor", "AR"),
            ("Heavy Armor", "AR"),
            ("Small Melee Weapon", "MW"),
            ("Medium Melee Weapon", "MW"),
            ("Large Melee Weapon", "MW"),
            ("Energy Field", "EF"),
            ("Scanner", "DV"),
            ("Device", "DV"),
            ("Artefact", "AX"),
        ]
        for name, prefix in default_types:
            logging.info(f"Adding item type: {name}")
            db.session.add(ItemType(name=name, id_prefix=prefix))
        db.session.commit()


def create_default_mods():
    if not Mod.query.first():
        ew_types = ItemType.query.filter(
            ItemType.name.in_(
                ["Light Energy Weapon", "Medium Energy Weapon", "Heavy Energy Weapon"]
            )
        ).all()
        tag = WikiTag(name="mod")
        mods = [
            ("Increase Charge Capacity", []),
            ("Hardened Components", []),
            ("Shock Bolt", ew_types),
        ]
        for name, types in mods:
            logging.info(f"Adding mod: {name}")
            wiki_slug = "mod/" + name.lower().replace(" ", "-")
            # Create wiki page if it doesn't exist
            wiki_page = WikiPage.query.filter_by(slug=wiki_slug).first()
            if not wiki_page:
                wiki_page = WikiPage(slug=wiki_slug, title=name + " - Mod", tags=[tag])
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
                    content=f"<p>Description for {name} mod.</p>",
                )
                db.session.add(wiki_section)
                db.session.flush()
            mod = Mod(name=name, wiki_slug=wiki_slug)
            mod.item_types = types
            db.session.add(mod)
        db.session.commit()


def create_default_item_blueprints():
    if not ItemBlueprint.query.first():
        # Helper to get item type by name
        def get_type(name):
            return ItemType.query.filter_by(name=name).first()

        # Helper to get mod by name
        def get_mod(name):
            return Mod.query.filter_by(name=name).first()

        blueprints = [
            ("AA Blaster", "Light Energy Weapon", 100, ["Increase Charge Capacity"]),
            (
                "AA Rifle",
                "Medium Energy Weapon",
                150,
                ["Increase Charge Capacity", "Hardened Components"],
            ),
            ("AA Cannon", "Heavy Energy Weapon", 200, ["Shock Bolt"]),
            ("Light Combat Armor", "Light Armor", 80, []),
            ("Medium Combat Armor", "Medium Armor", 120, ["Hardened Components"]),
            ("Heavy Combat Armor", "Heavy Armor", 180, ["Hardened Components"]),
            ("Combat Knife", "Small Melee Weapon", 50, []),
            ("Vibro Sword", "Medium Melee Weapon", 80, []),
            ("Plasma Axe", "Large Melee Weapon", 120, []),
            ("Personal Shield", "Energy Field", 200, ["Increase Charge Capacity"]),
            ("Tactical Scanner", "Scanner", 150, []),
            ("Medical Device", "Device", 100, []),
            ("Ancient Relic", "Artefact", 500, []),
        ]

        # Track blueprint_id per item type prefix
        prefix_counters = {}

        for name, type_name, cost, mod_names in blueprints:
            logging.info(f"Adding blueprint: {name}")
            item_type = get_type(type_name)
            if item_type:
                prefix = item_type.id_prefix
                if prefix not in prefix_counters:
                    prefix_counters[prefix] = 1
                blueprint_id = prefix_counters[prefix]
                prefix_counters[prefix] += 1

                blueprint = ItemBlueprint(
                    name=name, item_type_id=item_type.id, base_cost=cost, blueprint_id=blueprint_id
                )
                db.session.add(blueprint)
                db.session.flush()

                # Add mods to blueprint
                for mod_name in mod_names:
                    mod = get_mod(mod_name)
                    if mod:
                        blueprint.mods_applied.append(mod)

        db.session.commit()


def create_default_items():
    if not Item.query.first():
        # Helper to get blueprint by name
        def get_blueprint(name):
            return ItemBlueprint.query.filter_by(name=name).first()

        items = [
            ("AA Blaster", 1, 100),
            ("AA Rifle", 2, 150),
            ("Light Combat Armor", 1, 80),
            ("Combat Knife", 1, 50),
        ]

        for name, item_id, cost in items:
            logging.info(f"Adding item: {name}")
            blueprint = get_blueprint(name)
            if blueprint:
                item = Item(item_id=item_id, blueprint_id=blueprint.id)
                db.session.add(item)

        db.session.commit()


def create_default_group_types():
    """Create default group types if none exist."""
    if not GroupType.query.first():
        logging.info("Creating default group types")

        # Get some item blueprints for the group types
        weapons_blueprints = ItemBlueprint.query.filter(
            ItemBlueprint.item_type_id.in_([1, 2, 3])
        ).all()
        armor_blueprints = ItemBlueprint.query.filter(
            ItemBlueprint.item_type_id.in_([4, 5, 6])
        ).all()
        device_blueprints = ItemBlueprint.query.filter(
            ItemBlueprint.item_type_id.in_([7, 8, 9])
        ).all()

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
            ("Cybernetic Limb", "cybernetic/cybernetic-limb", 10, 0, 0, 0, None),
            (
                "Neural Interface",
                "cybernetic/neural-interface",
                15,
                0,
                0,
                1,
                ScienceType.GENERIC,
            ),
        ]
        for (
            name,
            wiki_slug,
            neural_shock_value,
            eng_mods,
            eng_downtime,
            sci_downtime,
            sci_type,
        ) in cybernetics:
            logging.info(f"Adding cybernetic: {name}")
            cybernetic = Cybernetic(
                name=name,
                wiki_slug=wiki_slug,
                neural_shock_value=neural_shock_value,
                adds_engineering_mods=eng_mods,
                adds_engineering_downtime=eng_downtime,
                adds_science_downtime=sci_downtime,
                science_type=sci_type,
            )
            db.session.add(cybernetic)
            db.session.flush()
            wiki_page = WikiPage(slug=wiki_slug, title=f"{name} - Cybernetic", tags=[tag])
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
                content=f"<p>Description for {name} cybernetic.</p>",
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
    create_default_species()
    create_default_exotics()
    create_default_medicaments()
    create_default_item_types()
    create_default_mods()
    create_default_item_blueprints()
    create_default_items()
    create_default_group_types()
    create_default_conditions()
    create_default_cybernetics()
    create_default_samples()
    create_default_events()
    create_default_templates()


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
