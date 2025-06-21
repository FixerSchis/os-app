from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role_name):
                flash(f"You need the {role_name} role to access this page.")
                return redirect(url_for("index"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# For backward compatibility
def admin_required(f):
    return role_required("admin")(f)
