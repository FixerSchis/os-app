from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.permissions import Role
from models.extensions import db
from models.tools.character import Character, CharacterStatus, CharacterTag
from models.tools.user import User
from utils.decorators import email_verified_required
from utils.mask_email import mask_email
from utils.permission_decorators import permission_required

user_management_bp = Blueprint("user_management", __name__)


@user_management_bp.route("/user-management")
@login_required
@email_verified_required
@permission_required(permissions=["user.view"])
def user_management():
    users = User.query.all()
    # Check if current user has admin role (not just user_admin)
    is_admin = current_user.has_permission("user.roles")

    return render_template(
        "user_management/list.html",
        users=users,
        CharacterStatus=CharacterStatus,
        is_admin=is_admin,
        mask_email=mask_email,
    )


@user_management_bp.route("/user-management/user/<int:user_id>", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["user.view", "user.edit"])
def user_management_edit_user(user_id):
    user = User.query.get_or_404(user_id)

    # Get all roles from the database
    all_roles = Role.query.all()

    # Filter roles based on permissions
    available_roles = []
    for role in all_roles:
        if role.name == "owner" and not current_user.has_permission("user.roles"):
            continue
        if role.name == "admin" and not current_user.has_permission("user.roles"):
            continue
        available_roles.append(role)

    characters = Character.query.filter_by(user_id=user.id).all()

    factions = Faction.query.all()
    return render_template(
        "user_management/edit.html",
        user=user,
        roles=available_roles,
        character_statuses=CharacterStatus.values(),
        characters=characters,
        CharacterStatus=CharacterStatus,
        Faction=factions,
    )


@user_management_bp.route("/user-management/user/<int:user_id>", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["user.view", "user.edit"])
def user_management_edit_user_post(user_id):
    user = User.query.get_or_404(user_id)

    if "update_user" in request.form:
        # Update basic user information
        if request.form.get("email"):
            user.email = request.form.get("email")
        if request.form.get("first_name"):
            user.first_name = request.form.get("first_name")
        if request.form.get("surname"):
            user.surname = request.form.get("surname")
        if request.form.get("pronouns_subject"):
            user.pronouns_subject = request.form.get("pronouns_subject")
        if request.form.get("pronouns_object"):
            user.pronouns_object = request.form.get("pronouns_object")

        # Update character points
        character_points = request.form.get("character_points")
        if character_points is not None:
            try:
                new_cp = float(character_points)
                if new_cp < 0:
                    flash("Character points cannot be negative", "error")
                    return redirect(
                        url_for("user_management.user_management_edit_user", user_id=user.id)
                    )
                user.character_points = new_cp
            except ValueError:
                flash("Character points must be a number", "error")
                return redirect(
                    url_for("user_management.user_management_edit_user", user_id=user.id)
                )

        # Update role assignment
        role_id = request.form.get("role_id")
        if role_id:
            role = Role.query.get(role_id)
            if role:
                # Prevent users from changing their own role
                if user.id == current_user.id:
                    flash("You cannot change your own role", "error")
                    return redirect(
                        url_for("user_management.user_management_edit_user", user_id=user.id)
                    )

                # Check if this is an owner promotion
                if role.name == "owner":
                    if not current_user.has_permission("owner.promote"):
                        flash("You do not have permission to promote users to owner", "error")
                        return redirect(
                            url_for("user_management.user_management_edit_user", user_id=user.id)
                        )

                    # Find the next highest role for the current user
                    all_roles = Role.query.all()
                    roles_by_permission_count = sorted(
                        all_roles, key=lambda r: len(r.permissions), reverse=True
                    )
                    non_owner_roles = [r for r in roles_by_permission_count if r.name != "owner"]

                    if not non_owner_roles:
                        flash("No other roles available for assignment", "error")
                        return redirect(
                            url_for("user_management.user_management_edit_user", user_id=user.id)
                        )

                    next_highest_role = non_owner_roles[0]

                    # Promote the target user to owner and demote current user
                    user.role = role
                    current_user.role = next_highest_role

                    flash(
                        f"User {user.email} has been promoted to owner. "
                        f"You now have the {next_highest_role.name} role.",
                        "success",
                    )
                else:
                    # Regular role assignment
                    if role.name == "admin" and not current_user.has_permission("user.roles"):
                        flash("You do not have permission to assign the admin role", "error")
                    else:
                        user.role = role
                        flash("Role assigned successfully", "success")
            else:
                flash("Invalid role selected", "error")
        else:
            # Prevent removing roles - roles are required
            flash("A role must be assigned to all users", "error")
            return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))

        db.session.commit()

    elif "add_tag" in request.form:
        tag_id = request.form.get("tag_id")
        if tag_id:
            tag = db.session.get(CharacterTag, tag_id)
            # Use the user's active character
            active_character = (
                user.get_active_character() if hasattr(user, "get_active_character") else None
            )
            if not active_character:
                flash("User has no active character", "error")
            elif tag and tag not in active_character.tags:
                active_character.tags.append(tag)
                db.session.commit()
                flash("Tag added successfully")
    elif "remove_tag" in request.form:
        tag_id = request.form.get("tag_id")
        if tag_id:
            tag = db.session.get(CharacterTag, tag_id)
            active_character = (
                user.get_active_character() if hasattr(user, "get_active_character") else None
            )
            if not active_character:
                flash("User has no active character", "error")
            elif tag and tag in active_character.tags:
                active_character.tags.remove(tag)
                db.session.commit()
                flash("Tag removed successfully")
    elif "update_character_status" in request.form:
        character_id = request.form.get("character_id")
        new_status = request.form.get("status")
        if character_id and new_status in CharacterStatus.values():
            character = db.session.get(Character, character_id)
            if character and character.user_id == user.id:
                character.status = new_status
                db.session.commit()
                flash("Character status updated successfully")

    # Get all roles from the database
    all_roles = Role.query.all()

    # Filter roles based on permissions
    available_roles = []
    for role in all_roles:
        if role.name == "owner" and not current_user.has_permission("owner.promote"):
            continue
        if role.name == "admin" and not current_user.has_permission("user.roles"):
            continue
        available_roles.append(role)

    characters = Character.query.filter_by(user_id=user.id).all()

    return render_template(
        "user_management/edit.html",
        user=user,
        roles=available_roles,
        character_statuses=CharacterStatus.values(),
        characters=characters,
        CharacterStatus=CharacterStatus,
        Faction=Faction,
    )
