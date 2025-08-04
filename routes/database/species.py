import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.item_blueprint import ItemBlueprint
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.enums import AbilityType, BodyHitsType
from models.extensions import db
from models.tools.character import Character
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required

species_bp = Blueprint("species", __name__)


@species_bp.route("/")
def species_list():
    # Get all species
    species = Species.query.all()
    factions = {f.id: f.name for f in Faction.query.all()}

    # Helper to get the first permitted faction's name for sorting
    def get_first_faction_name(species):
        if species.permitted_factions_list:
            faction = db.session.get(Faction, species.permitted_factions_list[0])
            return faction.name if faction else ""
        return ""

    # If user is not rules team, filter species
    if not current_user.is_authenticated or not current_user.has_permission("rules.species"):
        # Get user's active character species if they have one
        user_species_id = None
        if current_user.is_authenticated:
            active_char = Character.query.filter_by(
                user_id=current_user.id, status="active"
            ).first()
            if active_char:
                user_species_id = active_char.species_id
        # Filter species to only show those with player character factions or user's
        # species
        filtered_species = []
        for s in species:
            if user_species_id == s.id:
                filtered_species.append(s)
            else:
                # Check if any permitted faction allows player characters
                for faction_id in s.permitted_factions_list:
                    faction = db.session.get(Faction, faction_id)
                    if faction and faction.allow_player_characters:
                        filtered_species.append(s)
                        break
        species = filtered_species

    # Sort by first permitted faction name, then by species name
    species = sorted(species, key=lambda s: (get_first_faction_name(s), s.name))

    return render_template(
        "species/list.html",
        species=species,
        factions=factions,
        can_edit=current_user.is_authenticated and current_user.has_permission("rules.species"),
    )


@species_bp.route("/<int:species_id>/edit", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.species"])
def edit_species(species_id):
    species = Species.query.get_or_404(species_id)
    skills_list = Skill.query.all()
    factions = Faction.query.all()
    item_blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()

    # Convert factions to dictionaries for JSON serialization
    factions_dict = [
        {
            "id": faction.id,
            "name": faction.name,
        }
        for faction in factions
    ]

    # Convert item blueprints to dictionaries for JSON serialization
    item_blueprints_dict = [
        {
            "id": bp.id,
            "name": bp.name,
            "full_code": bp.full_code,
            "item_type_name": bp.item_type.name if bp.item_type else "Unknown",
        }
        for bp in item_blueprints
    ]

    return render_template(
        "species/edit.html",
        species=species,
        BodyHitsType=BodyHitsType,
        factions=factions,
        factions_dict=factions_dict,
        AbilityType=AbilityType,
        skills_list=skills_list,
        item_blueprints=item_blueprints_dict,
    )


@species_bp.route("/<int:species_id>/edit", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.species"])
def edit_species_post(species_id):
    species = Species.query.get_or_404(species_id)

    name = request.form.get("name")
    wiki_page = request.form.get("wiki_page")
    body_hits_type = request.form.get("body_hits_type")
    body_hits = request.form.get("body_hits")
    death_count = request.form.get("death_count")
    permitted_factions = request.form.getlist("permitted_factions")

    # Ability fields as lists
    ability_names = extract_indexed_fields("ability_name", request.form)
    ability_types = extract_indexed_fields("ability_type", request.form)
    ability_descriptions = extract_indexed_fields("ability_description", request.form)
    ability_additional_group_income = extract_indexed_fields(
        "ability_additional_group_income", request.form
    )
    ability_starting_skills = extract_indexed_multifields("ability_starting_skills", request.form)
    ability_starting_item_blueprints = extract_indexed_fields(
        "ability_starting_item_blueprint", request.form
    )
    ability_starting_reputation_factions = extract_indexed_fields(
        "ability_starting_reputation_faction", request.form
    )
    ability_starting_reputation_values = extract_indexed_fields(
        "ability_starting_reputation_value", request.form
    )

    if not all([name, wiki_page, body_hits_type, body_hits, death_count, permitted_factions]):
        flash("All fields are required.", "error")
        return render_template(
            "species/edit.html",
            species=species,
            BodyHitsType=BodyHitsType,
            factions=Faction.query.all(),
            factions_dict=[
                {
                    "id": faction.id,
                    "name": faction.name,
                }
                for faction in Faction.query.all()
            ],
            AbilityType=AbilityType,
            skills_list=Skill.query.all(),
            item_blueprints=ItemBlueprint.query.order_by(ItemBlueprint.name).all(),
        )

    try:
        species.name = name
        species.wiki_page = wiki_page
        species.body_hits_type_enum = body_hits_type
        species.body_hits = int(body_hits)
        species.death_count = int(death_count)
        species.permitted_factions_list = [int(faction_id) for faction_id in permitted_factions]
        species.keywords_list = request.form.getlist("keywords")

        # Remove old abilities
        for ab in list(species.abilities):
            db.session.delete(ab)
        db.session.flush()
        # Re-add abilities from form
        for i in range(len(ability_names)):
            ab_type = ability_types[i]
            ab = Ability(
                name=ability_names[i],
                description=ability_descriptions[i],
                type=ab_type,
                species=species,
            )
            if ab_type == AbilityType.STARTING_SKILLS.value:
                ab.starting_skills_list = ability_starting_skills[i]
            elif ab_type == AbilityType.SKILL_DISCOUNTS.value:
                discounts = {}
                skills = request.form.getlist(f"ability_discount_skills_{i}[]")
                value = request.form.get(f"ability_discount_value_{i}")
                if value is not None and value != "":
                    for skill_id in skills:
                        discounts[skill_id] = int(value)
                ab.skill_discounts_dict = discounts
            elif ab_type == AbilityType.GROUP_INCOME.value:
                ab.additional_group_income = int(ability_additional_group_income[i])
            elif ab_type == AbilityType.STARTING_ITEM.value:
                if ability_starting_item_blueprints[i]:
                    ab.starting_item_blueprint_id = int(ability_starting_item_blueprints[i])
            elif ab_type == AbilityType.STARTING_REPUTATION.value:
                if ability_starting_reputation_factions[i]:
                    ab.starting_reputation_faction_id = int(ability_starting_reputation_factions[i])
                if ability_starting_reputation_values[i]:
                    ab.starting_reputation_value = int(ability_starting_reputation_values[i])
            db.session.add(ab)
        db.session.commit()
        flash("Species updated successfully.", "success")
        return redirect(url_for("species.species_list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating species: {str(e)}", "error")
        return render_template(
            "species/edit.html",
            species=species,
            BodyHitsType=BodyHitsType,
            factions=Faction.query.all(),
            AbilityType=AbilityType,
            skills_list=Skill.query.all(),
        )


@species_bp.route("/new", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.species"])
def new_species():
    skills_list = Skill.query.all()
    factions = Faction.query.all()
    item_blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()

    # Convert factions to dictionaries for JSON serialization
    factions_dict = [
        {
            "id": faction.id,
            "name": faction.name,
        }
        for faction in factions
    ]

    return render_template(
        "species/edit.html",
        BodyHitsType=BodyHitsType,
        factions=factions,
        factions_dict=factions_dict,
        AbilityType=AbilityType,
        skills_list=skills_list,
        item_blueprints=item_blueprints,
    )


@species_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.species"])
def new_species_post():
    name = request.form.get("name")
    wiki_page = request.form.get("wiki_page")
    body_hits_type = request.form.get("body_hits_type")
    body_hits = request.form.get("body_hits")
    death_count = request.form.get("death_count")
    permitted_factions = request.form.getlist("permitted_factions")
    keywords = request.form.getlist("keywords")
    ability_names = extract_indexed_fields("ability_name", request.form)
    ability_types = extract_indexed_fields("ability_type", request.form)
    ability_descriptions = extract_indexed_fields("ability_description", request.form)
    ability_additional_group_income = extract_indexed_fields(
        "ability_additional_group_income", request.form
    )
    ability_starting_skills = extract_indexed_multifields("ability_starting_skills", request.form)
    ability_starting_item_blueprints = extract_indexed_fields(
        "ability_starting_item_blueprint", request.form
    )
    ability_starting_reputation_factions = extract_indexed_fields(
        "ability_starting_reputation_faction", request.form
    )
    ability_starting_reputation_values = extract_indexed_fields(
        "ability_starting_reputation_value", request.form
    )
    # Skill discounts
    if not all([name, wiki_page, body_hits_type, body_hits, death_count, permitted_factions]):
        flash("All fields are required.", "error")
        item_blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
        item_blueprints_dict = [
            {
                "id": bp.id,
                "name": bp.name,
                "full_code": bp.full_code,
                "item_type_name": bp.item_type.name if bp.item_type else "Unknown",
            }
            for bp in item_blueprints
        ]
        factions = Faction.query.all()
        factions_dict = [
            {
                "id": faction.id,
                "name": faction.name,
            }
            for faction in factions
        ]
        return render_template(
            "species/edit.html",
            BodyHitsType=BodyHitsType,
            factions=factions,
            factions_dict=factions_dict,
            AbilityType=AbilityType,
            skills_list=Skill.query.all(),
            item_blueprints=item_blueprints_dict,
        )
    try:
        species = Species(
            name=name,
            wiki_page=wiki_page,
            body_hits_type_enum=body_hits_type,
            body_hits=int(body_hits),
            death_count=int(death_count),
            # Convert faction IDs to integers
            permitted_factions_list=[int(faction_id) for faction_id in permitted_factions],
            keywords_list=keywords,
        )
        db.session.add(species)
        db.session.flush()
        for i in range(len(ability_names)):
            ab_type = ability_types[i]
            ab = Ability(
                name=ability_names[i],
                description=ability_descriptions[i],
                type=ab_type,
                species=species,
            )
            if ab_type == AbilityType.STARTING_SKILLS.value:
                ab.starting_skills_list = ability_starting_skills[i]
            elif ab_type == AbilityType.SKILL_DISCOUNTS.value:
                discounts = {}
                skills = request.form.getlist(f"ability_discount_skills_{i}[]")
                value = request.form.get(f"ability_discount_value_{i}")
                if value is not None and value != "":
                    for skill_id in skills:
                        discounts[skill_id] = int(value)
                ab.skill_discounts_dict = discounts
            elif ab_type == AbilityType.GROUP_INCOME.value:
                ab.additional_group_income = int(ability_additional_group_income[i])
            elif ab_type == AbilityType.STARTING_ITEM.value:
                if ability_starting_item_blueprints[i]:
                    ab.starting_item_blueprint_id = int(ability_starting_item_blueprints[i])
            elif ab_type == AbilityType.STARTING_REPUTATION.value:
                if ability_starting_reputation_factions[i]:
                    ab.starting_reputation_faction_id = int(ability_starting_reputation_factions[i])
                if ability_starting_reputation_values[i]:
                    ab.starting_reputation_value = int(ability_starting_reputation_values[i])
            db.session.add(ab)
        db.session.commit()
        flash("Species created successfully.", "success")
        return redirect(url_for("species.species_list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating species: {str(e)}", "error")
        skills_list = Skill.query.all()
        item_blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
        return render_template(
            "species/edit.html",
            BodyHitsType=BodyHitsType,
            factions=Faction.query.all(),
            AbilityType=AbilityType,
            skills_list=skills_list,
        )


def extract_indexed_fields(prefix, form):
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    indexed = {}
    for key in form:
        m = pattern.match(key)
        if m:
            indexed[int(m.group(1))] = form.get(key)
    return [indexed[i] for i in sorted(indexed.keys())]


def extract_indexed_multifields(prefix, form):
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)\[\]$")
    indexed = {}
    for key in form:
        m = pattern.match(key)
        if m:
            indexed[int(m.group(1))] = form.getlist(key)
    return [indexed[i] for i in sorted(indexed.keys())]
