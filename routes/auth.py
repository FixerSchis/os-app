from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.database.permissions import Role
from models.extensions import db
from models.tools.user import User
from utils.email import send_password_reset_email, send_verification_email
from utils.rate_limit import rate_limiter

auth_bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8


def password_policy_error(password):
    """Return an error message when a password is empty or too short."""
    if not password:
        return "Password is required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return None


def _client_is_limited(scope):
    """Return True when this address has exceeded the limit for a POST."""
    if not current_app.config.get("RATELIMIT_ENABLED", True):
        return False

    limits = {
        "login": ("AUTH_LOGIN_LIMIT", "AUTH_LOGIN_WINDOW_SECONDS", 10, 60),
        "forgot_password": (
            "AUTH_FORGOT_PASSWORD_LIMIT",
            "AUTH_FORGOT_PASSWORD_WINDOW_SECONDS",
            5,
            3600,
        ),
    }
    limit_key, window_key, default_limit, default_window = limits[scope]
    limit = current_app.config.get(limit_key, default_limit)
    window = current_app.config.get(window_key, default_window)
    address = request.remote_addr or "unknown"
    return not rate_limiter.allow(f"{scope}:{address}", limit, window)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        surname = request.form.get("surname")
        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for("auth.register"))
        password_error = password_policy_error(password)
        if password_error:
            flash(password_error)
            return render_template("auth/register.html")
        user = User(
            email=email,
            first_name=first_name,
            surname=surname,
        )
        user.set_password(password)

        if User.query.count() == 0:
            # First user gets owner role
            owner_role = Role.query.filter_by(name="owner").first()
            if owner_role:
                user.role = owner_role
            user.email_verified = True  # First user is automatically verified
            db.session.add(user)

        else:
            # Subsequent users get default role
            default_role = Role.query.filter_by(name="default").first()
            if default_role:
                user.role = default_role
            db.session.add(user)
            # Send verification email
            try:
                send_verification_email(user)
                flash(
                    "A verification email has been sent to your email address. "
                    "Please check your inbox."
                )
            except Exception:
                current_app.logger.exception("Failed to send verification email")
                flash("Failed to send verification email. Please try again later.")

        db.session.commit()
        login_user(user)

        if user.email_verified:
            flash("Registration successful!")
            return redirect(url_for("index"))
        else:
            return redirect(url_for("auth.verification_required"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if _client_is_limited("login"):
            flash("Too many login attempts. Please try again later.")
            return render_template("auth/login.html"), 429
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if not user.email_verified:
                return redirect(url_for("auth.verification_required"))
            return redirect(url_for("index"))
        flash("Invalid email or password")
    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@auth_bp.route("/verify/<token>")
def verify_email(token):
    if current_user.is_authenticated:
        user = current_user
        if user.email_verified:
            flash("Your email is already verified.")
            return redirect(url_for("index"))

        if user.verify_email(token):
            db.session.commit()
            flash("Your email has been verified. Thank you!")
            return redirect(url_for("index"))
        else:
            flash("The verification link is invalid or has expired.")
            return redirect(url_for("auth.verification_required"))
    else:
        # Handle case where user is not logged in
        user = User.query.filter_by(verification_token=token).first()
        if user and user.verify_email(token):
            db.session.commit()
            login_user(user)
            flash("Your email has been verified. Thank you!")
            return redirect(url_for("index"))
        else:
            flash("The verification link is invalid or has expired.")
            return redirect(url_for("auth.login"))


@auth_bp.route("/verification-required")
def verification_required():
    if current_user.is_authenticated and not current_user.email_verified:
        return render_template("auth/verification_required.html")
    elif current_user.is_authenticated:
        return redirect(url_for("index"))
    else:
        return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification")
@login_required
def resend_verification():
    if current_user.email_verified:
        flash("Your email is already verified.")
        return redirect(url_for("index"))

    try:
        send_verification_email(current_user)
        db.session.commit()
        flash("A new verification email has been sent. Please check your inbox.")
    except Exception:
        current_app.logger.exception("Failed to send verification email")
        flash("Failed to send verification email. Please try again later.")

    return redirect(url_for("auth.verification_required"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        if _client_is_limited("forgot_password"):
            flash("Too many password reset attempts. Please try again later.", "error")
            return render_template("auth/forgot_password.html"), 429
        email = request.form.get("email")
        if not email:
            flash("Email is required", "error")
            return render_template("auth/forgot_password.html")

        user = User.query.filter_by(email=email).first()
        if user:
            try:
                send_password_reset_email(user)
                db.session.commit()
                flash(
                    "A password reset email has been sent. Please check your inbox.",
                    "success",
                )
            except Exception:
                current_app.logger.exception("Failed to send password reset email")
                flash(
                    "Failed to send password reset email. Please try again later.",
                    "error",
                )
        else:
            # Don't reveal that the email doesn't exist, just show the same message
            flash(
                "A password reset email has been sent if this email is registered.",
                "info",
            )

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Find user by reset token
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires:
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.login"))

    # Ensure both datetimes are timezone-aware for comparison
    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires < datetime.now(timezone.utc):
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not password or not confirm_password:
            flash("Both password fields are required", "error")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("auth/reset_password.html", token=token)

        password_error = password_policy_error(password)
        if password_error:
            flash(password_error, "error")
            return render_template("auth/reset_password.html", token=token)

        if user.reset_password(token, password):
            db.session.commit()
            flash(
                "Your password has been reset successfully. "
                "You can now log in with your new password.",
                "success",
            )
            return redirect(url_for("auth.login"))
        else:
            flash("There was an error resetting your password.", "error")
            return redirect(url_for("auth.forgot_password"))

    return render_template("auth/reset_password.html", token=token)
