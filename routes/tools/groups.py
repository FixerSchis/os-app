from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.group_type import GroupType
from models.enums import CharacterAuditAction, CharacterStatus, GroupAuditAction
from models.extensions import db
from models.tools.character import Character, CharacterAuditLog
from models.tools.group import Group, GroupAuditLog, GroupBackground, GroupInvite, GroupJoinRequest
from utils.decorators import email_verified_required, has_active_character_required
from utils.permission_decorators import permission_required

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/")
@login_required
@email_verified_required
def group_list():
    # Admins can switch between admin and user view.
    # The 'admin_view' parameter will be 'false' when they switch to user view.
    admin_view_param = request.args.get("admin_view", "true")
    is_admin_and_wants_admin_view = (
        current_user.has_permission("group.view_all") and admin_view_param == "true"
    )

    if is_admin_and_wants_admin_view:
        show_inactive = request.args.get("show_inactive", "false") == "true"
        if show_inactive:
            groups = Group.query.all()
        else:
            groups = Group.query.filter_by(is_active=True).all()
        return render_template(
            "groups/admin_list.html",
            groups=groups,
            group_types=GroupType.query.all(),
            show_inactive=show_inactive,
        )

    # From here, it's the user view (for non-admins, or admins who've switched)
    # Get all active characters for the user
    user_characters = Character.query.filter_by(
        user_id=current_user.id, status=CharacterStatus.ACTIVE.value
    ).all()

    if not user_characters:
        flash("You need an active character to access groups", "error")
        return redirect(url_for("characters.character_list"))

    # Determine the selected character
    selected_character_id = request.args.get("character_id", type=int)
    if selected_character_id:
        active_character = next((c for c in user_characters if c.id == selected_character_id), None)
        if not active_character:
            flash("Invalid character selected.", "error")
            return redirect(url_for("characters.character_list"))
    else:
        active_character = user_characters[0]

    # Get group invites for the character
    invites = GroupInvite.query.filter_by(character_id=active_character.id).all()

    # Get list of active characters not in a group for invites
    active_characters_for_invite = (
        Character.query.filter_by(status=CharacterStatus.ACTIVE.value)
        .filter(Character.group_id.is_(None), Character.faction_id == active_character.faction_id)
        .all()
    )

    # Get active groups for the character's faction (for future use)
    # active_groups = Group.query.filter_by(is_active=True).all()

    return render_template(
        "groups/list.html",
        character=active_character,
        user_characters=user_characters,
        invites=invites,
        active_characters=active_characters_for_invite,
        group_types=GroupType.query.all(),
        admin_view=admin_view_param,
        character_id=active_character.id,
    )


@groups_bp.route("/new", methods=["GET"])
@login_required
@email_verified_required
def create_group():
    return redirect(url_for("groups.group_list"))


@groups_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
@has_active_character_required
def create_group_post():
    name = request.form.get("name")
    type = request.form.get("type")
    background = request.form.get("background", "")
    objective = request.form.get("objective", "")
    goals = request.form.get("goals", "")
    character_id = request.form.get("character_id")
    admin_view = request.form.get("admin_view")

    if not name or not type:
        flash("Name and type are required", "error")
        return redirect(url_for("groups.group_list"))

    if not GroupType.query.get(type):
        flash("Invalid group type", "error")
        return redirect(url_for("groups.group_list"))

    active_character = db.session.get(Character, character_id)
    if not active_character or active_character.user_id != current_user.id:
        flash("Invalid character selected.", "error")
        return redirect(url_for("groups.group_list"))

    group = Group(
        name=name,
        group_type_id=type,
        faction_id=active_character.faction_id,  # Set faction to character's faction
        bank_account=0,
        background=background,
        objective=objective,
        goals=goals,
    )
    db.session.add(group)
    db.session.flush()  # Flush to get the group ID

    # Create background record that needs review
    background_record = GroupBackground(
        group_id=group.id,
        background=background,
        objective=objective,
        goals=goals,
        needs_review=True,
    )
    db.session.add(background_record)

    # Add character to group
    active_character.group_id = group.id

    # Create audit log for group creation
    audit_log = GroupAuditLog(
        group_id=group.id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.CREATE.value,
        changes=f"Group created by {active_character.name}",
    )
    db.session.add(audit_log)

    db.session.commit()
    flash("Group created successfully.", "success")
    return redirect(
        url_for("groups.group_list", admin_view=admin_view, character_id=active_character.id)
    )


@groups_bp.route("/<int:group_id>/edit", methods=["POST"])
@login_required
@email_verified_required
def edit_group_post(group_id):
    group = Group.query.get_or_404(group_id)
    name = request.form.get("name")
    type = request.form.get("type")
    background = request.form.get("background", "")
    objective = request.form.get("objective", "")
    goals = request.form.get("goals", "")
    bank_account = request.form.get("bank_account")
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")

    # Prevent editing inactive groups (unless user is admin)
    if not group.is_active and not current_user.has_permission("group.edit"):
        flash("Cannot edit inactive groups", "error")
        if admin_view == "false":
            return redirect(
                url_for("groups.group_list", admin_view="false", character_id=character_id)
            )
        return redirect(url_for("groups.group_list"))

    if not name:
        flash("Name is required", "error")
        return redirect(url_for("groups.group_list"))

    # Track changes for audit log
    changes = []
    if group.name != name:
        changes.append(f"Name changed from '{group.name}' to '{name}'")

    # Track background changes
    background_changes = []
    if group.background != background:
        background_changes.append("Background updated")
    if group.objective != objective:
        background_changes.append("Objective updated")
    if group.goals != goals:
        background_changes.append("Goals updated")

    # Only allow type changes for admins
    if current_user.has_permission("group.edit") and type and group.group_type_id != int(type):
        group_type = GroupType.query.get(type)
        changes.append(f"Type changed from '{group.group_type.name}' to '{group_type.name}'")
        group.group_type_id = int(type)

    # Handle bank account changes using centralized methods
    if current_user.has_permission("group.edit") and bank_account:
        try:
            bank_account_int = int(bank_account)
            if group.bank_account != bank_account_int:
                group.set_funds(bank_account_int, current_user.id, "Admin group edit")
        except ValueError:
            flash("Bank account must be a number", "error")
            if admin_view == "false":
                return redirect(
                    url_for("groups.group_list", admin_view="false", character_id=character_id)
                )
            return redirect(url_for("groups.group_list"))

    group.name = name

    # Handle background review system
    if background_changes:
        # Group member edited background - mark for review
        group_background = GroupBackground.get_or_create_for_group(group.id)
        group_background.background = background
        group_background.objective = objective
        group_background.goals = goals
        group_background.mark_for_review()
        db.session.add(group_background)

    # Update group background fields
    group.background = background
    group.objective = objective
    group.goals = goals

    # Create audit log if there were changes
    if changes or background_changes:
        all_changes = changes + background_changes
        audit_log = GroupAuditLog(
            group_id=group.id,
            editor_user_id=current_user.id,
            action=GroupAuditAction.EDIT.value,
            changes="; ".join(all_changes),
        )
        db.session.add(audit_log)

    db.session.commit()
    flash("Group updated successfully", "success")
    if admin_view == "false":
        return redirect(url_for("groups.group_list", admin_view="false", character_id=character_id))
    return redirect(url_for("groups.group_list"))


@groups_bp.route("/<int:group_id>/invite", methods=["POST"])
@login_required
@email_verified_required
@has_active_character_required
def invite_to_group(group_id):
    group = Group.query.get_or_404(group_id)
    admin_view = request.form.get("admin_view")
    redirect_character_id = request.form.get("redirect_character_id")

    # Prevent inviting to inactive groups
    if not group.is_active:
        flash("Cannot invite to inactive groups", "error")
        if admin_view == "false":
            return redirect(
                url_for("groups.group_list", admin_view="false", character_id=redirect_character_id)
            )
        return redirect(url_for("groups.group_list"))

    if redirect_character_id:
        character = Character.query.get_or_404(redirect_character_id)
        if character.user_id != current_user.id:
            abort(403)
    else:
        character = current_user.get_character()

    if not character or character.group_id != group.id:
        abort(403)

    invite_character_id = request.form.get("character_id")
    if not invite_character_id:
        flash("Character ID is required", "error")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=redirect_character_id)
        )

    character = db.session.get(Character, invite_character_id)
    if not character:
        flash("Character not found", "error")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=redirect_character_id)
        )

    if character.group_id:
        flash("Character is already in a group", "error")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=redirect_character_id)
        )

    # Check faction compatibility (only for regular users, not admins)
    if not current_user.has_permission("group.edit"):
        if character.faction_id != group.faction_id:
            flash(
                f"Character must be from the same faction as the group ({group.faction.name})",
                "error",
            )
            return redirect(
                url_for(
                    "groups.group_list", admin_view=admin_view, character_id=redirect_character_id
                )
            )

    # Check if invite already exists
    existing_invite = GroupInvite.query.filter_by(
        group_id=group.id, character_id=character.id
    ).first()

    if existing_invite:
        flash("Character already has an invite to this group", "error")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=redirect_character_id)
        )

    invite = GroupInvite(group_id=group.id, character_id=character.id)
    db.session.add(invite)

    # Create audit log for invite sent
    audit_log = GroupAuditLog(
        group_id=group.id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.INVITE_SENT.value,
        changes=f"Invite sent to {character.name}",
    )
    db.session.add(audit_log)

    db.session.commit()

    flash(f"Invited {character.name} to the group.", "success")
    return redirect(
        url_for("groups.group_list", admin_view=admin_view, character_id=redirect_character_id)
    )


@groups_bp.route("/invites/<int:invite_id>/respond", methods=["POST"])
@login_required
@email_verified_required
@has_active_character_required
def respond_to_invite_post(invite_id):
    invite = GroupInvite.query.get_or_404(invite_id)
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")
    character = Character.query.get_or_404(character_id)

    if invite.character_id != character.id or character.user_id != current_user.id:
        abort(403)

    action = request.form.get("action")
    if action == "accept":
        # Check faction compatibility (only for regular users, not admins)
        if not current_user.has_permission("group.edit"):
            if character.faction_id != invite.group.faction_id:
                flash(
                    f"Character must be from the same faction as the group "
                    f"({invite.group.faction.name})",
                    "error",
                )
                return redirect(
                    url_for("groups.group_list", admin_view=admin_view, character_id=character_id)
                )

        character.group_id = invite.group_id

        # Create audit log for member joining (group audit)
        audit_log = GroupAuditLog(
            group_id=invite.group_id,
            editor_user_id=current_user.id,
            action=GroupAuditAction.MEMBER_ADDED.value,
            changes=f"Member joined: {character.name}",
        )
        db.session.add(audit_log)

        # Create audit log for character joining group (character audit)
        from models.enums import CharacterAuditAction

        character_audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.GROUP_JOINED.value,
            changes=f"Joined group: {invite.group.name}",
        )
        db.session.add(character_audit)

        flash(f"You have joined {invite.group.name}.", "success")
        GroupInvite.query.filter_by(character_id=character.id).delete()
    elif action == "decline":
        # Create audit log for invite declined
        audit_log = GroupAuditLog(
            group_id=invite.group_id,
            editor_user_id=current_user.id,
            action=GroupAuditAction.INVITE_DECLINED.value,
            changes=f"Invite declined by {character.name}",
        )
        db.session.add(audit_log)

        flash(f"You have declined the invitation to {invite.group.name}.", "success")

    db.session.delete(invite)
    db.session.commit()

    return redirect(url_for("groups.group_list", admin_view=admin_view, character_id=character_id))


@groups_bp.route("/<int:group_id>/leave", methods=["POST"])
@login_required
@email_verified_required
@has_active_character_required
def leave_group_post(group_id):
    group = Group.query.get_or_404(group_id)
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")
    character = db.session.get(Character, character_id)

    if not character or character.user_id != current_user.id:
        flash("Invalid character selected.", "error")
        return redirect(url_for("groups.group_list"))

    if character.group_id != group.id:
        flash("You are not a member of this group", "error")
        return redirect(url_for("groups.group_list", character_id=character_id))

    # Create audit log for member leaving (group audit)
    audit_log = GroupAuditLog(
        group_id=group.id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.MEMBER_LEFT.value,
        changes=f"Member left: {character.name}",
    )
    db.session.add(audit_log)

    # Create audit log for character leaving group (character audit)
    from models.enums import CharacterAuditAction

    character_audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.GROUP_LEFT.value,
        changes=f"Left group: {group.name}",
    )
    db.session.add(character_audit)

    character.group_id = None
    db.session.commit()
    flash("You have left the group.", "success")
    return redirect(url_for("groups.group_list", admin_view=admin_view, character_id=character_id))


@groups_bp.route("/<int:group_id>/disband", methods=["POST"])
@login_required
@email_verified_required
@has_active_character_required
def disband_group_post(group_id):
    group = Group.query.get_or_404(group_id)
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")
    character = Character.query.get_or_404(character_id)

    if character.user_id != current_user.id:
        abort(403)

    # Must be the last member to disband
    if len(group.characters) > 1:
        flash("Cannot disband group with multiple members", "error")
        return redirect(url_for("groups.group_list", character_id=character_id))

    # Remove character from group
    character.group_id = None

    # Delete all invites for this group
    GroupInvite.query.filter_by(group_id=group_id).delete()

    # Deactivate the group instead of deleting it
    group.deactivate(current_user.id, f"Group disbanded by {character.name}")

    db.session.commit()

    flash("Group disbanded and deactivated.", "success")
    return redirect(url_for("groups.group_list", admin_view=admin_view, character_id=character_id))


@groups_bp.route("/<int:group_id>/disband/admin", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["group.edit"])
def disband_group_admin(group_id):
    group = Group.query.get_or_404(group_id)

    # Delete all invites for this group
    GroupInvite.query.filter_by(group_id=group_id).delete()

    # Remove all characters from the group
    for character in group.characters:
        character.group_id = None

    # Deactivate the group instead of deleting it
    group.deactivate(
        current_user.id,
        f"Group disbanded by admin {current_user.first_name} {current_user.surname or ''}",
    )

    db.session.commit()

    flash("Group disbanded and deactivated.", "success")
    return redirect(url_for("groups.group_list"))


@groups_bp.route("/<int:group_id>/remove/<int:character_id>", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["group.edit"])
def remove_character(group_id, character_id):
    group = Group.query.get_or_404(group_id)
    character = Character.query.get_or_404(character_id)

    if character.group_id != group.id:
        flash("Character is not a member of this group", "error")
        return redirect(url_for("groups.group_list"))

    # Create audit log for member removal
    audit_log = GroupAuditLog(
        group_id=group.id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.MEMBER_REMOVED.value,
        changes=f"Member removed by admin: {character.name}",
    )
    db.session.add(audit_log)

    # Create audit log for character being removed from group (character audit)
    character_audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.GROUP_LEFT.value,
        changes=f"Removed from group by admin: {group.name}",
    )
    db.session.add(character_audit)

    character.group_id = None
    db.session.commit()
    flash("Character removed from group", "success")
    return redirect(url_for("groups.edit_group_admin", group_id=group_id))


@groups_bp.route("/create/admin", methods=["GET", "POST"])
@login_required
@email_verified_required
@permission_required(permissions=["group.edit"])
def create_group_admin():
    if request.method == "GET":
        # Get active characters that are not in any group
        available_characters = (
            Character.query.filter_by(group_id=None, status=CharacterStatus.ACTIVE.value)
            .order_by(Character.name)
            .all()
        )
        return render_template(
            "groups/admin_edit.html",
            group_types=GroupType.query.all(),
            factions=Faction.query.all(),
            available_characters=available_characters,
        )

    name = request.form.get("name")
    group_type_id = request.form.get("group_type_id")
    faction_id = request.form.get("faction_id")
    bank_account = request.form.get("bank_account")
    background = request.form.get("background", "")
    objective = request.form.get("objective", "")
    goals = request.form.get("goals", "")
    character_id = request.form.get("character_id")

    if not name or not group_type_id or not faction_id:
        flash("Name, group type, and faction are required", "error")
        return redirect(url_for("groups.create_group_admin"))

    group_type = GroupType.query.get(group_type_id)
    if not group_type:
        flash("Invalid group type", "error")
        return redirect(url_for("groups.create_group_admin"))

    faction = Faction.query.get(faction_id)
    if not faction:
        flash("Invalid faction", "error")
        return redirect(url_for("groups.create_group_admin"))

    try:
        bank_account_int = int(bank_account) if bank_account else 0
    except ValueError:
        flash("Bank account must be a number", "error")
        return redirect(url_for("groups.create_group_admin"))

    group = Group(
        name=name,
        group_type_id=group_type.id,
        faction_id=faction.id,
        bank_account=bank_account_int,
        background=background,
        objective=objective,
        goals=goals,
    )
    db.session.add(group)
    db.session.flush()  # Flush to get the group ID

    # Create background record that needs review
    background_record = GroupBackground(
        group_id=group.id,
        background=background,
        objective=objective,
        goals=goals,
        needs_review=True,
    )
    db.session.add(background_record)

    # Assign initial character if provided
    if character_id:
        character = db.session.get(Character, character_id)
        if character:
            character.group_id = group.id

    # Create audit log for admin group creation
    audit_log = GroupAuditLog(
        group_id=group.id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.CREATE.value,
        changes=f"Group created by admin with {bank_account_int} starting funds",
    )
    db.session.add(audit_log)

    db.session.commit()
    flash("Group created successfully", "success")
    return redirect(url_for("groups.group_list"))


@groups_bp.route("/<int:group_id>/edit/admin", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["group.edit"])
def edit_group_admin(group_id):
    group = Group.query.get_or_404(group_id)
    # Get active characters that are not in any group (available to add)
    available_characters = (
        Character.query.filter_by(group_id=None, status=CharacterStatus.ACTIVE.value)
        .order_by(Character.name)
        .all()
    )
    return render_template(
        "groups/admin_edit.html",
        group=group,
        group_types=GroupType.query.all(),
        factions=Faction.query.all(),
        available_characters=available_characters,
    )


@groups_bp.route("/<int:group_id>/edit/admin", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["group.edit"])
def edit_group_admin_post(group_id):
    group = Group.query.get_or_404(group_id)

    name = request.form.get("name")
    type = request.form.get("group_type_id")
    faction_id = request.form.get("faction_id")
    bank_account = request.form.get("bank_account")
    background = request.form.get("background", "")
    objective = request.form.get("objective", "")
    goals = request.form.get("goals", "")

    group_types = GroupType.query.all()

    if not name:
        flash("Name is required", "error")
        return redirect(
            url_for("groups.edit_group_admin", group_id=group.id, group_types=group_types)
        )

    # Validate group type
    group_type = GroupType.query.get(type)
    if not group_type:
        flash("Invalid group type", "error")
        return redirect(
            url_for("groups.edit_group_admin", group_id=group.id, group_types=group_types)
        )

    # Validate faction
    faction = Faction.query.get(faction_id)
    if not faction:
        flash("Invalid faction", "error")
        return redirect(
            url_for("groups.edit_group_admin", group_id=group.id, group_types=group_types)
        )

    try:
        bank_account_int = int(bank_account) if bank_account else 0
    except ValueError:
        flash("Bank account must be a number", "error")
        return redirect(
            url_for("groups.edit_group_admin", group_id=group.id, group_types=group_types)
        )

    # Track changes for audit log
    changes = []
    if group.name != name:
        changes.append(f"Name changed from '{group.name}' to '{name}'")

    # Only allow type changes for admins
    if current_user.has_permission("group.edit") and type and group.group_type_id != int(type):
        changes.append(f"Type changed from '{group.group_type.name}' to '{group_type.name}'")
        group.group_type_id = int(type)

    # Only allow faction changes for admins
    if (
        current_user.has_permission("group.edit")
        and faction_id
        and group.faction_id != int(faction_id)
    ):
        changes.append(f"Faction changed from '{group.faction.name}' to '{faction.name}'")
        group.faction_id = int(faction_id)

    # Handle bank account changes using centralized methods
    if current_user.has_permission("group.edit"):
        if group.bank_account != bank_account_int:
            group.set_funds(bank_account_int, current_user.id, "Admin group edit")

    group.name = name
    group.background = background
    group.objective = objective
    group.goals = goals

    # Create audit log if there were changes
    if changes:
        audit_log = GroupAuditLog(
            group_id=group.id,
            editor_user_id=current_user.id,
            action=GroupAuditAction.EDIT.value,
            changes="; ".join(changes),
        )
        db.session.add(audit_log)

    db.session.commit()
    flash("Group updated successfully", "success")
    return redirect(url_for("groups.edit_group_admin", group_id=group.id))


@groups_bp.route("/<int:group_id>/add_character/admin", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["group.edit"])
def add_character_admin(group_id):
    Group.query.get_or_404(group_id)
    character_id = request.form.get("character_id")

    if not character_id:
        flash("Character ID is required", "error")
        return redirect(url_for("groups.group_list"))

    character = db.session.get(Character, character_id)
    if not character:
        flash("Character not found", "error")
        return redirect(url_for("groups.group_list"))

    if character.group_id:
        flash("Character is already in a group", "error")
        return redirect(url_for("groups.group_list"))

    # Create audit log for admin adding member
    audit_log = GroupAuditLog(
        group_id=group_id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.MEMBER_ADDED.value,
        changes=f"Member added by admin: {character.name}",
    )
    db.session.add(audit_log)

    character.group_id = group_id
    db.session.commit()

    flash("Character added to group", "success")
    return redirect(url_for("groups.edit_group_admin", group_id=group_id))


@groups_bp.route("/<int:group_id>/audit-log")
@login_required
@email_verified_required
def group_audit_log(group_id):
    group = Group.query.get_or_404(group_id)

    # Check if user has access to this group
    # User can view audit log if they are a member of the group or an admin
    user_has_access = False
    if current_user.has_permission("group.view_all"):
        user_has_access = True
    else:
        # Check if any of user's characters are in this group
        user_characters = Character.query.filter_by(user_id=current_user.id).all()
        for character in user_characters:
            if character.group_id == group.id:
                user_has_access = True
                break

    if not user_has_access:
        abort(403)

    audit_logs = (
        GroupAuditLog.query.filter_by(group_id=group_id)
        .order_by(GroupAuditLog.timestamp.desc())
        .all()
    )

    return render_template(
        "groups/audit_log.html",
        group=group,
        audit_logs=audit_logs,
        GroupAuditAction=GroupAuditAction,
    )


@groups_bp.route("/<int:group_id>/activate", methods=["POST"])
@login_required
@email_verified_required
def activate_group(group_id):
    group = Group.query.get_or_404(group_id)
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")

    # Check if user is admin or if user has a character in this group
    user_has_access = False
    if current_user.has_permission("group.edit"):
        user_has_access = True
    else:
        # Check if any of user's characters are in this group
        user_characters = Character.query.filter_by(user_id=current_user.id).all()
        for character in user_characters:
            if character.group_id == group.id:
                user_has_access = True
                break

    if not user_has_access:
        abort(403)

    if group.is_active:
        flash("Group is already active", "info")
    else:
        group.activate(current_user.id, "Group reactivated")
        db.session.commit()
        flash("Group activated successfully", "success")

    if admin_view == "false":
        return redirect(url_for("groups.group_list", admin_view="false", character_id=character_id))
    return redirect(url_for("groups.group_list"))


@groups_bp.route("/<int:group_id>/deactivate", methods=["POST"])
@login_required
@email_verified_required
def deactivate_group(group_id):
    group = Group.query.get_or_404(group_id)
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")

    # Only user-admins can deactivate groups with characters in them
    if len(group.characters) > 0 and not current_user.has_permission("group.edit"):
        flash("Only administrators can deactivate groups with members", "error")
        if admin_view == "false":
            return redirect(
                url_for("groups.group_list", admin_view="false", character_id=character_id)
            )
        return redirect(url_for("groups.group_list"))

    if not group.is_active:
        flash("Group is already inactive", "info")
    else:
        group.deactivate(current_user.id, "Group deactivated")
        db.session.commit()
        flash("Group deactivated successfully", "success")

    if admin_view == "false":
        return redirect(url_for("groups.group_list", admin_view="false", character_id=character_id))
    return redirect(url_for("groups.group_list"))


@groups_bp.route("/api/groups/search")
@login_required
@email_verified_required
def api_groups_search():
    """API endpoint for searching groups."""
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    if not query or len(query) < 2:
        return jsonify({"items": [], "has_more": False})

    # Search for active groups
    groups = Group.query.filter(Group.is_active.is_(True), Group.name.ilike(f"%{query}%")).paginate(
        page=page, per_page=per_page, error_out=False
    )

    items = []
    for group in groups.items:
        items.append(
            {
                "id": group.id,
                "name": group.name,
                "group_type": group.group_type.name,
                "member_count": len(group.characters),
            }
        )

    return jsonify({"items": items, "has_more": groups.has_next})


@groups_bp.route("/api/characters/search")
@login_required
@email_verified_required
def api_characters_search():
    """API endpoint for searching characters for group invites."""
    query = request.args.get("q", "")
    if not query or len(query) < 2:
        return jsonify({"items": [], "has_more": False})

    # Get the current character's faction for filtering
    character_id = request.args.get("character_id", type=int)
    if character_id:
        current_character = Character.query.get(character_id)
        if current_character and current_character.user_id == current_user.id:
            faction_id = current_character.faction_id
        else:
            faction_id = None
    else:
        faction_id = None

    # Build the query
    characters_query = Character.query.filter_by(status=CharacterStatus.ACTIVE.value)

    # Filter out characters already in groups
    characters_query = characters_query.filter(Character.group_id.is_(None))

    # Check if query looks like user_id.character_id format
    if "." in query:
        try:
            user_id_str, char_id_str = query.split(".", 1)
            user_id = int(user_id_str)
            char_id = int(char_id_str)

            # Search by user_id and character_id
            characters_query = characters_query.filter(
                Character.user_id == user_id, Character.character_id == char_id
            )
        except (ValueError, TypeError):
            # If parsing fails, fall back to name search
            characters_query = characters_query.filter(Character.name.ilike(f"%{query}%"))
    else:
        # Search by name
        characters_query = characters_query.filter(Character.name.ilike(f"%{query}%"))

    # Only apply faction filter for non-admin users
    if faction_id and not current_user.has_permission("group.view_all"):
        characters_query = characters_query.filter(Character.faction_id == faction_id)

    # Limit results
    characters = characters_query.limit(10).all()

    items = []
    for character in characters:
        # Include user info in the text for better identification
        user_info = f"{character.user.first_name} {character.user.surname or ''}"
        items.append(
            {
                "id": character.id,
                "text": f"{character.name} ({character.faction.name}) - {user_info}",
                "name": character.name,
                "faction": character.faction.name,
                "user_info": user_info,
            }
        )

    return jsonify({"items": items, "has_more": False})


@groups_bp.route("/<int:group_id>/join-request", methods=["POST"])
@login_required
@email_verified_required
@has_active_character_required
def request_join_group(group_id):
    group = Group.query.get_or_404(group_id)
    character_id = request.form.get("character_id")
    admin_view = request.form.get("admin_view")

    # Check if character belongs to current user
    character = db.session.get(Character, character_id)
    if not character or character.user_id != current_user.id:
        flash("Invalid character selected.", "error")
        return redirect(url_for("groups.group_list"))

    # Check if character is already in a group
    if character.group_id:
        flash("Character is already in a group", "error")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=character_id)
        )

    # Check if group is active
    if not group.is_active:
        flash("Cannot request to join an inactive group", "error")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=character_id)
        )

    # Check faction compatibility (only for regular users, not admins)
    if not current_user.has_permission("group.edit"):
        if character.faction_id != group.faction_id:
            flash(
                f"Character must be from the same faction as the group ({group.faction.name})",
                "error",
            )
            return redirect(
                url_for("groups.group_list", admin_view=admin_view, character_id=character_id)
            )

    # Check if request already exists
    existing_request = GroupJoinRequest.query.filter_by(
        group_id=group_id, character_id=character_id
    ).first()

    if existing_request:
        if existing_request.status == "pending":
            flash("You already have a pending request to join this group", "info")
        else:
            flash("You have already requested to join this group", "info")
        return redirect(
            url_for("groups.group_list", admin_view=admin_view, character_id=character_id)
        )

    # Create join request
    join_request = GroupJoinRequest(group_id=group_id, character_id=character_id, status="pending")
    db.session.add(join_request)
    db.session.commit()

    flash("Join request sent successfully", "success")
    return redirect(url_for("groups.group_list", admin_view=admin_view, character_id=character_id))


@groups_bp.route("/<int:group_id>/join-requests")
@login_required
@email_verified_required
def view_join_requests(group_id):
    group = Group.query.get_or_404(group_id)

    # Check if user has access to view join requests
    # User can view if they are a member of the group or an admin
    user_has_access = False
    if current_user.has_permission("group.view_all"):
        user_has_access = True
    else:
        # Check if any of user's characters are in this group
        user_characters = Character.query.filter_by(user_id=current_user.id).all()
        for character in user_characters:
            if character.group_id == group.id:
                user_has_access = True
                break

    if not user_has_access:
        abort(403)

    join_requests = GroupJoinRequest.query.filter_by(group_id=group_id, status="pending").all()

    return render_template(
        "groups/join_requests.html",
        group=group,
        join_requests=join_requests,
    )


@groups_bp.route("/<int:group_id>/join-requests/<int:request_id>/respond", methods=["POST"])
@login_required
@email_verified_required
def respond_to_join_request(group_id, request_id):
    group = Group.query.get_or_404(group_id)
    join_request = GroupJoinRequest.query.get_or_404(request_id)

    # Verify the request belongs to this group
    if join_request.group_id != group_id:
        abort(404)

    # Check if user has access to respond to join requests
    # User can respond if they are a member of the group or an admin
    user_has_access = False
    if current_user.has_permission("group.view_all"):
        user_has_access = True
    else:
        # Check if any of user's characters are in this group
        user_characters = Character.query.filter_by(user_id=current_user.id).all()
        for character in user_characters:
            if character.group_id == group.id:
                user_has_access = True
                break

    if not user_has_access:
        abort(403)

    action = request.form.get("action")
    if action not in ["approve", "deny"]:
        flash("Invalid action", "error")
        return redirect(url_for("groups.view_join_requests", group_id=group_id))

    if action == "approve":
        # Check faction compatibility (only for regular users, not admins)
        if not current_user.has_permission("group.edit"):
            if join_request.character.faction_id != group.faction_id:
                flash(
                    f"Character must be from the same faction as the group ({group.faction.name})",
                    "error",
                )
                return redirect(url_for("groups.view_join_requests", group_id=group_id))

        join_request.approve(current_user.id)
        flash("Join request approved", "success")
    else:
        join_request.deny(current_user.id)
        flash("Join request denied", "success")

    db.session.commit()
    return redirect(url_for("groups.view_join_requests", group_id=group_id))


@groups_bp.route("/backgrounds/")
@login_required
@email_verified_required
@permission_required(permissions=["group.background_approve"])
def list_group_backgrounds():
    """List all group backgrounds that need review."""
    backgrounds = GroupBackground.query.filter_by(needs_review=True).all()

    return render_template(
        "groups/backgrounds/list.html",
        backgrounds=backgrounds,
    )


@groups_bp.route("/backgrounds/<int:background_id>/review", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["group.background_approve"])
def review_group_background(background_id):
    """Review a specific group background."""
    background = GroupBackground.query.get_or_404(background_id)

    if not background.needs_review:
        flash("This background has already been reviewed.", "info")
        return redirect(url_for("groups.list_group_backgrounds"))

    return render_template(
        "groups/backgrounds/review.html",
        background=background,
    )


@groups_bp.route("/backgrounds/<int:background_id>/review", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["group.background_approve"])
def review_group_background_post(background_id):
    """Handle the review submission."""
    background = GroupBackground.query.get_or_404(background_id)

    if not background.needs_review:
        flash("This background has already been reviewed.", "info")
        return redirect(url_for("groups.list_group_backgrounds"))

    # Update group information
    group = background.group
    new_background = request.form.get("background", group.background)
    new_objective = request.form.get("objective", group.objective)
    new_goals = request.form.get("goals", group.goals)

    # Track changes for audit logging
    changes = []
    if group.background != new_background:
        changes.append("Background updated during review")
    if group.objective != new_objective:
        changes.append("Objective updated during review")
    if group.goals != new_goals:
        changes.append("Goals updated during review")

    group.background = new_background
    group.objective = new_objective
    group.goals = new_goals

    # Update background information
    background.background = group.background
    background.objective = group.objective
    background.goals = group.goals

    # Create audit log for background changes
    if changes:
        audit = GroupAuditLog(
            group_id=group.id,
            editor_user_id=current_user.id,
            action=GroupAuditAction.EDIT.value,
            changes="; ".join(changes),
        )
        db.session.add(audit)

    # Check if marked as done
    mark_done = request.form.get("mark_done") == "on"

    if mark_done:
        background.mark_as_reviewed(current_user.id)
        flash("Background marked as reviewed.", "success")
    else:
        flash("Background updated but still needs review.", "info")

    db.session.commit()

    return redirect(url_for("groups.list_group_backgrounds"))
