import base64

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.conditions import Condition
from models.database.cybernetic import (
    CharacterCybernetic,
    Cybernetic,
    implants_by_ids,
    slot_conflict_message,
)
from models.database.faction import Faction
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.sample import Sample
from models.database.species import Ability, Species
from models.enums import AbilityType, CharacterAuditAction, PrintTemplateType
from models.extensions import db
from models.tools.character import (
    Character,
    CharacterAuditLog,
    CharacterBackground,
    CharacterCondition,
    CharacterStatus,
    CharacterTag,
    assign_character_id,
    format_event_count,
)
from models.tools.character_inventory import CharacterItem
from models.tools.group import GroupBackground
from models.tools.print_template import PrintTemplate
from models.tools.research import CharacterResearch
from models.tools.user import User
from utils import generate_qr_code, generate_web_qr_code
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required
from utils.skill_pairs import apply_skill_pair_grants
from utils.starting_conditions import (
    apply_starting_conditions,
    starting_condition_catalogue,
    validate_starting_condition_stages,
)
from utils.starting_skills import (
    apply_starting_skills,
    choice_catalogue,
    validate_starting_skill_picks,
)


def _posted_character_abilities():
    """Read character-ability rows posted by the game team."""
    rows = []
    index = 0
    while (
        f"character_ability_name_{index}" in request.form
        or f"character_ability_description_{index}" in request.form
    ):
        name = (request.form.get(f"character_ability_name_{index}") or "").strip()
        description = (request.form.get(f"character_ability_description_{index}") or "").strip()
        index += 1
        if not name and not description:
            continue
        if not name or not description:
            return None, "Each character ability needs a name and a description."
        if len(name) > 100:
            return None, "Character ability names must be 100 characters or fewer."
        rows.append((name, description))
    return rows, None


def _replace_character_abilities(character, rows):
    """Store the posted abilities on this character. Returns an audit note when they change."""
    previous = [(ability.name, ability.description) for ability in character.abilities]
    if previous == rows:
        return None
    for ability in list(character.abilities):
        db.session.delete(ability)
    db.session.flush()
    for name, description in rows:
        db.session.add(
            Ability(
                character_id=character.id,
                name=name,
                description=description,
                type=AbilityType.GENERIC,
            )
        )
    if rows:
        names = ", ".join(name for name, _description in rows)
        return f"Character abilities set to: {names}"
    return "Character abilities removed"


def _edit_redirect(character, admin_context):
    redirect_url = url_for("characters.edit", character_id=character.id)
    if admin_context:
        redirect_url += "?admin_context=1"
    return redirect(redirect_url)


def _assign_new_character_implants(character, raw_ids):
    """Install the submitted implants on a new character, or return an error."""
    implants = implants_by_ids(raw_ids)
    conflict = slot_conflict_message(implants)
    if conflict:
        return conflict
    for implant in implants:
        db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=implant.id))
    if implants:
        db.session.commit()
    return None


def can_edit_character(user, args, kwargs):
    """Check if a user can edit a specific character."""
    if not user or not user.is_authenticated:
        return False

    # Admin users can edit any character
    if user.has_permission("character.edit_all"):
        return True

    # Regular users can only edit their own characters
    character_id = kwargs.get("character_id")
    if character_id:
        character = Character.query.get(character_id)
        if character and character.user_id == user.id:
            return True

    return False


def _posted_base_character_points(user):
    """Parse an admin base-character-points field.

    Returns (points, error_message). points is None when the field was not submitted
    or the user cannot edit every character.
    """
    if "base_character_points" not in request.form:
        return None, None
    if not user.has_permission("character.edit_all"):
        return None, None
    raw = (request.form.get("base_character_points") or "").strip()
    try:
        points = int(raw)
    except ValueError:
        return None, "Base character points must be a whole number."
    if points < 0:
        return None, "Base character points cannot be negative."
    return points, None


def _posted_earned_character_points(user):
    """Parse the owner's earned character points pool from the character form.

    Returns (points, error_message). points is None when the field was not submitted
    or the user cannot edit users.
    """
    if "earned_character_points" not in request.form:
        return None, None
    if not user.has_permission("user.edit"):
        return None, None
    raw = (request.form.get("earned_character_points") or "").strip()
    try:
        points = float(raw)
    except ValueError:
        return None, "Earned character points must be a number."
    if points < 0:
        return None, "Earned character points cannot be negative."
    if points * 2 != int(points * 2):
        return None, "Earned character points must be a whole or half point."
    return points, None


characters_bp = Blueprint("characters", __name__)


@characters_bp.context_processor
def inject_starting_skill_catalogue():
    return {
        "starting_skill_catalogue": choice_catalogue(),
        "starting_condition_catalogue": starting_condition_catalogue(),
    }


@characters_bp.route("/")
@login_required
@email_verified_required
def character_list():
    characters = []
    if current_user.has_permission("character.view_all"):
        # Admin view: sort by user_id, then character_id
        characters = (
            Character.query.options(
                db.joinedload(Character.group),
                db.joinedload(Character.faction),
                db.joinedload(Character.species),
            )
            .order_by(Character.user_id, Character.character_id)
            .all()
        )
    else:
        # User view: sort by character_id for their own characters
        characters = (
            Character.query.options(
                db.joinedload(Character.group),
                db.joinedload(Character.faction),
                db.joinedload(Character.species),
            )
            .filter_by(user_id=current_user.id)
            .order_by(Character.character_id)
            .all()
        )

    return render_template(
        "characters/list.html",
        characters=characters,
        CharacterStatus=CharacterStatus,
        Faction=Faction,
    )


@characters_bp.route("/new", methods=["GET"])
@login_required
@email_verified_required
def create_character():
    admin_context = request.args.get("admin_context") == "1"
    factions = Faction.query.all()
    species_list = Species.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    return render_template(
        "characters/edit.html",
        admin_context=admin_context,
        factions=factions,
        species_list=species_list,
        all_cybernetics=all_cybernetics,
    )


@characters_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
def create_character_post():
    admin_context = request.form.get("admin_context") == "1"
    name = request.form.get("name")
    pronouns_subject = request.form.get("pronouns_subject")
    pronouns_object = request.form.get("pronouns_object")
    faction_id = request.form.get("faction")
    species_id = request.form.get("species_id")
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    if not name or not faction_id or not species_id:
        flash("Character name, faction, and species are required", "error")
        return render_template(
            "characters/edit.html",
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    faction = db.session.get(Faction, faction_id)
    if not faction:
        flash("Invalid faction selected", "error")
        return render_template(
            "characters/edit.html",
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    if not faction.allow_player_characters and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You do not have permission to select this faction.", "error")
        return render_template(
            "characters/edit.html",
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    # Validate species is permitted for faction
    if not (current_user.has_permission("character.edit_all")):
        species = db.session.get(Species, species_id)
        if not species or faction.id not in species.permitted_factions_list:
            flash("Selected species is not permitted for the chosen faction.", "error")
            return render_template(
                "characters/edit.html",
                admin_context=admin_context,
                factions=factions,
                species_list=species_list,
                all_cybernetics=all_cybernetics,
            )

    species = db.session.get(Species, species_id)
    pick_error = validate_starting_skill_picks(
        species, request.form.getlist("starting_skill_pick")
    ) or validate_starting_condition_stages(species, request.form)
    if pick_error:
        flash(pick_error, "error")
        return render_template(
            "characters/edit.html",
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    base_character_points = 10
    posted_points, points_error = _posted_base_character_points(current_user)
    if points_error:
        flash(points_error, "error")
        return render_template(
            "characters/edit.html",
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )
    if posted_points is not None:
        base_character_points = posted_points

    # Get background fields from form
    background = request.form.get("background", "").strip()
    goals = request.form.get("goals", "").strip()
    concept = request.form.get("concept", "").strip()

    character = Character(
        user_id=current_user.id,
        name=name,
        pronouns_subject=pronouns_subject,
        pronouns_object=pronouns_object,
        status=CharacterStatus.DEVELOPING.value,
        faction_id=faction.id,
        species_id=int(species_id),
        base_character_points=base_character_points,
        background=background,
        goals=goals,
        concept=concept,
    )
    db.session.add(character)
    db.session.flush()
    apply_starting_skills(
        character, species, current_user, request.form.getlist("starting_skill_pick")
    )
    apply_skill_pair_grants(character, species, current_user)
    condition_notes = apply_starting_conditions(character, species, request.form)
    db.session.commit()

    # Handle background review system for character creation
    if background or goals or concept:
        # Character owner added background during creation - mark for review
        char_background = CharacterBackground.get_or_create_for_character(character.id)
        char_background.background = background
        char_background.goals = goals
        char_background.concept = concept
        char_background.mark_for_review()
        db.session.add(char_background)
        db.session.commit()

    # Audit log for creation
    created = "Character created"
    if condition_notes:
        created += ". " + "; ".join(condition_notes)
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.CREATE.value,
        changes=created,
    )
    db.session.add(audit)
    db.session.commit()
    if current_user.has_permission("character.edit_all"):
        implant_error = _assign_new_character_implants(
            character, request.form.getlist("cybernetic_ids[]")
        )
        if implant_error:
            flash(implant_error, "error")
    flash("Character created successfully!", "success")
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/edit", methods=["GET"])
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You don't have permission to edit this character.",
        "flash_category": "error",
    },
)
def edit(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can edit this character
    if not character.can_edit(current_user):
        flash("You don't have permission to edit this character.", "error")
        return redirect(url_for("characters.character_list"))

    admin_context = request.args.get("admin_context") == "1"
    user_id = character.user_id if admin_context else None
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()

    # Serialize all_conditions as a list of dicts for JSON
    all_conditions = []
    for cond in Condition.query.order_by(Condition.name).all():
        all_conditions.append(
            {
                "id": cond.id,
                "name": cond.name,
                "stages": [
                    {
                        "stage_number": stage.stage_number,
                        "rp_effect": stage.rp_effect,
                        "diagnosis": stage.diagnosis,
                        "cure": stage.cure,
                        "duration": stage.duration,
                    }
                    for stage in sorted(cond.stages, key=lambda s: s.stage_number)
                ],
            }
        )
    # Get research projects for this character
    research_projects = CharacterResearch.query.filter_by(character_id=character.id).all()
    for r in research_projects:
        r.current_stage_progress = None
        if r.current_stage_id is not None:
            r.current_stage_progress = next(
                (p for p in r.progress if p.stage_id == r.current_stage_id), None
            )

    # Get character inventory items
    inventory_items = (
        CharacterItem.query.filter_by(character_id=character.id)
        .join(Item)
        .join(ItemBlueprint)
        .order_by(ItemBlueprint.name)
        .all()
    )

    # Get all available items for assignment (admin only)
    available_items = []
    if current_user.has_permission("character.edit_all"):
        all_items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()
        assigned_item_ids = {ci.item_id for ci in inventory_items}
        available_items = [item for item in all_items if item.id not in assigned_item_ids]

    # Get all item blueprints for creating new items (admin only)
    item_blueprints = []
    if current_user.has_permission("character.edit_all"):
        item_blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()

    # Get character samples and available samples for assignment (admin only)
    character_samples = character.samples.order_by(Sample.name).all()
    available_samples = []
    if current_user.has_permission("character.edit_all"):
        all_samples = Sample.query.order_by(Sample.name).all()
        assigned_sample_ids = {s.id for s in character_samples}
        available_samples = [
            sample for sample in all_samples if sample.id not in assigned_sample_ids
        ]

    return render_template(
        "characters/edit.html",
        character=character,
        admin_context=admin_context,
        user_id=user_id,
        factions=factions,
        species_list=species_list,
        all_conditions=all_conditions,
        all_cybernetics=all_cybernetics,
        research_projects=research_projects,
        inventory_items=inventory_items,
        available_items=available_items,
        item_blueprints=item_blueprints,
        character_samples=character_samples,
        available_samples=available_samples,
    )


@characters_bp.route("/<int:character_id>/edit", methods=["POST"])
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You don't have permission to edit this character.",
        "flash_category": "error",
    },
)
def edit_post(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can edit this character
    if not character.can_edit(current_user):
        flash("You don't have permission to edit this character.", "error")
        return redirect(url_for("characters.character_list"))

    admin_context = request.form.get("admin_context") == "1"

    name = request.form.get("name")
    pronouns_subject = request.form.get("pronouns_subject")
    pronouns_object = request.form.get("pronouns_object")
    faction_id = request.form.get("faction")
    species_id = request.form.get("species_id")
    species_list = Species.query.all()
    factions = Faction.query.all()

    if not name or not faction_id or not species_id:
        flash("Character name, faction, and species are required", "error")
        return render_template(
            "characters/edit.html",
            character=character,
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
        )

    faction = db.session.get(Faction, faction_id)
    if not faction:
        flash("Invalid faction selected", "error")
        return render_template(
            "characters/edit.html",
            character=character,
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
        )

    if not faction.allow_player_characters and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You do not have permission to select this faction.", "error")
        return render_template(
            "characters/edit.html",
            character=character,
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
        )

    # Validate species is permitted for faction
    if not (current_user.has_permission("character.edit_all")):
        species = db.session.get(Species, species_id)
        if not species or faction.id not in species.permitted_factions_list:
            flash("Selected species is not permitted for the chosen faction.", "error")
            return render_template(
                "characters/edit.html",
                character=character,
                admin_context=admin_context,
                factions=factions,
                species_list=species_list,
            )

    species = db.session.get(Species, species_id)
    choosing_starting_conditions = character.status == CharacterStatus.DEVELOPING.value
    pick_error = validate_starting_skill_picks(species, request.form.getlist("starting_skill_pick"))
    if not pick_error and choosing_starting_conditions:
        pick_error = validate_starting_condition_stages(species, request.form)
    if pick_error:
        flash(pick_error, "error")
        return render_template(
            "characters/edit.html",
            character=character,
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
        )

    ability_rows = None
    if current_user.has_permission("character.edit_all"):
        ability_rows, ability_error = _posted_character_abilities()
        if ability_error:
            flash(ability_error, "error")
            return _edit_redirect(character, admin_context)

    posted_points, points_error = _posted_base_character_points(current_user)
    posted_earned, earned_error = _posted_earned_character_points(current_user)
    points_error = points_error or earned_error
    if points_error:
        flash(points_error, "error")
        redirect_url = url_for("characters.edit", character_id=character.id)
        if admin_context:
            redirect_url += "?admin_context=1"
        return redirect(redirect_url)

    selected_implants = []
    if current_user.has_permission("character.edit_all"):
        selected_implants = implants_by_ids(request.form.getlist("cybernetic_ids[]"))
        conflict = slot_conflict_message(selected_implants)
        if conflict:
            flash(conflict, "error")
            return _edit_redirect(character, admin_context)

    # Track basic information changes for EDIT action
    basic_changes = []

    if character.name != name:
        basic_changes.append(f"Name changed from '{character.name}' to '{name}'")
    if character.pronouns_subject != pronouns_subject:
        basic_changes.append(
            f"Pronouns (subject) changed from '{character.pronouns_subject}' "
            f"to '{pronouns_subject}'"
        )
    if character.pronouns_object != pronouns_object:
        basic_changes.append(
            f"Pronouns (object) changed from '{character.pronouns_object}' to '{pronouns_object}'"
        )
    if character.faction_id != int(faction_id):
        old_faction = Faction.query.get(character.faction_id)
        new_faction = Faction.query.get(faction_id)
        old_name = old_faction.name if old_faction else "None"
        new_name = new_faction.name if new_faction else "None"
        basic_changes.append(f"Faction changed from '{old_name}' to '{new_name}'")
    if character.species_id != int(species_id):
        old_species = Species.query.get(character.species_id)
        new_species = Species.query.get(species_id)
        old_name = old_species.name if old_species else "None"
        new_name = new_species.name if new_species else "None"
        basic_changes.append(f"Species changed from '{old_name}' to '{new_name}'")
    if posted_points is not None and character.base_character_points != posted_points:
        basic_changes.append(
            f"Base character points changed from '{character.base_character_points}' "
            f"to '{posted_points}'"
        )
    owner = character.user
    if posted_earned is not None and owner.character_points != posted_earned:
        basic_changes.append(
            f"Player earned character points changed from '{owner.character_points:g}' "
            f"to '{posted_earned:g}'"
        )
        owner.character_points = posted_earned

    character.name = name
    character.pronouns_subject = pronouns_subject
    character.pronouns_object = pronouns_object
    character.faction_id = faction_id
    character.species_id = species_id
    if posted_points is not None:
        character.base_character_points = posted_points

    # Handle background fields
    background = request.form.get("background", "")
    goals = request.form.get("goals", "")
    concept = request.form.get("concept", "")

    # Track background changes
    background_changes = []
    if character.background != background:
        background_changes.append("Background updated")
    if character.goals != goals:
        background_changes.append("Goals updated")
    if character.concept != concept:
        background_changes.append("Concept updated")

    character.background = background
    character.goals = goals
    character.concept = concept

    # Handle background review system
    if background_changes:
        # Character owner edited background - mark for review
        char_background = CharacterBackground.get_or_create_for_character(character.id)
        char_background.background = background
        char_background.goals = goals
        char_background.concept = concept
        char_background.mark_for_review()
        db.session.add(char_background)

    # Track condition changes for CONDITION_CHANGE action
    condition_changes = []
    cybernetic_changes = []  # Initialize cybernetic_changes outside the if block
    sample_changes = []  # Initialize sample_changes outside the if block

    if current_user.has_permission("character.edit_all"):
        if ability_rows is not None:
            ability_change = _replace_character_abilities(character, ability_rows)
            if ability_change:
                db.session.add(
                    CharacterAuditLog(
                        character_id=character.id,
                        editor_user_id=current_user.id,
                        action=CharacterAuditAction.EDIT.value,
                        changes=ability_change,
                    )
                )
        # Remove condition
        remove_condition_id = request.form.get("remove_condition")
        if remove_condition_id:
            cc = CharacterCondition.query.filter_by(
                id=remove_condition_id, character_id=character.id
            ).first()
            if cc:
                condition_changes.append(f"Condition removed: {cc.condition.name}")
                db.session.delete(cc)
                db.session.commit()
                flash("Condition removed.", "success")
                redirect_url = url_for("characters.edit", character_id=character.id)
                if admin_context:
                    redirect_url += "?admin_context=1"
                return redirect(redirect_url)
        # Add condition
        if request.form.get("add_condition"):
            cond_id = request.form.get("add_condition_id")
            if cond_id:
                exists = CharacterCondition.query.filter_by(
                    character_id=character.id, condition_id=cond_id
                ).first()
                if not exists:
                    condition = Condition.query.get(cond_id)
                    if condition:
                        # Get the duration of the first stage (stage 1)
                        first_stage = next(
                            (stage for stage in condition.stages if stage.stage_number == 1), None
                        )
                        initial_duration = first_stage.duration if first_stage else 0

                        condition_changes.append(f"Condition added: {condition.name}")
                        new_cc = CharacterCondition(
                            character_id=character.id,
                            condition_id=cond_id,
                            current_stage=1,  # Default to stage 1
                            current_duration=initial_duration,  # Use first stage duration
                        )
                        db.session.add(new_cc)
                        db.session.commit()
                        flash("Condition added.", "success")
                        redirect_url = url_for("characters.edit", character_id=character.id)
                        if admin_context:
                            redirect_url += "?admin_context=1"
                        return redirect(redirect_url)
                    else:
                        flash("Condition not found.", "error")
                else:
                    flash("Condition already exists for this character.", "error")
            else:
                flash("Please select a condition.", "error")
        # Update existing conditions
        for cc in character.active_conditions:
            stage_val = request.form.get(f"condition_stage_{cc.id}")
            duration_val = request.form.get(f"condition_duration_{cc.id}")
            if stage_val is not None and int(stage_val) != cc.current_stage:
                condition_changes.append(
                    f"Condition {cc.condition.name} stage changed from {cc.current_stage} "
                    f"to {stage_val}"
                )
                cc.current_stage = int(stage_val)
            posted_duration = None
            if duration_val is not None and str(duration_val).strip() != "":
                try:
                    posted_duration = float(duration_val)
                except ValueError:
                    posted_duration = None
            if posted_duration is not None and posted_duration != float(cc.current_duration or 0):
                condition_changes.append(
                    f"Condition {cc.condition.name} duration changed from "
                    f"{format_event_count(cc.current_duration)} to "
                    f"{format_event_count(posted_duration)}"
                )
                cc.current_duration = posted_duration

        # Track cybernetic changes for CYBERNETICS_CHANGE action

        # Update cybernetics if user_admin
        current_cyber_ids = {cc.cybernetic_id for cc in character.cybernetics_link}
        new_cyber_ids = {implant.id for implant in selected_implants}

        # Track cybernetic changes
        added_cybernetics = new_cyber_ids - current_cyber_ids
        removed_cybernetics = current_cyber_ids - new_cyber_ids

        for cyber_id in added_cybernetics:
            cyber = Cybernetic.query.get(cyber_id)
            if cyber:
                cybernetic_changes.append(f"Implant added: {cyber.name}")

        for cyber_id in removed_cybernetics:
            cyber = Cybernetic.query.get(cyber_id)
            if cyber:
                cybernetic_changes.append(f"Implant removed: {cyber.name}")

        # Remove all current
        CharacterCybernetic.query.filter_by(character_id=character.id).delete()
        # Add new
        for implant in selected_implants:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=implant.id))

    # Update faction reputations if user is admin (handled by set_reputation method)
    if current_user.has_permission("character.edit_all"):
        for faction in factions:
            reputation = request.form.get(f"reputation_{faction.id}")
            if reputation is not None:
                try:
                    reputation_value = int(reputation)
                    character.set_reputation(faction.id, reputation_value, current_user.id)
                except ValueError:
                    pass
        # Handle tag updates (no audit logging for tags as requested)
        tag_ids = request.form.getlist("tag_ids[]")
        current_tags = set(tag.id for tag in character.tags)
        new_tags = set()
        for tag_id in tag_ids:
            if tag_id.isdigit():
                new_tags.add(int(tag_id))
            else:
                tag = CharacterTag.query.filter_by(name=tag_id).first()
                if not tag:
                    tag = CharacterTag(name=tag_id)
                    db.session.add(tag)
                    db.session.flush()
                new_tags.add(tag.id)
        for tag_id in current_tags - new_tags:
            tag = db.session.get(CharacterTag, tag_id)
            if tag:
                character.tags.remove(tag)
        for tag_id in new_tags - current_tags:
            tag = db.session.get(CharacterTag, tag_id)
            if tag and tag not in character.tags:
                character.tags.append(tag)

        # Handle sample management (admin only)

        # Remove samples
        remove_sample_id = request.form.get("remove_sample")
        if remove_sample_id:
            sample = Sample.query.get(remove_sample_id)
            if sample and sample in character.samples:
                sample_changes.append(f"Sample removed: {sample.name}")
                character.samples.remove(sample)
                db.session.commit()
                flash("Sample removed.", "success")
                redirect_url = url_for("characters.edit", character_id=character.id)
                if admin_context:
                    redirect_url += "?admin_context=1"
                return redirect(redirect_url)

        # Add samples
        if request.form.get("add_sample"):
            sample_id = request.form.get("add_sample_id")
            if sample_id:
                sample = Sample.query.get(sample_id)
                if sample and sample not in character.samples:
                    # Remove sample from any other characters first
                    for other_character in Character.query.all():
                        if other_character != character and sample in other_character.samples:
                            other_character.samples.remove(sample)
                            sample_changes.append(
                                f"Sample removed from {other_character.name}: {sample.name}"
                            )

                    # Add sample to current character
                    sample_changes.append(f"Sample added: {sample.name}")
                    character.samples.append(sample)
                    db.session.commit()
                    flash("Sample added.", "success")
                    redirect_url = url_for("characters.edit", character_id=character.id)
                    if admin_context:
                        redirect_url += "?admin_context=1"
                    return redirect(redirect_url)
                else:
                    flash("Sample not found or already assigned to character.", "error")
            else:
                flash("Please select a sample.", "error")

    # Create separate audit logs for different types of changes
    if basic_changes:
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.EDIT.value,
            changes="; ".join(basic_changes),
        )
        db.session.add(audit)

    if condition_changes:
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.CONDITION_CHANGE.value,
            changes="; ".join(condition_changes),
        )
        db.session.add(audit)

    if cybernetic_changes:
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.CYBERNETICS_CHANGE.value,
            changes="; ".join(cybernetic_changes),
        )
        db.session.add(audit)

    if sample_changes:
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.EDIT.value,
            changes="; ".join(sample_changes),
        )
        db.session.add(audit)

    if background_changes:
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.EDIT.value,
            changes="; ".join(background_changes),
        )
        db.session.add(audit)

    apply_starting_skills(
        character, species, current_user, request.form.getlist("starting_skill_pick")
    )
    apply_skill_pair_grants(character, species, current_user)
    if choosing_starting_conditions:
        condition_notes = apply_starting_conditions(character, species, request.form)
        if condition_notes:
            db.session.add(
                CharacterAuditLog(
                    character_id=character.id,
                    editor_user_id=current_user.id,
                    action=CharacterAuditAction.CONDITION_CHANGE.value,
                    changes="; ".join(condition_notes),
                )
            )
    db.session.commit()
    flash("Character updated successfully")
    redirect_url = url_for("characters.edit", character_id=character.id)
    if admin_context:
        redirect_url += "?admin_context=1"
    return redirect(redirect_url)


@characters_bp.route("/<int:character_id>/retire", methods=["POST"])
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You can only retire your own characters.",
        "flash_category": "error",
    },
)
def retire_character(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can retire this character
    if character.user_id != current_user.id and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You can only retire your own characters.", "error")
        return redirect(url_for("characters.character_list"))

    admin_context = request.form.get("admin_context") == "1"
    if character.status != CharacterStatus.ACTIVE.value:
        flash("Only active characters can be retired.", "error")
        return redirect(url_for("characters.character_list"))
    character.status = CharacterStatus.RETIRED.value
    db.session.commit()
    # Audit log for status change
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes="Retired character",
    )
    db.session.add(audit)
    db.session.commit()
    flash("Character retired.", "success")
    if admin_context:
        user = User.query.filter_by(id=character.user_id).first()
        if user:
            return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/kill", methods=["POST"])
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You can only kill your own characters.",
        "flash_category": "error",
    },
)
def kill_character(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can kill this character
    if character.user_id != current_user.id and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You can only kill your own characters.", "error")
        return redirect(url_for("characters.character_list"))

    admin_context = request.form.get("admin_context") == "1"
    if character.status != CharacterStatus.ACTIVE.value:
        flash("Only active characters can be killed.", "error")
        return redirect(url_for("characters.character_list"))
    character.status = CharacterStatus.DEAD.value
    db.session.commit()
    # Audit log for status change
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes="Character marked as dead",
    )
    db.session.add(audit)
    db.session.commit()
    flash("Character marked as dead.", "success")
    if admin_context:
        user = User.query.filter_by(id=character.user_id).first()
        if user:
            return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/restore", methods=["POST"])
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You can only restore your own characters.",
        "flash_category": "error",
    },
)
def restore_character(character_id):
    """Restores a retired character to active status."""
    character = Character.query.get_or_404(character_id)

    # Check if user can restore this character
    if character.user_id != current_user.id and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You can only restore your own characters.", "error")
        return redirect(url_for("characters.character_list"))

    if character.status not in [
        CharacterStatus.RETIRED.value,
        CharacterStatus.DEAD.value,
    ]:
        flash("Only retired or dead characters can be restored.", "error")
        return redirect(url_for("characters.character_list"))

    user = User.query.filter_by(id=character.user_id).first()
    if not user:
        flash("Could not find character owner.", "error")
        return redirect(url_for("characters.character_list"))

    if user.has_active_character() and not current_user.has_permission("character.edit_all"):
        flash("This user already has an active character.", "danger")
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))

    if character.character_id is None:
        character.character_id = assign_character_id(character.user_id)

    character.status = CharacterStatus.ACTIVE.value
    db.session.commit()
    # Audit log for status change
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes="Restored character.",
    )
    db.session.add(audit)
    db.session.commit()
    flash("Character restored.", "success")
    admin_context = request.form.get("admin_context") == "1"
    if admin_context:
        return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/delete", methods=["POST"])
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You can only delete your own characters.",
        "flash_category": "error",
    },
)
def delete_character(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can delete this character
    if character.user_id != current_user.id and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You can only delete your own characters.", "error")
        return redirect(url_for("characters.character_list"))

    # Delete all related records before deleting the character
    # Character audit logs
    for audit_log in CharacterAuditLog.query.filter_by(character_id=character.id).all():
        db.session.delete(audit_log)

    # Character backgrounds
    for background in CharacterBackground.query.filter_by(character_id=character.id).all():
        db.session.delete(background)

    # Character skills
    for skill in character.skills:
        db.session.delete(skill)

    # Character reputations
    for reputation in character.reputations:
        db.session.delete(reputation)

    # Character conditions
    for condition in character.active_conditions:
        db.session.delete(condition)

    # Character cybernetics
    for cybernetic in character.cybernetics_link:
        db.session.delete(cybernetic)

    # Downtime packs
    for pack in character.downtime_packs:
        db.session.delete(pack)

    # Event tickets
    for ticket in character.event_tickets:
        db.session.delete(ticket)

    # Character inventory items
    for item in character.inventory_items:
        db.session.delete(item)

    # Character cybernetics (from database models)
    for cybernetic in CharacterCybernetic.query.filter_by(character_id=character.id).all():
        db.session.delete(cybernetic)

    # Finally delete the character
    db.session.delete(character)
    db.session.commit()
    flash("Character deleted.", "success")
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/activate", methods=["POST"])
@login_required
@email_verified_required
def activate_character(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can activate this character
    if character.user_id != current_user.id and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You can only activate your own characters.", "error")
        return redirect(url_for("characters.character_list"))

    if character.status != CharacterStatus.DEVELOPING.value:
        flash("Only developing characters can be activated.", "error")
        return redirect(url_for("characters.character_list"))

    if current_user.has_active_character() and not current_user.has_permission(
        "character.edit_all"
    ):
        if current_user.get_active_character().id != character.id:
            flash("You already have an active character.", "danger")
            return redirect(url_for("characters.character_list"))

    user = User.query.filter_by(id=character.user_id).first()
    if not user:
        flash("Could not find character owner.", "error")
        return redirect(url_for("characters.character_list"))

    earned_spend = character.earned_points_spent()
    if earned_spend > 0 and not user.can_spend_character_points(earned_spend):
        flash("Not enough character points to activate character.", "error")
        return redirect(url_for("characters.character_list"))

    if character.character_id is None:
        character.character_id = assign_character_id(character.user_id)

    if earned_spend > 0:
        user.spend_character_points(earned_spend)

    character.status = CharacterStatus.ACTIVE.value

    # Handle starting items from species abilities
    if character.species:
        for ability in character.species.abilities:
            if ability.type == AbilityType.STARTING_ITEM and ability.starting_item_blueprint_id:
                # Create item from blueprint
                blueprint = ItemBlueprint.query.get(ability.starting_item_blueprint_id)
                if blueprint:
                    # Get the next item ID for this blueprint
                    max_item = (
                        Item.query.filter_by(blueprint_id=blueprint.id)
                        .order_by(Item.item_id.desc())
                        .first()
                    )
                    next_item_id = (max_item.item_id + 1) if max_item else 1

                    # Create the item
                    item = Item(
                        blueprint_id=blueprint.id,
                        item_id=next_item_id,
                        expiry=None,  # Starting items don't expire
                    )
                    db.session.add(item)
                    db.session.flush()

                    # Add item to character's inventory
                    character_item = CharacterItem(
                        character_id=character.id,
                        item_id=item.id,
                        assigned_by_user_id=current_user.id,
                    )
                    db.session.add(character_item)

                    # Add audit log for starting item
                    item_audit = CharacterAuditLog(
                        character_id=character.id,
                        editor_user_id=current_user.id,
                        action=CharacterAuditAction.STATUS_CHANGE.value,
                        changes=f"Starting item added: {blueprint.display_name} ({item.full_code})",
                    )
                    db.session.add(item_audit)

    # Handle reputation from skills and species abilities
    reputation_changes = []

    # Add reputation from skills
    for character_skill in character.skills:
        skill = character_skill.skill
        if skill.adds_reputation_faction_id and skill.adds_reputation_value:
            current_reputation = character.get_reputation(skill.adds_reputation_faction_id)
            new_reputation = current_reputation + skill.adds_reputation_value
            character.set_reputation(
                skill.adds_reputation_faction_id, new_reputation, current_user.id
            )
            reputation_changes.append(
                f"Added {skill.adds_reputation_value} reputation with "
                f"{skill.adds_reputation_faction.name} from skill {skill.name}"
            )

    # Add reputation from species abilities
    if character.species:
        for ability in character.species.abilities:
            if (
                ability.type == AbilityType.STARTING_REPUTATION.value
                and ability.starting_reputation_faction_id
                and ability.starting_reputation_value
            ):
                current_reputation = character.get_reputation(
                    ability.starting_reputation_faction_id
                )
                new_reputation = current_reputation + ability.starting_reputation_value
                character.set_reputation(
                    ability.starting_reputation_faction_id, new_reputation, current_user.id
                )
                reputation_changes.append(
                    f"Added {ability.starting_reputation_value} reputation with "
                    f"{ability.starting_reputation_faction.name} from species ability "
                    f"{ability.name}"
                )

    db.session.commit()
    # Audit log for activation
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes=(
            f"Character activated. Spent {character.get_total_skill_cost()} character points "
            "on skills."
        ),
    )
    db.session.add(audit)
    db.session.commit()
    flash("Character activated successfully!", "success")
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/new/<int:user_id>", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["character.edit_all"])
def create_for_player(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("characters.character_list"))
    factions = Faction.query.all()
    species_list = Species.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    return render_template(
        "characters/edit.html",
        user_id=user_id,
        admin_context=True,
        factions=factions,
        species_list=species_list,
        all_cybernetics=all_cybernetics,
    )


@characters_bp.route("/new/<int:user_id>", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["character.edit_all"])
def create_for_player_post(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("characters.character_list"))
    name = request.form.get("name")
    pronouns_subject = request.form.get("pronouns_subject")
    pronouns_object = request.form.get("pronouns_object")
    faction_id = request.form.get("faction")
    species_id = request.form.get("species_id")
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    if not name or not faction_id or not species_id:
        flash("Character name, faction, and species are required", "error")
        return render_template(
            "characters/edit.html",
            user_id=user_id,
            admin_context=True,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    faction = db.session.get(Faction, faction_id)
    if not faction:
        flash("Invalid faction selected", "error")
        return render_template(
            "characters/edit.html",
            user_id=user_id,
            admin_context=True,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    if not faction.allow_player_characters and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You do not have permission to select this faction.", "error")
        return render_template(
            "characters/edit.html",
            user_id=user_id,
            admin_context=True,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    # Validate species is permitted for faction
    if not (current_user.has_permission("character.edit_all")):
        species = db.session.get(Species, species_id)
        if not species or faction.id not in species.permitted_factions_list:
            flash("Selected species is not permitted for the chosen faction.", "error")
            return render_template(
                "characters/edit.html",
                user_id=user_id,
                admin_context=True,
                factions=factions,
                species_list=species_list,
                all_cybernetics=all_cybernetics,
            )

    species = db.session.get(Species, species_id)
    pick_error = validate_starting_skill_picks(
        species, request.form.getlist("starting_skill_pick")
    ) or validate_starting_condition_stages(species, request.form)
    if pick_error:
        flash(pick_error, "error")
        return render_template(
            "characters/edit.html",
            user_id=user_id,
            admin_context=True,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    base_character_points = 10
    posted_points, points_error = _posted_base_character_points(current_user)
    if points_error:
        flash(points_error, "error")
        return render_template(
            "characters/edit.html",
            user_id=user_id,
            admin_context=True,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )
    if posted_points is not None:
        base_character_points = posted_points

    # Get background fields from form
    background = request.form.get("background", "").strip()
    goals = request.form.get("goals", "").strip()
    concept = request.form.get("concept", "").strip()

    character = Character(
        user_id=user.id,
        name=name,
        pronouns_subject=pronouns_subject,
        pronouns_object=pronouns_object,
        status=CharacterStatus.DEVELOPING.value,
        faction_id=faction.id,
        species_id=int(species_id),
        base_character_points=base_character_points,
        background=background,
        goals=goals,
        concept=concept,
    )
    db.session.add(character)
    db.session.flush()
    apply_starting_skills(
        character, species, current_user, request.form.getlist("starting_skill_pick")
    )
    apply_skill_pair_grants(character, species, current_user)
    condition_notes = apply_starting_conditions(character, species, request.form)
    db.session.commit()

    # Handle background review system for character creation by admin
    if background or goals or concept:
        # Admin created character with background - mark for review
        char_background = CharacterBackground.get_or_create_for_character(character.id)
        char_background.background = background
        char_background.goals = goals
        char_background.concept = concept
        char_background.mark_for_review()
        db.session.add(char_background)
        db.session.commit()

    # Audit log for creation
    created = "Character created by admin"
    if condition_notes:
        created += ". " + "; ".join(condition_notes)
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.CREATE.value,
        changes=created,
    )
    db.session.add(audit)
    db.session.commit()
    if current_user.has_permission("character.edit_all"):
        implant_error = _assign_new_character_implants(
            character, request.form.getlist("cybernetic_ids[]")
        )
        if implant_error:
            flash(implant_error, "error")
    flash("Character created successfully!", "success")
    return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))


@characters_bp.route("/<int:character_id>/audit-log")
@login_required
@email_verified_required
@permission_required(
    permissions=["character.edit_all"],
    condition_func=can_edit_character,
    on_declined={
        "redirect_url": "characters.character_list",
        "flash_message": "You can only view audit logs for your own characters.",
        "flash_category": "error",
    },
)
def audit_log(character_id):
    character = Character.query.get_or_404(character_id)

    # Check if user can view this character's audit log
    if character.user_id != current_user.id and not current_user.has_permission(
        "character.edit_all"
    ):
        flash("You can only view audit logs for your own characters.", "error")
        return redirect(url_for("characters.character_list"))

    audit_logs = (
        CharacterAuditLog.query.filter_by(character_id=character_id)
        .order_by(CharacterAuditLog.timestamp.desc())
        .all()
    )
    return render_template(
        "characters/audit_log.html",
        character=character,
        audit_logs=audit_logs,
        CharacterAuditAction=CharacterAuditAction,
    )


@characters_bp.route("/api/search")
@login_required
@email_verified_required
def api_character_search():
    """Search active characters by name, user name, or user_id.character_id."""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"items": []})

    characters_query = Character.query.filter(
        Character.status == CharacterStatus.ACTIVE.value,
        Character.character_id.isnot(None),
    )
    characters = (
        Character.filter_by_search(query, characters_query).order_by(Character.name).limit(20).all()
    )

    items = []
    for character in characters:
        faction_name = character.faction.name if character.faction else "No faction"
        surname = character.user.surname or ""
        user_info = f"{character.user.first_name} {surname}".strip()
        player_reference = f"{character.user_id}.{character.character_id}"
        items.append(
            {
                "id": character.id,
                "player_reference": player_reference,
                "text": (f"{character.name} ({faction_name}) - {user_info} ({player_reference})"),
            }
        )
    return jsonify({"items": items})


@characters_bp.route("/api/validate_user_id_character_id")
@login_required
@email_verified_required
def validate_user_id_character_id():
    character_id = request.args.get("character_id")
    if not character_id:
        return jsonify({"success": False, "error": "No character ID provided"})

    try:
        # Split the character_id into user_id and character_id
        user_id, char_id = map(int, character_id.split("."))

        # Query the character
        character = Character.query.filter_by(user_id=user_id, id=char_id).first()

        if character:
            return jsonify({"success": True, "character_name": character.name})
        else:
            return jsonify({"success": False, "error": "Character not found"})

    except (ValueError, AttributeError):
        return jsonify({"success": False, "error": "Invalid character ID format"})


@characters_bp.route("/<int:character_id>/view")
@login_required
@email_verified_required
@permission_required(permissions=["character.view_all"])
def view(character_id):
    character = Character.query.get_or_404(character_id)

    # Get the character sheet template
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CHARACTER_SHEET.value).first()

    if not template:
        flash("Character sheet template not found.", "error")
        return redirect(url_for("characters.character_list"))

    # Prepare template context
    template_context = {
        "character": character,
        "generate_qr_code": generate_qr_code,
        "generate_web_qr_code": generate_web_qr_code,
    }

    # Render the template
    front_rendered = template.get_front_page_render(template_context)
    back_rendered = template.get_back_page_render(template_context)
    css = template.get_css_render()
    css_b64 = base64.b64encode(css.encode("utf-8")).decode("ascii")

    # Determine edit URL based on permissions
    edit_url = None
    if current_user.is_authenticated and (
        character.user_id == current_user.id or current_user.has_permission("character.edit_all")
    ):
        edit_url = url_for("characters.edit", character_id=character.id)

    return render_template(
        "templates/view.html",
        title=f"{character.name} - Character Sheet",
        template=template,
        front_rendered=front_rendered,
        back_rendered=back_rendered,
        edit_url=edit_url,
        back_url=url_for("characters.character_list"),
        css_b64=css_b64,
        character=character,
    )
