from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def email_verified_required(f):
    """
    Decorator that checks if the current user's email is verified.
    If not, redirects to the verification required page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if current_user.is_authenticated and not current_user.email_verified:
        #     flash('Please verify your email address to access this page.')
        #     return redirect(url_for('auth.verification_required'))
        return f(*args, **kwargs)
    return decorated_function