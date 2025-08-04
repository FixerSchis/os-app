import base64

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.conditions import Condition
from models.database.cybernetic import CharacterCybernetic, Cybernetic
from models.database.faction import Faction
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.sample import Sample
from models.database.species import Species
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
)
from models.tools.character_inventory import CharacterItem
from models.tools.group import GroupBackground
from models.tools.print_template import PrintTemplate
from models.tools.research import CharacterResearch
from models.tools.user import User
from utils import generate_qr_code, generate_web_qr_code
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required


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


characters_bp = Blueprint("characters", __name__)


@characters_bp.route("/")
@login_required
@email_verified_required
def character_list():
    characters = []
    if current_user.has_permission("character.view_all"):
        characters = Character.query.all()
    else:
        characters = Character.query.filter_by(user_id=current_user.id).all()

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

    base_character_points = 10

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
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.CREATE.value,
        changes="Character created",
    )
    db.session.add(audit)
    db.session.commit()
    if current_user.has_permission("character.edit_all"):
        selected_cyber_ids = request.form.getlist("cybernetic_ids[]")
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
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

    character.name = name
    character.pronouns_subject = pronouns_subject
    character.pronouns_object = pronouns_object
    character.faction_id = faction_id
    character.species_id = species_id

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
            if duration_val is not None and int(duration_val) != cc.current_duration:
                condition_changes.append(
                    f"Condition {cc.condition.name} duration changed from {cc.current_duration} "
                    f"to {duration_val}"
                )
                cc.current_duration = int(duration_val)

        # Track cybernetic changes for CYBERNETICS_CHANGE action

        # Update cybernetics if user_admin
        selected_cyber_ids = request.form.getlist("cybernetic_ids[]")
        current_cyber_ids = {cc.cybernetic_id for cc in character.cybernetics_link}
        new_cyber_ids = set(int(cid) for cid in selected_cyber_ids if cid.isdigit())

        # Track cybernetic changes
        added_cybernetics = new_cyber_ids - current_cyber_ids
        removed_cybernetics = current_cyber_ids - new_cyber_ids

        for cyber_id in added_cybernetics:
            cyber = Cybernetic.query.get(cyber_id)
            if cyber:
                cybernetic_changes.append(f"Cybernetic added: {cyber.name}")

        for cyber_id in removed_cybernetics:
            cyber = Cybernetic.query.get(cyber_id)
            if cyber:
                cybernetic_changes.append(f"Cybernetic removed: {cyber.name}")

        # Remove all current
        CharacterCybernetic.query.filter_by(character_id=character.id).delete()
        # Add new
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))

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

    total_skill_cost = character.get_total_skill_cost()
    if total_skill_cost > character.base_character_points and not user.can_spend_character_points(
        total_skill_cost - character.base_character_points
    ):
        flash("Not enough character points to activate character.", "error")
        return redirect(url_for("characters.character_list"))

    if character.character_id is None:
        character.character_id = assign_character_id(character.user_id)

    if total_skill_cost > character.base_character_points:
        user.spend_character_points(total_skill_cost - character.base_character_points)

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
                        changes=f"Starting item added: {blueprint.name} ({item.full_code})",
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
        changes=(f"Character activated. Spent {total_skill_cost} character points on skills."),
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
        background=background,
        goals=goals,
        concept=concept,
    )
    db.session.add(character)
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
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.CREATE.value,
        changes="Character created by admin",
    )
    db.session.add(audit)
    db.session.commit()
    if current_user.has_permission("character.edit_all"):
        selected_cyber_ids = request.form.getlist("cybernetic_ids[]")
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
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


@characters_bp.route("/api/validate_user_id_character_id")
@login_required
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
