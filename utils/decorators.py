from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from models.enums import Role
from models.tools.character import Character


def roles_required(roles=None, condition_func=None):
    """
    A decorator to require a user to have one of the specified roles,
    or to satisfy a custom condition.

    :param roles: A list of role names. The user must have at least one.
    :param condition_func: A function that takes the current user and returns
                           True if the condition is met.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            # Check for roles
            has_required_role = False
            if roles:
                if any(current_user.has_role(role) for role in roles):
                    has_required_role = True

            # Check for custom condition
            custom_condition_met = False
            if condition_func:
                if condition_func(current_user):
                    custom_condition_met = True

            # If neither roles nor a condition function is provided,
            # or if the user has the role or meets the condition, allow access.
            if has_required_role or custom_condition_met:
                return f(*args, **kwargs)

            # If roles were specified but the user doesn't have them, and no custom
            # condition was met
            if roles and not custom_condition_met:
                flash(
                    f"You require one of the following roles to access this page: "
                    f"{', '.join(roles)}."
                )
                abort(403)

            # If only a custom condition was specified and not met
            if condition_func and not roles:
                flash("You do not have permission to access this page.")
                abort(403)

            # Fallback for any other case
            abort(403)

        return decorated_function

    return decorator


def admin_required(f):
    """Decorator for routes that require 'admin' or 'owner' roles."""
    return roles_required(roles=[Role.ADMIN.value])(f)


def owner_required(f):
    """Decorator for routes that require the 'owner' role."""
    return roles_required(roles=[Role.OWNER.value])(f)


def user_admin_required(f):
    """Decorator for routes that require the 'user_admin' role."""
    return roles_required(roles=[Role.USER_ADMIN.value])(f)


def has_active_character_required(f):
    """
    Decorator that checks if the current user has an active character.
    If not, redirects to the character list page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_active_character():
            flash("You need an active character to access this page.", "error")
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


def downtime_team_required(f):
    """Decorator for routes that require the 'downtime_team' role."""
    return roles_required(roles=[Role.DOWNTIME_TEAM.value])(f)


def npc_required(f):
    """Decorator for routes that require the 'npc' role."""
    return roles_required(roles=[Role.NPC.value])(f)


def rules_team_required(f):
    """Decorator for routes that require the 'rules_team' role."""
    return roles_required(roles=[Role.RULES_TEAM.value])(f)


def downtime_or_rules_team_required(f):
    """Decorator for routes that require the 'downtime_team' or 'rules_team' role."""
    return roles_required(roles=[Role.DOWNTIME_TEAM.value, Role.RULES_TEAM.value])(f)


def plot_team_required(f):
    """Decorator for routes that require the 'plot_team' role."""
    return roles_required(roles=[Role.PLOT_TEAM.value])(f)


def character_owner_or_user_admin_required(f):
    """
    Decorator that checks if the current user is a 'user_admin' or the owner of the
    character.
    It expects 'character_id' in the view arguments.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        character_id = kwargs.get("character_id")
        if not character_id:
            # This should not happen if routes are set up correctly
            abort(404)

        character = Character.query.get_or_404(character_id)

        # User is owner of the character or a user_admin
        if character.player_id == current_user.player_id or current_user.has_role(
            Role.USER_ADMIN.value
        ):
            return f(*args, **kwargs)

        abort(403)

    return decorated_function


def character_owner_or_downtime_team_required(f):
    """
    Decorator that checks if the current user is a 'downtime_team' or the owner of the
    character.
    It expects 'character_id' in the view arguments.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        character_id = kwargs.get("character_id")
        if not character_id:
            # This should not happen if routes are set up correctly
            abort(404)

        character = Character.query.get_or_404(character_id)

        # User is owner of the character or a downtime_team member
        if character.user_id == current_user.id or current_user.has_role(Role.DOWNTIME_TEAM.value):
            return f(*args, **kwargs)

        abort(403)

    return decorated_function
