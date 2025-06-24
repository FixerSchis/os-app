from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.group_type import GroupType
from models.database.sample import Sample
from models.enums import CharacterAuditAction, CharacterStatus, GroupAuditAction, Role
from models.extensions import db
from models.tools.character import Character, CharacterAuditLog
from models.tools.group import Group, GroupAuditLog, GroupInvite
from utils.decorators import (
    email_verified_required,
    has_active_character_required,
    user_admin_required,
)

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/")
@login_required
@email_verified_required
def group_list():
    # Admins can switch between admin and user view.
    # The 'admin_view' parameter will be 'false' when they switch to user view.
    admin_view_param = request.args.get("admin_view", "true")
    is_admin_and_wants_admin_view = (
        current_user.has_role(Role.USER_ADMIN.value) and admin_view_param == "true"
    )

    if is_admin_and_wants_admin_view:
        groups = Group.query.all()
        return render_template(
            "groups/admin_list.html", groups=groups, group_types=GroupType.query.all()
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
        bank_account=0,
    )
    db.session.add(group)
    db.session.flush()  # Flush to get the group ID

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
    bank_account = request.form.get("bank_account")
    admin_view = request.form.get("admin_view")
    character_id = request.form.get("character_id")

    if not name:
        flash("Name is required", "error")
        return redirect(url_for("groups.group_list"))

    # Track changes for audit log
    changes = []
    if group.name != name:
        changes.append(f"Name changed from '{group.name}' to '{name}'")

    # Only allow type changes for admins
    if current_user.has_role(Role.USER_ADMIN.value) and type and group.group_type_id != int(type):
        group_type = GroupType.query.get(type)
        changes.append(f"Type changed from '{group.group_type.name}' to '{group_type.name}'")
        group.group_type_id = int(type)

    # Handle bank account changes using centralized methods
    if current_user.has_role(Role.USER_ADMIN.value):
        if group.bank_account != bank_account:
            group.set_funds(bank_account, current_user.id, "Admin group edit")

    group.name = name

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

    # Create audit log for group disbanding
    audit_log = GroupAuditLog(
        group_id=group.id,
        editor_user_id=current_user.id,
        action=GroupAuditAction.DISBANDED.value,
        changes=f"Group disbanded by {character.name}",
    )
    db.session.add(audit_log)

    # Remove character from group
    character.group_id = None

    # Delete all invites for this group
    GroupInvite.query.filter_by(group_id=group_id).delete()

    # Delete all audit logs for this group
    GroupAuditLog.query.filter_by(group_id=group_id).delete()

    # Delete the group
    db.session.delete(group)
    db.session.commit()

    flash("Group disbanded.", "success")
    return redirect(url_for("groups.group_list", admin_view=admin_view, character_id=character_id))


@groups_bp.route("/<int:group_id>/remove/<int:character_id>", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
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
@user_admin_required
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
            available_characters=available_characters,
        )

    name = request.form.get("name")
    group_type_id = request.form.get("group_type_id")
    bank_account = request.form.get("bank_account")
    character_id = request.form.get("character_id")

    if not name or not group_type_id:
        flash("Name and group type are required", "error")
        return redirect(url_for("groups.create_group_admin"))

    group_type = GroupType.query.get(group_type_id)
    if not group_type:
        flash("Invalid group type", "error")
        return redirect(url_for("groups.create_group_admin"))

    try:
        bank_account_int = int(bank_account) if bank_account else 0
    except ValueError:
        flash("Bank account must be a number", "error")
        return redirect(url_for("groups.create_group_admin"))

    group = Group(name=name, group_type_id=group_type.id, bank_account=bank_account_int)
    db.session.add(group)
    db.session.flush()  # Flush to get the group ID

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
@user_admin_required
def edit_group_admin(group_id):
    group = Group.query.get_or_404(group_id)
    samples = Sample.query.order_by(Sample.name).all()
    assigned_sample_ids = {sample.id for sample in group.samples}
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
        samples=samples,
        assigned_sample_ids=assigned_sample_ids,
        available_characters=available_characters,
    )


@groups_bp.route("/<int:group_id>/edit/admin", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def edit_group_admin_post(group_id):
    group = Group.query.get_or_404(group_id)

    name = request.form.get("name")
    type = request.form.get("type")
    bank_account = request.form.get("bank_account")
    sample_ids = request.form.getlist("sample_ids")

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
    if current_user.has_role(Role.USER_ADMIN.value) and type and group.group_type_id != int(type):
        changes.append(f"Type changed from '{group.group_type.name}' to '{group_type.name}'")
        group.group_type_id = int(type)

    # Handle bank account changes using centralized methods
    if current_user.has_role(Role.USER_ADMIN.value):
        if group.bank_account != bank_account_int:
            group.set_funds(bank_account_int, current_user.id, "Admin group edit")

    group.name = name

    # Update samples
    if sample_ids:
        new_samples = Sample.query.filter(Sample.id.in_(sample_ids)).all()
        group.samples = new_samples
    else:
        group.samples = []

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
@user_admin_required
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
    if current_user.has_role(Role.USER_ADMIN.value):
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
