from functools import wraps

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user

from models.tools.character import Character

# Legacy roles_required decorator removed - use permission_required instead


def has_active_character_required(f):
    """
    Decorator that checks if the current user has an active character.
    If not, redirects to the character list page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # This should be handled by @login_required, but as a fallback
            return redirect(url_for("auth.login", next=request.url))
        if not current_user.has_active_character():
            flash("You must have an active character to access this page.", "warning")
            return redirect(url_for("characters.character_list"))
        return f(*args, **kwargs)

    return decorated_function


def email_verified_required(f):
    """
    Decorator that checks if the current user's email is verified.
    If not, redirects to the verification required page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and not current_user.email_verified:
            flash("Please verify your email address to access this page.")
            return redirect(url_for("auth.verification_required"))
        return f(*args, **kwargs)

    return decorated_function


def character_owner_or_user_admin_required(f):
    """
    Decorator that checks if the current user is the owner of the character or has character edit permissions.
    It expects 'character_id' in the view arguments.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        character_id = kwargs.get("character_id")
        if not character_id:
            # This should not happen if routes are set up correctly
            abort(404)

        character = Character.query.get_or_404(character_id)

        # User is owner of the character or has character edit permissions
        if character.user_id == current_user.id or current_user.has_permission(
            "character.edit_all"
        ):
            return f(*args, **kwargs)

        abort(403)

    return decorated_function


def character_owner_or_downtime_team_required(f):
    """
    Decorator that checks if the current user is the owner of the character or has downtime management permissions.
    It expects 'character_id' in the view arguments.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        character_id = kwargs.get("character_id")
        if not character_id:
            # This should not happen if routes are set up correctly
            abort(404)

        character = Character.query.get_or_404(character_id)

        # User is owner of the character or has downtime management permissions
        if character.user_id == current_user.id or current_user.has_permission("downtime.manage"):
            return f(*args, **kwargs)

        abort(403)

    return decorated_function
