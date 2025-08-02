from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def permission_required(permissions=None, condition_func=None):
    """
    Decorator to check if the current user has any of the specified permissions.

    Args:
        permissions: List of permission names to check (or single string)
        condition_func: Optional function that takes the user and returns True/False
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "error")
                return redirect(url_for("auth.login"))

            # Check condition function first if provided
            if condition_func and condition_func(current_user):
                return f(*args, **kwargs)

            # Check permissions if provided
            if permissions:
                # Convert single string to list if needed
                perm_list = [permissions] if isinstance(permissions, str) else permissions
                if current_user.has_any_permission(perm_list):
                    return f(*args, **kwargs)

            flash("You don't have permission to access this page.", "error")
            return redirect(url_for("index"))

        return decorated_function

    return decorator


def all_permissions_required(permissions):
    """
    Decorator to check if the current user has ALL of the specified permissions.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "error")
                return redirect(url_for("auth.login"))

            if current_user.has_all_permissions(permissions):
                return f(*args, **kwargs)

            flash("You don't have permission to access this page.", "error")
            return redirect(url_for("index"))

        return decorated_function

    return decorator
