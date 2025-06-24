from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.group_type import GroupType
from models.extensions import db
from utils.decorators import rules_team_required

group_types_bp = Blueprint("group_types", __name__)


@group_types_bp.route("/")
@login_required
def list_group_types():
    """List all group types - accessible to everyone."""
    group_types = GroupType.query.order_by(GroupType.name).all()
    return render_template("database/group_types/list.html", group_types=group_types)


@group_types_bp.route("/create", methods=["GET"])
@login_required
@rules_team_required
def create_group_type():
    """Create a new group type - rules team only."""
    return render_template("database/group_types/edit.html", group_type=None)


@group_types_bp.route("/create", methods=["POST"])
@login_required
@rules_team_required
def create_group_type_post():
    """Handle group type creation - rules team only."""
    name = request.form.get("name")
    description = request.form.get("description")
    income_items_discount = (
        float(request.form.get("income_items_discount", 50)) / 100
    )  # Convert percentage to decimal
    income_substances = bool(request.form.get("income_substances"))
    income_substance_cost = int(request.form.get("income_substance_cost", 0))
    income_medicaments = bool(request.form.get("income_medicaments"))
    income_medicament_cost = int(request.form.get("income_medicament_cost", 0))

    # Parse income distribution
    items_ratio = int(request.form.get("items_ratio", 0))
    exotics_ratio = int(request.form.get("exotics_ratio", 0))
    medicaments_ratio = int(request.form.get("medicaments_ratio", 0))
    chits_ratio = int(request.form.get("chits_ratio", 0))

    income_distribution = {}
    if items_ratio > 0:
        income_distribution["items"] = items_ratio
    if exotics_ratio > 0:
        income_distribution["exotics"] = exotics_ratio
    if medicaments_ratio > 0:
        income_distribution["medicaments"] = medicaments_ratio
    if chits_ratio > 0:
        income_distribution["chits"] = chits_ratio

    if not name:
        flash("Name is required", "error")
        return redirect(url_for("group_types.create_group_type"))

    if GroupType.query.filter_by(name=name).first():
        flash("A group type with this name already exists", "error")
        return redirect(url_for("group_types.create_group_type"))

    group_type = GroupType(
        name=name,
        description=description,
        income_items_list=[],
        income_items_discount=income_items_discount,
        income_substances=income_substances,
        income_substance_cost=income_substance_cost,
        income_medicaments=income_medicaments,
        income_medicament_cost=income_medicament_cost,
        income_distribution_dict=income_distribution,
    )

    db.session.add(group_type)
    db.session.commit()

    flash("Group type created successfully", "success")
    return redirect(url_for("group_types.list_group_types"))


@group_types_bp.route("/<int:group_type_id>/edit", methods=["GET"])
@login_required
@rules_team_required
def edit_group_type(group_type_id):
    """Edit a group type - rules team only."""
    group_type = GroupType.query.get_or_404(group_type_id)
    return render_template("database/group_types/edit.html", group_type=group_type)


@group_types_bp.route("/<int:group_type_id>/edit", methods=["POST"])
@login_required
@rules_team_required
def edit_group_type_post(group_type_id):
    """Handle group type editing - rules team only."""
    group_type = GroupType.query.get_or_404(group_type_id)

    name = request.form.get("name")
    description = request.form.get("description")
    income_items_discount = (
        float(request.form.get("income_items_discount", 50)) / 100
    )  # Convert percentage to decimal
    income_substances = bool(request.form.get("income_substances"))
    income_substance_cost = int(request.form.get("income_substance_cost", 0))
    income_medicaments = bool(request.form.get("income_medicaments"))
    income_medicament_cost = int(request.form.get("income_medicament_cost", 0))

    # Parse income distribution
    items_ratio = int(request.form.get("items_ratio", 0))
    exotics_ratio = int(request.form.get("exotics_ratio", 0))
    medicaments_ratio = int(request.form.get("medicaments_ratio", 0))
    chits_ratio = int(request.form.get("chits_ratio", 0))

    income_distribution = {}
    if items_ratio > 0:
        income_distribution["items"] = items_ratio
    if exotics_ratio > 0:
        income_distribution["exotics"] = exotics_ratio
    if medicaments_ratio > 0:
        income_distribution["medicaments"] = medicaments_ratio
    if chits_ratio > 0:
        income_distribution["chits"] = chits_ratio

    if not name:
        flash("Name is required", "error")
        return redirect(url_for("group_types.edit_group_type", group_type_id=group_type_id))

    existing = GroupType.query.filter_by(name=name).first()
    if existing and existing.id != group_type_id:
        flash("A group type with this name already exists", "error")
        return redirect(url_for("group_types.edit_group_type", group_type_id=group_type_id))

    group_type.name = name
    group_type.description = description
    group_type.income_items_discount = income_items_discount
    group_type.income_substances = income_substances
    group_type.income_substance_cost = income_substance_cost
    group_type.income_medicaments = income_medicaments
    group_type.income_medicament_cost = income_medicament_cost
    group_type.income_distribution_dict = income_distribution

    db.session.commit()

    flash("Group type updated successfully", "success")
    return redirect(url_for("group_types.list_group_types"))
