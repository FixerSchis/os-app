from collections import Counter

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import text

from models.database.item_blueprint import ItemBlueprint, item_blueprint_mods
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.enums import Role
from models.extensions import db

item_blueprints_bp = Blueprint("item_blueprints", __name__)


@item_blueprints_bp.route("/")
def list():
    # Get all blueprints
    blueprints = ItemBlueprint.query.all()

    # Sort by item type prefix, then blueprint ID, then base cost, then name
    def blueprint_sort_key(bp):
        return (
            bp.item_type.id_prefix if bp.item_type else "",
            bp.blueprint_id,
            bp.base_cost,
            bp.name,
        )

    blueprints = sorted(blueprints, key=blueprint_sort_key)
    can_edit = current_user.is_authenticated and current_user.has_role(Role.RULES_TEAM.value)

    # Fetch all mod instances for each blueprint
    mod_instances_by_blueprint = {}
    for bp in blueprints:
        mod_rows = db.session.execute(
            item_blueprint_mods.select().where(item_blueprint_mods.c.item_blueprint_id == bp.id)
        ).fetchall()
        # List of (mod, count) tuples
        mod_counts = [(db.session.get(Mod, row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_blueprint[bp.id] = mod_counts

    return render_template(
        "rules/item_blueprints/list.html",
        blueprints=blueprints,
        can_edit=can_edit,
        mod_instances_by_blueprint=mod_instances_by_blueprint,
    )


@item_blueprints_bp.route("/create", methods=["GET"])
@login_required
def create():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item_types = ItemType.query.order_by(ItemType.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    # Convert mods to dictionaries for JSON serialization
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    return render_template("rules/item_blueprints/edit.html", item_types=item_types, mods=mods_dict)


@item_blueprints_bp.route("/create", methods=["POST"])
@login_required
def create_post():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item_types = ItemType.query.order_by(ItemType.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    name = request.form.get("name")
    item_type_id = request.form.get("item_type_id")
    base_cost = request.form.get("base_cost")
    mods_applied_ids = request.form.getlist("mods_applied[]")
    if not name or not item_type_id or not base_cost:
        flash("All fields are required", "error")
        return render_template(
            "rules/item_blueprints/edit.html", item_types=item_types, mods=mods_dict
        )
    try:
        item_type = db.session.get(ItemType, item_type_id)
        if not item_type:
            flash("Invalid item type", "error")
            return render_template(
                "rules/item_blueprints/edit.html", item_types=item_types, mods=mods_dict
            )
        # Get the id_prefix of the current item type
        current_prefix = item_type.id_prefix
        # Find all item types with the same prefix
        same_prefix_types = ItemType.query.filter(ItemType.id_prefix == current_prefix).all()
        same_prefix_type_ids = [t.id for t in same_prefix_types]
        # Query existing blueprints with the same prefix to determine the next
        # blueprint_id
        existing_blueprints = ItemBlueprint.query.filter(
            ItemBlueprint.item_type_id.in_(same_prefix_type_ids)
        ).all()
        if existing_blueprints:
            blueprint_id = max(bp.blueprint_id for bp in existing_blueprints) + 1
        else:
            blueprint_id = 1
        blueprint = ItemBlueprint(
            name=name,
            item_type_id=item_type_id,
            blueprint_id=blueprint_id,
            base_cost=int(base_cost),
        )
        db.session.add(blueprint)
        db.session.flush()
        # Group mod IDs and insert with count
        mod_counts = Counter([int(mid) for mid in mods_applied_ids])
        for mod_id, count in mod_counts.items():
            db.session.execute(
                text(
                    "INSERT INTO item_blueprint_mods "
                    "(item_blueprint_id, mod_id, count) "
                    "VALUES (:bid, :mid, :count)"
                ),
                {"bid": blueprint.id, "mid": mod_id, "count": count},
            )
        db.session.commit()
        flash("Item blueprint created successfully", "success")
        return redirect(url_for("item_blueprints.list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating blueprint: {e}", "error")
        return render_template(
            "rules/item_blueprints/edit.html", item_types=item_types, mods=mods_dict
        )


@item_blueprints_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
def edit(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    blueprint = ItemBlueprint.query.get_or_404(id)
    item_types = ItemType.query.order_by(ItemType.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    from models.database.item_blueprint import item_blueprint_mods

    mod_rows = db.session.execute(
        item_blueprint_mods.select().where(item_blueprint_mods.c.item_blueprint_id == blueprint.id)
    ).fetchall()
    # For the edit form, expand to a flat list of mod_ids for each count
    initial_mods = []
    for row in mod_rows:
        initial_mods.extend([row.mod_id] * row.count)
    return render_template(
        "rules/item_blueprints/edit.html",
        blueprint=blueprint,
        item_types=item_types,
        mods=mods_dict,
        initial_mods=initial_mods,
    )


@item_blueprints_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
def edit_post(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    blueprint = ItemBlueprint.query.get_or_404(id)
    item_types = ItemType.query.order_by(ItemType.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    name = request.form.get("name")
    item_type_id = request.form.get("item_type_id")
    blueprint_id = request.form.get("blueprint_id")
    base_cost = request.form.get("base_cost")
    mods_applied_ids = request.form.getlist("mods_applied[]")
    if not name or not item_type_id or not blueprint_id or not base_cost:
        flash("All fields are required", "error")
        return render_template(
            "rules/item_blueprints/edit.html",
            blueprint=blueprint,
            item_types=item_types,
            mods=mods_dict,
        )
    try:
        blueprint.name = name
        blueprint.item_type_id = item_type_id
        blueprint.blueprint_id = int(blueprint_id)
        blueprint.base_cost = int(base_cost)
        db.session.flush()
        # Remove all current mods_applied using ORM delete
        db.session.execute(
            item_blueprint_mods.delete().where(
                item_blueprint_mods.c.item_blueprint_id == blueprint.id
            )
        )
        # Group mod IDs and insert with count
        mod_counts = Counter([int(mid) for mid in mods_applied_ids])
        for mod_id, count in mod_counts.items():
            db.session.execute(
                text(
                    "INSERT INTO item_blueprint_mods "
                    "(item_blueprint_id, mod_id, count) "
                    "VALUES (:bid, :mid, :count)"
                ),
                {"bid": blueprint.id, "mid": mod_id, "count": count},
            )
        db.session.commit()
        flash("Item blueprint updated successfully", "success")
        return redirect(url_for("item_blueprints.list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating blueprint: {e}", "error")
        return render_template(
            "rules/item_blueprints/edit.html",
            blueprint=blueprint,
            item_types=item_types,
            mods=mods_dict,
        )


@item_blueprints_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    blueprint = ItemBlueprint.query.get_or_404(id)
    try:
        db.session.delete(blueprint)
        db.session.commit()
        flash("Item blueprint deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting blueprint: {e}", "error")
    return redirect(url_for("item_blueprints.list"))
