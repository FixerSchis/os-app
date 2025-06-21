import base64
import re
from collections import Counter
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_, text
from sqlalchemy.orm import aliased

from models.database.item import Item, item_mods_applied
from models.database.item_blueprint import ItemBlueprint, item_blueprint_mods
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.enums import PrintTemplateType, Role
from models.extensions import db
from models.tools.downtime import DowntimePack
from models.tools.print_template import PrintTemplate
from utils import generate_qr_code, generate_web_qr_code

items_bp = Blueprint("items", __name__)


@items_bp.route("/")
@login_required
def list():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    # Get query parameters
    sort_by = request.args.get("sort_by", "item_id")
    sort_order = request.args.get("sort_order", "asc")
    item_type_id = request.args.get("item_type_id", type=int)
    blueprint_id = request.args.get("blueprint_id", type=int)
    mod_id = request.args.get("mod_id", type=int)
    expiry_filter = request.args.get("expiry", "all")
    search = request.args.get("search", "")

    # Aliases for joins
    BP = aliased(ItemBlueprint)
    IT = aliased(ItemType)

    # Always join BP and IT once
    query = Item.query.join(BP, Item.blueprint_id == BP.id).join(IT, BP.item_type_id == IT.id)

    # Apply filters
    if item_type_id:
        query = query.filter(BP.item_type_id == item_type_id)
    if blueprint_id:
        query = query.filter(Item.blueprint_id == blueprint_id)
    if mod_id:
        query = query.outerjoin(item_mods_applied, item_mods_applied.c.item_id == Item.id)
        query = query.outerjoin(
            item_blueprint_mods, item_blueprint_mods.c.item_blueprint_id == BP.id
        )
        query = query.filter(
            or_(
                item_mods_applied.c.mod_id == mod_id,
                item_blueprint_mods.c.mod_id == mod_id,
            )
        )
    if expiry_filter == "expired":
        query = query.filter(Item.expiry < datetime.now())
    elif expiry_filter == "active":
        query = query.filter(Item.expiry >= datetime.now())
    elif expiry_filter == "none":
        query = query.filter(Item.expiry is None)

    # Apply search
    if search:
        # Remove SQL search, do it in Python after fetching items
        pass

    # Apply sorting
    if sort_by == "item_id":
        query = query.order_by(
            IT.id_prefix,
            BP.blueprint_id,
            Item.item_id if sort_order == "asc" else Item.item_id.desc(),
        )
    elif sort_by == "blueprint":
        query = query.order_by(BP.name if sort_order == "asc" else BP.name.desc())
    elif sort_by == "expiry":
        query = query.order_by(Item.expiry if sort_order == "asc" else Item.expiry.desc())

    items = query.all()
    if search:
        items = [item for item in items if search.lower() in item.full_code.lower()]

    blueprints = {bp.id: bp for bp in ItemBlueprint.query.all()}
    item_types = ItemType.query.order_by(ItemType.name).all()
    mods = Mod.query.order_by(Mod.name).all()

    # Get mod instances for items and blueprints
    mod_instances_by_item = {}
    mod_instances_by_blueprint = {}
    for item in items:
        mod_rows = db.session.execute(
            item_mods_applied.select().where(item_mods_applied.c.item_id == item.id)
        ).fetchall()
        mod_counts = [(Mod.query.get(row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_item[item.id] = mod_counts
    for bp in blueprints.values():
        mod_rows = db.session.execute(
            item_blueprint_mods.select().where(item_blueprint_mods.c.item_blueprint_id == bp.id)
        ).fetchall()
        mod_counts = [(Mod.query.get(row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_blueprint[bp.id] = mod_counts

    return render_template(
        "rules/items/list.html",
        items=items,
        blueprints=blueprints,
        item_types=item_types,
        mods=mods,
        mod_instances_by_item=mod_instances_by_item,
        mod_instances_by_blueprint=mod_instances_by_blueprint,
        sort_by=sort_by,
        sort_order=sort_order,
        item_type_id=item_type_id,
        blueprint_id=blueprint_id,
        mod_id=mod_id,
        expiry_filter=expiry_filter,
        search=search,
        now=datetime.now(),
    )


@items_bp.route("/create", methods=["GET"])
@login_required
def create():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    return render_template("rules/items/edit.html", blueprints=blueprints, mods=mods_dict)


@items_bp.route("/create", methods=["POST"])
@login_required
def create_post():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    blueprint_id = request.form.get("blueprint_id")
    expiry = request.form.get("expiry")
    mods_applied_ids = request.form.getlist("mods_applied[]")
    if not blueprint_id:
        flash("Blueprint is required", "error")
        return render_template("rules/items/edit.html", blueprints=blueprints, mods=mods_dict)
    try:
        # Auto-increment item_id for this blueprint
        max_item = (
            Item.query.filter_by(blueprint_id=blueprint_id).order_by(Item.item_id.desc()).first()
        )
        next_item_id = (max_item.item_id + 1) if max_item else 1
        item = Item(
            blueprint_id=blueprint_id,
            item_id=next_item_id,
            expiry=expiry if expiry else None,
        )
        db.session.add(item)
        db.session.flush()
        mod_counts = Counter([int(mid) for mid in mods_applied_ids])
        for mod_id, count in mod_counts.items():
            db.session.execute(
                text(
                    "INSERT INTO item_mods_applied "
                    "(item_id, mod_id, count) "
                    "VALUES (:iid, :mid, :count)"
                ),
                {"iid": item.id, "mid": mod_id, "count": count},
            )
        db.session.commit()
        flash("Item created successfully", "success")
        return redirect(url_for("items.list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating item: {e}", "error")
        return render_template("rules/items/edit.html", blueprints=blueprints, mods=mods_dict)


@items_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
def edit(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item = Item.query.get_or_404(id)
    blueprints = {bp.id: bp for bp in ItemBlueprint.query.all()}
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    mod_rows = db.session.execute(
        item_mods_applied.select().where(item_mods_applied.c.item_id == item.id)
    ).fetchall()
    initial_mods = []
    for row in mod_rows:
        initial_mods.extend([row.mod_id] * row.count)
    mod_instances_by_blueprint = {}
    for bp in blueprints.values():
        mod_rows = db.session.execute(
            item_blueprint_mods.select().where(item_blueprint_mods.c.item_blueprint_id == bp.id)
        ).fetchall()
        mod_counts = [(Mod.query.get(row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_blueprint[bp.id] = mod_counts
    return render_template(
        "rules/items/edit.html",
        item=item,
        blueprints=blueprints,
        mods=mods_dict,
        initial_mods=initial_mods,
        mod_instances_by_blueprint=mod_instances_by_blueprint,
    )


@items_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
def edit_post(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item = Item.query.get_or_404(id)
    blueprints = {bp.id: bp for bp in ItemBlueprint.query.all()}
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    mod_rows = db.session.execute(
        item_mods_applied.select().where(item_mods_applied.c.item_id == item.id)
    ).fetchall()
    blueprint_id = request.form.get("blueprint_id")
    expiry = request.form.get("expiry")
    mods_applied_ids = request.form.getlist("mods_applied[]")

    initial_mods = []
    for row in mod_rows:
        initial_mods.extend([row.mod_id] * row.count)
    mod_instances_by_blueprint = {}
    for bp in blueprints.values():
        mod_rows = db.session.execute(
            item_blueprint_mods.select().where(item_blueprint_mods.c.item_blueprint_id == bp.id)
        ).fetchall()
        mod_counts = [(Mod.query.get(row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_blueprint[bp.id] = mod_counts

    if not blueprint_id:
        flash("Blueprint is required", "error")
        return render_template(
            "rules/items/edit.html",
            item=item,
            blueprints=blueprints,
            mods=mods_dict,
            initial_mods=initial_mods,
            mod_instances_by_blueprint=mod_instances_by_blueprint,
        )
    try:
        item.blueprint_id = blueprint_id
        item.expiry = expiry if expiry else None
        db.session.flush()
        db.session.execute(item_mods_applied.delete().where(item_mods_applied.c.item_id == item.id))
        mod_counts = Counter([int(mid) for mid in mods_applied_ids])
        for mod_id, count in mod_counts.items():
            db.session.execute(
                text(
                    "INSERT INTO item_mods_applied "
                    "(item_id, mod_id, count) "
                    "VALUES (:iid, :mid, :count)"
                ),
                {"iid": item.id, "mid": mod_id, "count": count},
            )
        db.session.commit()
        flash("Item updated successfully", "success")
        return redirect(url_for("items.list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating item: {e}", "error")
        return render_template(
            "rules/items/edit.html",
            item=item,
            blueprints=blueprints,
            mods=mods_dict,
            initial_mods=initial_mods,
            mod_instances_by_blueprint=mod_instances_by_blueprint,
        )


@items_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    item = Item.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {e}", "error")
    return redirect(url_for("items.list"))


@items_bp.route("/find_by_code", methods=["POST", "GET"])
def find_by_code():
    full_code = request.values.get("full_code")
    requires_pack = request.values.get("requires_pack", "false").lower() in [
        "1",
        "true",
        "yes",
    ]
    if not full_code:
        return jsonify({"error": "Missing full_code"}), 400
    # Match format: 2 letters, 4 digits, hyphen, 3 digits
    m = re.match(r"^([A-Za-z]{2})(\d{4})-(\d{3})$", full_code)
    if not m:
        return jsonify({"error": "Item not found"}), 404
    type_prefix, blueprint_id_str, item_id_str = m.groups()
    blueprint_id = int(blueprint_id_str)
    item_id = int(item_id_str)
    # Find the item type first
    item_type = ItemType.query.filter_by(id_prefix=type_prefix).first()
    if not item_type:
        return jsonify({"error": "Item not found"}), 404
    # Find the blueprint first
    blueprint = ItemBlueprint.query.filter_by(
        item_type_id=item_type.id, blueprint_id=blueprint_id
    ).first()
    if not blueprint:
        return jsonify({"error": "Item not found"}), 404
    # Find the item
    item = Item.query.filter_by(blueprint_id=blueprint.id, item_id=item_id).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404
    # If requires_pack, check if item is in any DowntimePack's items list
    if requires_pack:
        packs_with_item = DowntimePack.query.filter(
            DowntimePack.items.contains([str(item.id)])
        ).all()
        if not packs_with_item:
            return jsonify({"error": "Item not found in any pack"}), 404
    return jsonify({"id": item.id, "name": blueprint.name, "full_code": item.full_code})


@items_bp.route("/engineering_cost", methods=["POST"])
def engineering_cost():
    data = request.get_json() or request.form
    action = data.get("action")
    item_id = data.get("item_id")
    blueprint_id = data.get("blueprint_id")
    try:
        mods = int(data.get("mods", 0))
    except (TypeError, ValueError):
        mods = 0

    if item_id:
        item = Item.query.get_or_404(item_id)
        if action == "maintain":
            cost = item.get_maintenance_cost()
            return jsonify({"cost": cost})
        elif action == "modify":
            mod_count = len(item.mods_applied) + mods
            cost = item.get_modification_cost(mod_count)
            return jsonify({"cost": cost})
        else:
            return jsonify({"error": "Invalid action"}), 400
    elif blueprint_id:
        blueprint = ItemBlueprint.query.get_or_404(blueprint_id)
        if action == "maintain":
            cost = blueprint.get_maintenance_cost(mods)
            return jsonify({"cost": cost})
        elif action == "modify":
            cost = blueprint.get_modification_cost(mods)
            return jsonify({"cost": cost})
        else:
            return jsonify({"error": "Invalid action"}), 400
    else:
        return jsonify({"error": "No item_id or blueprint_id provided"}), 400


@items_bp.route("/<int:id>/view")
def view(id):
    item = Item.query.get_or_404(id)

    # Get the item card template
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.ITEM_CARD.value).first()

    if not template:
        flash("Item card template not found.", "error")
        return redirect(url_for("items.list"))

    # Prepare template context
    template_context = {
        "item": item,
        "generate_qr_code": generate_qr_code,
        "generate_web_qr_code": generate_web_qr_code,
    }

    # Render the template
    front_rendered = template.get_front_page_render(template_context)
    back_rendered = template.get_back_page_render(template_context)
    css = template.get_css_render()
    css_b64 = base64.b64encode(css.encode("utf-8")).decode("ascii")

    # Determine edit URL based on permissions
    edit_url = None
    if current_user.is_authenticated and current_user.has_role("rules_team"):
        edit_url = url_for("items.edit", id=item.id)

    return render_template(
        "templates/view.html",
        title=f"{item.full_code} - Item Card",
        template=template,
        front_rendered=front_rendered,
        back_rendered=back_rendered,
        edit_url=edit_url,
        back_url=url_for("items.list"),
        css_b64=css_b64,
        item=item,
    )
