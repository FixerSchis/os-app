from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.item_type import ItemType
from models.enums import Role
from models.extensions import db

item_types_bp = Blueprint("item_types", __name__)


@item_types_bp.route("/")
def list():
    # Get all item types and order by id_prefix, then name
    item_types = ItemType.query.order_by(ItemType.id_prefix, ItemType.name).all()
    can_edit = current_user.is_authenticated and current_user.has_role(Role.RULES_TEAM.value)
    return render_template("rules/item_types/list.html", item_types=item_types, can_edit=can_edit)


@item_types_bp.route("/create", methods=["GET"])
@login_required
def create():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    return render_template("rules/item_types/edit.html")


@item_types_bp.route("/create", methods=["POST"])
@login_required
def create_post():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    name = request.form.get("name")
    id_prefix = request.form.get("id_prefix")
    if not name or not id_prefix:
        flash("Name and ID prefix are required", "error")
        return render_template("rules/item_types/edit.html")
    try:
        item_type = ItemType(name=name, id_prefix=id_prefix)
        db.session.add(item_type)
        db.session.commit()
        flash("Item type created successfully", "success")
        return redirect(url_for("item_types.list"))
    except ValueError as e:
        flash(str(e), "error")
        return render_template("rules/item_types/edit.html")
    except Exception:
        import logging

        logging.exception("Error creating item type")
        flash("An error occurred while creating the item type", "error")
        return render_template("rules/item_types/edit.html")


@item_types_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
def edit(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item_type = ItemType.query.get_or_404(id)
    return render_template("rules/item_types/edit.html", item_type=item_type)


@item_types_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
def edit_post(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item_type = ItemType.query.get_or_404(id)
    name = request.form.get("name")
    id_prefix = request.form.get("id_prefix")
    if not name or not id_prefix:
        flash("Name and ID prefix are required", "error")
        return render_template("rules/item_types/edit.html", item_type=item_type)
    try:
        item_type.name = name
        item_type.id_prefix = id_prefix
        db.session.commit()
        flash("Item type updated successfully", "success")
        return redirect(url_for("item_types.list"))
    except ValueError as e:
        flash(str(e), "error")
        return render_template("rules/item_types/edit.html", item_type=item_type)
    except Exception:
        import logging

        logging.exception("Error updating item type")
        flash("An error occurred while updating the item type", "error")
        return render_template("rules/item_types/edit.html", item_type=item_type)


@item_types_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item_type = ItemType.query.get_or_404(id)
    if item_type.blueprints and len(item_type.blueprints) > 0:
        flash(
            "Cannot delete item type with associated blueprints. "
            "Please delete or reassign the blueprints first.",
            "error",
        )
        return redirect(url_for("item_types.list"))
    try:
        db.session.delete(item_type)
        db.session.commit()
        flash("Item type deleted successfully", "success")
    except Exception:
        import logging

        logging.exception("Error deleting item type")
        flash("An error occurred while deleting the item type", "error")
    return redirect(url_for("item_types.list"))
