from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.extensions import db
from models.tools.user import User
from models.tools.character import Character, CharacterStatus, CharacterTag
from models.enums import Role
from models.database.faction import Faction
from utils.decorators import email_verified_required, user_admin_required

user_management_bp = Blueprint("user_management", __name__)

@user_management_bp.route("/user-management")
@login_required
@email_verified_required
@user_admin_required
def user_management():
    users = User.query.all()
    return render_template("user_management/list.html", users=users, Role=Role, CharacterStatus=CharacterStatus)

@user_management_bp.route("/user-management/user/<int:user_id>", methods=["GET"])
@login_required
@email_verified_required
@user_admin_required
def user_management_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    roles = [
        role
        for role in Role.values()
        if role != Role.OWNER.value and role != Role.ADMIN.value
    ]
    if current_user.has_role(Role.OWNER.value):
        roles.append(Role.ADMIN.value)

    characters = []
    if user.player_id:
        characters = Character.query.filter_by(player_id=user.player_id).all()

    factions = Faction.query.all()
    return render_template(
        "user_management/edit.html",
        user=user,
        roles=roles,
        character_statuses=CharacterStatus.values(),
        Role=Role,
        characters=characters,
        CharacterStatus=CharacterStatus,
        Faction=factions
    )

@user_management_bp.route("/user-management/user/<int:user_id>", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def user_management_edit_user_post(user_id):
    user = User.query.get_or_404(user_id)
    
    if "update_user" in request.form:
        # Update basic user information
        user.email = request.form.get("email")
        user.first_name = request.form.get("first_name")
        user.surname = request.form.get("surname")
        user.pronouns_subject = request.form.get("pronouns_subject")
        user.pronouns_object = request.form.get("pronouns_object")
        
        # Update player ID
        new_player_id = request.form.get("player_id")
        if new_player_id == '' or new_player_id is None:
            user.player_id = None
        else:
            try:
                new_player_id_int = int(new_player_id)
                if new_player_id_int != user.player_id:
                    existing_user = User.query.filter_by(player_id=new_player_id_int).first()
                    if existing_user:
                        flash("Player ID already in use", "error")
                        return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
                    user.player_id = new_player_id_int
            except (ValueError, TypeError):
                flash("Player ID must be an integer.", "error")
                return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
        
        # Update character points
        try:
            new_cp = float(request.form.get("character_points"))
            if new_cp < 0:
                flash("Character points cannot be negative", "error")
                return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
            user.character_points = new_cp
        except ValueError:
            flash("Character points must be a number", "error")
            return redirect(url_for("user_management.user_management_edit_user", user_id=user.id))
        
        db.session.commit()
        flash("User updated successfully")
        
    elif "add_role" in request.form:
        role = request.form.get("role")
        if role in Role.values():
            if role == Role.OWNER.value and not current_user.has_role(Role.OWNER.value):
                flash("You do not have permission to add the owner role")
            elif role == Role.ADMIN.value and not current_user.has_role(
                Role.OWNER.value
            ):
                flash("You do not have permission to add the admin role")
            else:
                user.add_role(role)
                db.session.commit()
                flash("Role added successfully")
    elif "remove_role" in request.form:
        role = request.form.get("role")
        if role in Role.values():
            user.remove_role(role)
            db.session.commit()
            flash("Role removed successfully")
    elif "add_tag" in request.form:
        tag_id = request.form.get("tag_id")
        if tag_id:
            tag = CharacterTag.query.get(tag_id)
            # Use the user's active character
            active_character = user.get_active_character() if hasattr(user, 'get_active_character') else None
            if not active_character:
                flash("User has no active character", "error")
            elif tag and tag not in active_character.tags:
                active_character.tags.append(tag)
                db.session.commit()
                flash("Tag added successfully")
    elif "remove_tag" in request.form:
        tag_id = request.form.get("tag_id")
        if tag_id:
            tag = CharacterTag.query.get(tag_id)
            active_character = user.get_active_character() if hasattr(user, 'get_active_character') else None
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
            character = Character.query.get(character_id)
            if character and character.player_id == user.player_id:
                character.status = new_status
                db.session.commit()
                flash("Character status updated successfully")

    roles = [
        role
        for role in Role.values()
        if role != Role.OWNER.value and role != Role.ADMIN.value
    ]
    if current_user.has_role(Role.OWNER.value):
        roles.append(Role.ADMIN.value)

    characters = []
    if user.player_id:
        characters = Character.query.filter_by(player_id=user.player_id).all()

    return render_template(
        "user_management/edit.html",
        user=user,
        roles=roles,
        character_statuses=CharacterStatus.values(),
        Role=Role,
        characters=characters,
        CharacterStatus=CharacterStatus,
        Faction=Faction
    )
