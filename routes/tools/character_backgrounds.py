from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.enums import CharacterAuditAction, Role
from models.extensions import db
from models.tools.character import Character, CharacterAuditLog, CharacterBackground
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
    new_background = request.form.get("background", character.background)
    new_goals = request.form.get("goals", character.goals)
    new_concept = request.form.get("concept", character.concept)

    # Track changes for audit logging
    changes = []
    if character.background != new_background:
        changes.append("Background updated during review")
    if character.goals != new_goals:
        changes.append("Goals updated during review")
    if character.concept != new_concept:
        changes.append("Concept updated during review")

    character.background = new_background
    character.goals = new_goals
    character.concept = new_concept

    # Update background information
    background.background = character.background
    background.goals = character.goals
    background.concept = character.concept

    # Create audit log for background changes
    if changes:
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.EDIT.value,
            changes="; ".join(changes),
        )
        db.session.add(audit)

    # Check if marked as done
    mark_done = request.form.get("mark_done") == "on"

    if mark_done:
        background.mark_as_reviewed(current_user.id)
        flash("Background marked as reviewed.", "success")
    else:
        flash("Background updated but still needs review.", "info")

    db.session.commit()

    return redirect(url_for("character_backgrounds.list_backgrounds"))
