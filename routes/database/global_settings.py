from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.global_settings import GlobalSettings
from models.extensions import db
from utils.decorators import rules_team_required

global_settings_bp = Blueprint("global_settings", __name__)


@global_settings_bp.route("/")
@login_required
def list_global_settings():
    """List global settings - accessible to everyone."""
    settings = GlobalSettings.query.first()
    return render_template("database/global_settings/list.html", settings=settings)


@global_settings_bp.route("/edit", methods=["GET"])
@login_required
@rules_team_required
def edit_global_settings():
    """Edit global settings - rules team only."""
    settings = GlobalSettings.query.first()
    if not settings:
        # Create default settings if none exist
        settings = GlobalSettings.create_default_settings()
        db.session.add(settings)
        db.session.commit()

    return render_template("database/global_settings/edit.html", settings=settings)


@global_settings_bp.route("/edit", methods=["POST"])
@login_required
@rules_team_required
def edit_global_settings_post():
    """Handle global settings editing - rules team only."""
    settings = GlobalSettings.query.first()
    if not settings:
        settings = GlobalSettings.create_default_settings()
        db.session.add(settings)

    try:
        settings.character_income_ec = int(request.form.get("character_income_ec", 0))
        settings.group_income_contribution = int(request.form.get("group_income_contribution", 0))
    except ValueError:
        flash("Income values must be valid numbers", "error")
        return redirect(url_for("global_settings.edit_global_settings"))

    db.session.commit()
    flash("Global settings updated successfully", "success")
    return redirect(url_for("global_settings.list_global_settings"))
