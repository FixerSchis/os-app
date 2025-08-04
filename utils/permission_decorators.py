from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def permission_required(permissions=None, condition_func=None, on_declined=None):
    """
    Decorator to check if the current user has any of the specified permissions.

    Args:
        permissions: List of permission names to check (or single string)
        condition_func: Optional function that takes the user and route args/kwargs
                      and returns True/False
        on_declined: Optional dict with custom handling for permission denial:
            - redirect_url: URL to redirect to (default: 'index')
            - flash_message: Message to flash (default: "You don't have permission
                           to access this page.")
            - flash_category: Flash message category (default: "error")
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "error")
                return redirect(url_for("auth.login"))

            # Check condition function first if provided
            if condition_func and condition_func(current_user, args, kwargs):
                return f(*args, **kwargs)

            # Check permissions if provided
            if permissions:
                # Convert single string to list if needed
                perm_list = [permissions] if isinstance(permissions, str) else permissions
                if current_user.has_any_permission(perm_list):
                    return f(*args, **kwargs)

            # Handle permission denial with custom parameters
            if on_declined:
                redirect_url = on_declined.get("redirect_url", "index")
                flash_message = on_declined.get(
                    "flash_message", "You don't have permission to access this page."
                )
                flash_category = on_declined.get("flash_category", "error")
            else:
                redirect_url = "index"
                flash_message = "You don't have permission to access this page."
                flash_category = "error"

            flash(flash_message, flash_category)
            return redirect(url_for(redirect_url))

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
