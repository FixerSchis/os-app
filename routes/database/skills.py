import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.rule_tag import RuleTag
from models.database.skills import Skill
from models.database.species import Species
from models.enums import ScienceType
from models.extensions import db
from models.tools.character import CharacterTag
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required
from utils.skill_grouping import group_skills_for_display

skills_bp = Blueprint("skills", __name__)


def _blank_to_none(value):
    text = (value or "").strip()
    return text or None


def _form_skill_ids(values):
    return [int(value) for value in values if str(value).isdigit()]


def _optional_positive_float(value):
    text = (value or "").strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 0 else None


def _assign_condition_timing(skill):
    skill.condition_tags = RuleTag.resolve_list(request.form.getlist("condition_tags[]"))
    skill.condition_progress_rate = _optional_positive_float(
        request.form.get("condition_progress_rate")
    )


def _optional_rank_limit(value):
    text = (value or "").strip()
    if not text.isdigit():
        return None
    limit = int(text)
    if limit < 1:
        return None
    return limit


@skills_bp.route("/")
def skills_list():
    skills = Skill.query.all()
    return render_template(
        "skills/list.html",
        sections=group_skills_for_display(skills),
        can_edit=current_user.is_authenticated and current_user.has_permission("rules.skills"),
    )


@skills_bp.route("/<int:skill_id>/edit", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.skills"])
def edit_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    species_list = Species.query.all()
    skills_list = Skill.query.all()
    skill_types = Skill.get_all_skill_types()
    science_types = ScienceType.values()

    return render_template(
        "skills/edit.html",
        skill=skill,
        factions=Faction.query.all(),
        species_list=species_list,
        skills_list=skills_list,
        skill_types=skill_types,
        science_types=science_types,
        tags=CharacterTag.query.all(),
    )


@skills_bp.route("/<int:skill_id>/edit", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.skills"])
def edit_skill_post(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    name = request.form.get("name")
    description = request.form.get("description")
    skill_type = request.form.get("skill_type")
    base_cost = request.form.get("base_cost")
    can_purchase_multiple = request.form.get("can_purchase_multiple") == "on"
    cost_increases = request.form.get("cost_increases") == "on"
    required_skill_id = request.form.get("required_skill_id")
    required_species = request.form.getlist("required_species")
    required_factions = request.form.getlist("required_factions")
    required_tags = request.form.getlist("required_tags")
    adds_reputation_faction_id = request.form.get("adds_reputation_faction_id")
    adds_reputation_value = request.form.get("adds_reputation_value")

    # Handle character sheet values
    character_sheet_values = []
    form_data = request.form.to_dict()
    for key, value in form_data.items():
        if key.startswith("character_sheet_values[") and key.endswith("][id]"):
            # Extract the index from the key using regex
            match = re.match(r"character_sheet_values\[(\d+)\]\[id\]", key)
            if match:
                index = match.group(1)
            else:
                index = ""
            id_value = value
            description_value = form_data.get(f"character_sheet_values[{index}][description]", "")
            value_value = form_data.get(f"character_sheet_values[{index}][value]", "0")
            # Only add if we have an ID
            if id_value.strip():
                try:
                    value_value = int(value_value) if value_value else 0
                except ValueError:
                    value_value = 0
                character_sheet_values.append(
                    {
                        "id": id_value.strip(),
                        "description": description_value.strip(),
                        "value": value_value,
                    }
                )

    if not all([name, description, skill_type, base_cost]):
        flash("Name, description, skill type, and base cost are required.", "error")
        species_list = Species.query.all()
        skills_list = Skill.query.all()
        skill_types = Skill.get_all_skill_types()
        science_types = ScienceType.values()
        return render_template(
            "skills/edit.html",
            skill=skill,
            factions=Faction.query.all(),
            species_list=species_list,
            skills_list=skills_list,
            skill_types=skill_types,
            science_types=science_types,
            tags=CharacterTag.query.all(),
        )

    try:
        # Handle new tags
        tag_ids = []
        for tag_id in required_tags:
            if not tag_id.isdigit():  # This is a new tag
                tag = CharacterTag(name=tag_id)
                db.session.add(tag)
                db.session.flush()  # Get the new tag's ID
                tag_ids.append(str(tag.id))
            else:
                tag_ids.append(tag_id)

        skill.name = name
        skill.description = description
        skill.skill_type = skill_type
        skill.group_name = _blank_to_none(request.form.get("group_name"))
        skill.base_cost = int(base_cost)
        skill.can_purchase_multiple = can_purchase_multiple
        skill.cost_increases = cost_increases
        skill.earned_points_only = request.form.get("earned_points_only") == "on"
        skill.max_ranks = _optional_rank_limit(request.form.get("max_ranks"))
        skill.required_skill_id = int(required_skill_id) if required_skill_id else None
        skill.required_any_skills_list = _form_skill_ids(
            request.form.getlist("required_any_skills")
        )
        skill.distinct_requirements_list = _form_skill_ids(
            request.form.getlist("distinct_requirements")
        )
        skill.required_species_list = required_species
        skill.required_factions_list = required_factions
        skill.required_tags_list = tag_ids
        skill.character_sheet_values_list = character_sheet_values
        skill.adds_reputation_faction_id = (
            int(adds_reputation_faction_id) if adds_reputation_faction_id else None
        )
        skill.adds_reputation_value = int(adds_reputation_value) if adds_reputation_value else 0
        _assign_condition_timing(skill)

        db.session.commit()
        flash("Skill updated successfully.", "success")
        return redirect(url_for("skills.skills_list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating skill: {str(e)}", "error")


@skills_bp.route("/new", methods=["GET", "POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.skills"])
def new_skill():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        skill_type = request.form.get("skill_type")
        base_cost = request.form.get("base_cost")
        can_purchase_multiple = request.form.get("can_purchase_multiple") == "on"
        cost_increases = request.form.get("cost_increases") == "on"
        required_skill_id = request.form.get("required_skill_id")
        required_species = request.form.getlist("required_species")
        required_factions = request.form.getlist("required_factions")
        required_tags = request.form.getlist("required_tags")
        adds_reputation_faction_id = request.form.get("adds_reputation_faction_id")
        adds_reputation_value = request.form.get("adds_reputation_value")

        # Handle character sheet values
        character_sheet_values = []
        form_data = request.form.to_dict()
        for key, value in form_data.items():
            if key.startswith("character_sheet_values[") and key.endswith("][id]"):
                # Extract the index from the key using regex
                match = re.match(r"character_sheet_values\[(\d+)\]\[id\]", key)
                if match:
                    index = match.group(1)
                else:
                    index = ""
                id_value = value
                description_value = form_data.get(
                    f"character_sheet_values[{index}][description]", ""
                )
                value_value = form_data.get(f"character_sheet_values[{index}][value]", "0")
                # Only add if we have an ID
                if id_value.strip():
                    try:
                        value_value = int(value_value) if value_value else 0
                    except ValueError:
                        value_value = 0
                    character_sheet_values.append(
                        {
                            "id": id_value.strip(),
                            "description": description_value.strip(),
                            "value": value_value,
                        }
                    )

        if not all([name, description, skill_type, base_cost]):
            flash("Name, description, skill type, and base cost are required.", "error")
            species_list = Species.query.all()
            skills_list = Skill.query.all()
            skill_types = Skill.get_all_skill_types()
            science_types = ScienceType.values()
            return render_template(
                "skills/edit.html",
                skill=None,
                factions=Faction.query.all(),
                species_list=species_list,
                skills_list=skills_list,
                skill_types=skill_types,
                science_types=science_types,
                tags=CharacterTag.query.all(),
            )

        try:
            # Handle new tags
            tag_ids = []
            for tag_id in required_tags:
                if not tag_id.isdigit():  # This is a new tag
                    tag = CharacterTag(name=tag_id)
                    db.session.add(tag)
                    db.session.flush()  # Get the new tag's ID
                    tag_ids.append(str(tag.id))
                else:
                    tag_ids.append(tag_id)

            skill = Skill(
                name=name,
                description=description,
                skill_type=skill_type,
                group_name=_blank_to_none(request.form.get("group_name")),
                base_cost=int(base_cost),
                can_purchase_multiple=can_purchase_multiple,
                cost_increases=cost_increases,
                earned_points_only=request.form.get("earned_points_only") == "on",
                max_ranks=_optional_rank_limit(request.form.get("max_ranks")),
                required_skill_id=int(required_skill_id) if required_skill_id else None,
                required_any_skills_list=_form_skill_ids(
                    request.form.getlist("required_any_skills")
                ),
                distinct_requirements_list=_form_skill_ids(
                    request.form.getlist("distinct_requirements")
                ),
                required_species_list=required_species,
                required_factions_list=required_factions,
                required_tags_list=tag_ids,
                character_sheet_values_list=character_sheet_values,
                adds_reputation_faction_id=(
                    int(adds_reputation_faction_id) if adds_reputation_faction_id else None
                ),
                adds_reputation_value=int(adds_reputation_value) if adds_reputation_value else 0,
            )
            db.session.add(skill)
            _assign_condition_timing(skill)
            db.session.commit()
            flash("Skill created successfully.", "success")
            return redirect(url_for("skills.skills_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating skill: {str(e)}", "error")

    species_list = Species.query.all()
    skills_list = Skill.query.all()
    skill_types = Skill.get_all_skill_types()
    science_types = ScienceType.values()

    return render_template(
        "skills/edit.html",
        factions=Faction.query.all(),
        species_list=species_list,
        skills_list=skills_list,
        skill_types=skill_types,
        science_types=science_types,
        tags=CharacterTag.query.all(),
    )
