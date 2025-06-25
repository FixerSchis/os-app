import base64

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.conditions import Condition
from models.database.cybernetic import CharacterCybernetic, Cybernetic
from models.database.faction import Faction
from models.database.species import Species
from models.enums import CharacterAuditAction, PrintTemplateType, Role
from models.extensions import db
from models.tools.character import (
    Character,
    CharacterAuditLog,
    CharacterCondition,
    CharacterStatus,
    CharacterTag,
    assign_character_id,
)
from models.tools.print_template import PrintTemplate
from models.tools.research import CharacterResearch
from models.tools.user import User
from utils import generate_qr_code, generate_web_qr_code
from utils.decorators import (
    character_owner_or_user_admin_required,
    email_verified_required,
    user_admin_required,
)

characters_bp = Blueprint("characters", __name__)


@characters_bp.route("/")
@login_required
@email_verified_required
def character_list():
    characters = []
    if current_user.has_role(Role.USER_ADMIN.value):
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

    # Only allow factions that allow player characters if user is not an NPC
    if not faction.allow_player_characters and not current_user.has_role("npc"):
        flash("You do not have permission to select this faction.", "error")
        return render_template(
            "characters/edit.html",
            admin_context=admin_context,
            factions=factions,
            species_list=species_list,
            all_cybernetics=all_cybernetics,
        )

    # Set base character points based on NPC role
    base_character_points = 30 if current_user.has_role("npc") else 10

    character = Character(
        user_id=current_user.id,
        name=name,
        pronouns_subject=pronouns_subject,
        pronouns_object=pronouns_object,
        status=CharacterStatus.DEVELOPING.value,
        faction_id=faction.id,
        species_id=int(species_id),
        base_character_points=base_character_points,
    )
    db.session.add(character)
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
    if current_user.has_role("user_admin"):
        selected_cyber_ids = request.form.getlist("cybernetic_ids[]")
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
    flash("Character created successfully!", "success")
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/edit", methods=["GET"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def edit(character_id):
    character = Character.query.get_or_404(character_id)
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
    )


@characters_bp.route("/<int:character_id>/edit", methods=["POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def edit_post(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.form.get("admin_context") == "1"
    user = User.query.get(character.user_id) if admin_context else None

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

    # Only allow factions that allow player characters if user is not an NPC
    if not faction.allow_player_characters and not current_user.has_role("npc"):
        flash("You do not have permission to select this faction.", "error")
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

    # Track condition changes for CONDITION_CHANGE action
    condition_changes = []

    if current_user.has_role("user_admin"):
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
                return redirect(url_for("characters.edit", character_id=character.id))
        # Add condition
        if request.form.get("add_condition"):
            cond_id = request.form.get("add_condition_id")
            stage = request.form.get("add_condition_stage")
            duration = request.form.get("add_condition_duration")
            if cond_id and stage and duration is not None:
                exists = CharacterCondition.query.filter_by(
                    character_id=character.id, condition_id=cond_id
                ).first()
                if not exists:
                    condition = Condition.query.get(cond_id)
                    condition_changes.append(
                        f"Condition added: {condition.name} (Stage {stage}, Duration {duration})"
                    )
                    new_cc = CharacterCondition(
                        character_id=character.id,
                        condition_id=cond_id,
                        current_stage=stage,
                        current_duration=duration,
                    )
                    db.session.add(new_cc)
                    db.session.commit()
                    flash("Condition added.", "success")
                    return redirect(url_for("characters.edit", character_id=character.id))
        # Update existing conditions
        for cc in character.active_conditions:
            stage_val = request.form.get(f"active_condition_stage_{cc.id}")
            duration_val = request.form.get(f"active_condition_duration_{cc.id}")
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
        cybernetic_changes = []

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
    if current_user.has_role("user_admin"):
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

    db.session.commit()
    flash("Character updated successfully")
    if admin_context:
        return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/retire", methods=["POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def retire_character(character_id):
    character = Character.query.get_or_404(character_id)
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
@user_admin_required
def kill_character(character_id):
    character = Character.query.get_or_404(character_id)
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
@user_admin_required
def restore_character(character_id):
    """Restores a retired character to active status."""
    character = Character.query.get_or_404(character_id)

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

    if user.has_active_character() and not user.has_role("npc"):
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
    flash("Character restored and set to active.", "success")
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/delete", methods=["POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def delete_character(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.form.get("admin_context") == "1"
    if (
        not current_user.has_role("user_admin")
        and character.status != CharacterStatus.DEVELOPING.value
    ):
        flash("Only developing characters can be deleted.", "error")
        return redirect(url_for("characters.character_list"))
    for audit_log in CharacterAuditLog.query.filter_by(character_id=character.id).all():
        db.session.delete(audit_log)
    db.session.delete(character)
    db.session.commit()
    flash("Character deleted.", "success")
    if admin_context:
        user = User.query.filter_by(id=character.user_id).first()
        if user:
            return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
    return redirect(url_for("characters.character_list"))


@characters_bp.route("/<int:character_id>/activate", methods=["POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def activate_character(character_id):
    character = Character.query.get_or_404(character_id)
    if character.status != CharacterStatus.DEVELOPING.value:
        flash("Only developing characters can be activated.", "error")
        return redirect(url_for("characters.character_list"))

    if current_user.has_active_character() and not current_user.has_role("npc"):
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
@user_admin_required
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
@user_admin_required
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

    # Only allow factions that allow player characters if user is not an NPC
    if not faction.allow_player_characters and not user.has_role("npc"):
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
    if not (current_user.has_role("user_admin") or current_user.has_role("npc")):
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

    character = Character(
        user_id=user.id,
        name=name,
        pronouns_subject=pronouns_subject,
        pronouns_object=pronouns_object,
        status=CharacterStatus.DEVELOPING.value,
        faction_id=faction.id,
        species_id=int(species_id),
    )
    db.session.add(character)
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
    if current_user.has_role("user_admin"):
        selected_cyber_ids = request.form.getlist("cybernetic_ids[]")
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
    flash("Character created successfully!", "success")
    return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))


@characters_bp.route("/<int:character_id>/audit-log")
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def audit_log(character_id):
    character = Character.query.get_or_404(character_id)

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
@character_owner_or_user_admin_required
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
        character.user_id == current_user.id or current_user.has_role("user_admin")
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
