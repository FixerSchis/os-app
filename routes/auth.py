from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.database.cybernetic import CharacterCybernetic, Cybernetic
from models.database.faction import Faction
from models.database.mods import Mod
from models.database.skills import Skill
from models.database.species import Species
from models.enums import CharacterStatus, Role, TicketType
from models.event import Event
from models.extensions import db
from models.tools.character import Character, CharacterSkill
from models.tools.event_ticket import EventTicket
from models.tools.user import User
from utils.email import send_password_reset_email, send_verification_email

auth_bp = Blueprint("auth", __name__)


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
        user = User(
            email=email,
            first_name=first_name,
            surname=surname,
        )
        user.set_password(password)
        if User.query.count() == 0:
            user.add_role(Role.OWNER.value)
            user.player_id = 1  # Set player ID to 1 for the first user
            user.email_verified = True  # First user is automatically verified
            db.session.add(user)

            # Create a default character for the user
            species = Species.query.filter_by(name="Ascendancy Terran").first()
            faction = Faction.query.filter_by(name="Terran Ascendancy").first()
            mod = Mod.query.first()
            character = Character(
                name="Default Character",
                user_id=user.id,
                character_id=1,
                status=CharacterStatus.ACTIVE.value,
                species_id=species.id,
                faction_id=faction.id,
                known_modifications=[mod.id],
            )
            db.session.add(character)

            for skill in Skill.query.all():
                character_skill = CharacterSkill(
                    character_id=character.id,
                    skill_id=skill.id,
                    times_purchased=1,
                    purchased_at=datetime.now(timezone.utc),
                    purchased_by_user_id=user.id,
                )
                if skill.name == "Engineering":
                    character_skill.times_purchased = 3
                db.session.add(character_skill)

            cybernetic = Cybernetic.query.filter_by(name="Neural Interface").first()
            character_cybernetic = CharacterCybernetic(
                character_id=character.id,
                cybernetic_id=cybernetic.id,
            )
            db.session.add(character_cybernetic)
            db.session.flush()

            prev_event = Event.query.filter_by(event_number="1").first()
            ticket = EventTicket(
                event_id=prev_event.id,
                character_id=character.id,
                ticket_type=TicketType.ADULT.value,
                price_paid=prev_event.standard_ticket_price,
                meal_ticket=False,
                requires_bunk=False,
                assigned_by_id=user.id,
                assigned_at=datetime.now(timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()

        else:
            # Get the highest player_id and add 1
            highest_id = db.session.query(db.func.max(User.player_id)).scalar() or 0
            user.player_id = highest_id + 1
            db.session.add(user)
            # Send verification email
            try:
                send_verification_email(user)
                flash(
                    "A verification email has been sent to your email address. "
                    "Please check your inbox."
                )
            except Exception as e:
                flash(f"Failed to send verification email: {str(e)}")

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


@auth_bp.route("/logout")
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
    except Exception as e:
        flash(f"Failed to send verification email: {str(e)}")

    return redirect(url_for("auth.verification_required"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
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
            except Exception as e:
                flash(f"Failed to send password reset email: {str(e)}", "error")
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
    if not user or user.reset_token_expires < datetime.now(timezone.utc):
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
