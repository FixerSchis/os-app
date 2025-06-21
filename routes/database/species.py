import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.enums import AbilityType, BodyHitsType, Role
from models.extensions import db
from models.tools.character import Character
from utils.decorators import email_verified_required

species_bp = Blueprint("species", __name__)


@species_bp.route("/")
def species_list():
    # Get all species
    species = Species.query.all()
    factions = {f.id: f.name for f in Faction.query.all()}

    # Helper to get the first permitted faction's name for sorting
    def get_first_faction_name(species):
        if species.permitted_factions_list:
            faction = Faction.query.get(species.permitted_factions_list[0])
            return faction.name if faction else ""
        return ""

    # If user is not rules team, filter species
    if not current_user.is_authenticated or not current_user.has_role(Role.RULES_TEAM.value):
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
                    faction = Faction.query.get(faction_id)
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
        can_edit=current_user.is_authenticated and current_user.has_role(Role.RULES_TEAM.value),
    )


@species_bp.route("/<int:species_id>/edit", methods=["GET"])
@login_required
@email_verified_required
def edit_species(species_id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("index"))

    species = Species.query.get_or_404(species_id)
    skills_list = Skill.query.all()
    factions = Faction.query.all()
    return render_template(
        "species/edit.html",
        species=species,
        BodyHitsType=BodyHitsType,
        factions=factions,
        AbilityType=AbilityType,
        skills_list=skills_list,
    )


@species_bp.route("/<int:species_id>/edit", methods=["POST"])
@login_required
@email_verified_required
def edit_species_post(species_id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("index"))

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
    ability_starting_skills = extract_indexed_multifields("ability_starting_skills", request.form)

    if not all([name, wiki_page, body_hits_type, body_hits, death_count, permitted_factions]):
        flash("All fields are required.", "error")
        return render_template(
            "species/edit.html",
            species=species,
            BodyHitsType=BodyHitsType,
            factions=Faction.query.all(),
            AbilityType=AbilityType,
            skills_list=Skill.query.all(),
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
def new_species():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("index"))

    skills_list = Skill.query.all()
    return render_template(
        "species/edit.html",
        BodyHitsType=BodyHitsType,
        factions=Faction.query.all(),
        AbilityType=AbilityType,
        skills_list=skills_list,
    )


@species_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
def new_species_post():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("index"))
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
    ability_starting_skills = extract_indexed_multifields("ability_starting_skills", request.form)
    # Skill discounts
    if not all([name, wiki_page, body_hits_type, body_hits, death_count, permitted_factions]):
        flash("All fields are required.", "error")
        skills_list = Skill.query.all()
        return render_template(
            "species/edit.html",
            BodyHitsType=BodyHitsType,
            factions=Faction.query.all(),
            AbilityType=AbilityType,
            skills_list=skills_list,
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
            db.session.add(ab)
        db.session.commit()
        flash("Species created successfully.", "success")
        return redirect(url_for("species.species_list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating species: {str(e)}", "error")
        skills_list = Skill.query.all()
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
