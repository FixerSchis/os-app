from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.enums import Role
from models.extensions import db
from models.tools.character import Character, CharacterBackground
from utils.decorators import email_verified_required, user_admin_required

character_backgrounds_bp = Blueprint("character_backgrounds", __name__)


@character_backgrounds_bp.route("/")
@login_required
@email_verified_required
@user_admin_required
def list_backgrounds():
    """List all character backgrounds that need review."""
    backgrounds = CharacterBackground.query.filter_by(needs_review=True).all()

    return render_template(
        "tools/character_backgrounds/list.html",
        backgrounds=backgrounds,
    )


@character_backgrounds_bp.route("/<int:background_id>/review", methods=["GET"])
@login_required
@email_verified_required
@user_admin_required
def review_background(background_id):
    """Review a specific character background."""
    background = CharacterBackground.query.get_or_404(background_id)

    if not background.needs_review:
        flash("This background has already been reviewed.", "info")
        return redirect(url_for("character_backgrounds.list_backgrounds"))

    return render_template(
        "tools/character_backgrounds/review.html",
        background=background,
    )


@character_backgrounds_bp.route("/<int:background_id>/review", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def review_background_post(background_id):
    """Handle the review submission."""
    background = CharacterBackground.query.get_or_404(background_id)

    if not background.needs_review:
        flash("This background has already been reviewed.", "info")
        return redirect(url_for("character_backgrounds.list_backgrounds"))

    # Update character information
    character = background.character
    character.name = request.form.get("character_name", character.name)
    character.background = request.form.get("background", character.background)
    character.goals = request.form.get("goals", character.goals)
    character.concept = request.form.get("concept", character.concept)

    # Update background information
    background.background = character.background
    background.goals = character.goals
    background.concept = character.concept

    # Check if marked as done
    mark_done = request.form.get("mark_done") == "on"

    if mark_done:
        background.mark_as_reviewed(current_user.id)
        flash("Background marked as reviewed.", "success")
    else:
        flash("Background updated but still needs review.", "info")

    db.session.commit()

    return redirect(url_for("character_backgrounds.list_backgrounds"))
