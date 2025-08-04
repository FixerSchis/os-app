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
from models.enums import PrintTemplateType
from models.extensions import db
from models.tools.downtime import DowntimePack
from models.tools.print_template import PrintTemplate
from utils import generate_qr_code, generate_web_qr_code
from utils.permission_decorators import permission_required

items_bp = Blueprint("items", __name__)


@items_bp.route("/")
@login_required
@permission_required(permissions=["rules.items"])
def list():
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
        mod_counts = [(db.session.get(Mod, row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_item[item.id] = mod_counts
    for bp in blueprints.values():
        mod_rows = db.session.execute(
            item_blueprint_mods.select().where(item_blueprint_mods.c.item_blueprint_id == bp.id)
        ).fetchall()
        mod_counts = [(db.session.get(Mod, row.mod_id), row.count) for row in mod_rows]
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
@permission_required(permissions=["rules.items"])
def create():
    blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
    mods = Mod.query.order_by(Mod.name).all()
    mods_dict = [{"id": mod.id, "name": mod.name} for mod in mods]
    return render_template("rules/items/edit.html", blueprints=blueprints, mods=mods_dict)


@items_bp.route("/create", methods=["POST"])
@login_required
@permission_required(permissions=["rules.items"])
def create_post():
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

        # Create audit log for item creation
        from models.database.item import ItemAuditLog
        from models.enums import ItemAuditAction

        audit_log = ItemAuditLog(
            item_id=item.id,
            editor_user_id=current_user.id,
            action=ItemAuditAction.CREATE.value,
            changes=f"Item created with {len(mod_counts)} mod types",
        )
        db.session.add(audit_log)

        db.session.commit()
        flash("Item created successfully", "success")
        return redirect(url_for("items.list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating item: {e}", "error")
        return render_template("rules/items/edit.html", blueprints=blueprints, mods=mods_dict)


@items_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
@permission_required(permissions=["rules.items"])
def edit(id):
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
        mod_counts = [(db.session.get(Mod, row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_blueprint[bp.id] = mod_counts
    return render_template(
        "rules/items/edit.html",
        item=item,
        blueprints=[bp for bp in blueprints.values()],
        mods=mods_dict,
        initial_mods=initial_mods,
        mod_instances_by_blueprint=mod_instances_by_blueprint,
    )


@items_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
@permission_required(permissions=["rules.items"])
def edit_post(id):
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
        mod_counts = [(db.session.get(Mod, row.mod_id), row.count) for row in mod_rows]
        mod_instances_by_blueprint[bp.id] = mod_counts

    if not blueprint_id:
        flash("Blueprint is required", "error")
        return render_template(
            "rules/items/edit.html",
            item=item,
            blueprints=[bp for bp in blueprints.values()],
            mods=mods_dict,
            initial_mods=initial_mods,
            mod_instances_by_blueprint=mod_instances_by_blueprint,
        )

    try:
        # Track changes to determine if version should be incremented
        changes = []
        version_incremented = False

        # Check blueprint changes
        if item.blueprint_id != int(blueprint_id):
            changes.append(f"Blueprint changed from {item.blueprint_id} to {blueprint_id}")
            version_incremented = True

        # Check expiry changes
        new_expiry = expiry if expiry else None
        if item.expiry != new_expiry:
            changes.append(f"Expiry changed from {item.expiry} to {new_expiry}")
            version_incremented = True

        # Check mods changes
        new_mods = Counter([int(mid) for mid in mods_applied_ids])
        current_mods = Counter(initial_mods)
        if new_mods != current_mods:
            changes.append("Modifications changed")
            version_incremented = True

        # Apply changes
        item.blueprint_id = blueprint_id
        item.expiry = new_expiry
        db.session.flush()

        # Update mods
        db.session.execute(item_mods_applied.delete().where(item_mods_applied.c.item_id == item.id))
        for mod_id, count in new_mods.items():
            db.session.execute(
                text(
                    "INSERT INTO item_mods_applied "
                    "(item_id, mod_id, count) "
                    "VALUES (:iid, :mid, :count)"
                ),
                {"iid": item.id, "mid": mod_id, "count": count},
            )

        # Increment version if any non-ownership fields changed
        if version_incremented:
            item.increment_version(current_user.id, f"Item edited: {', '.join(changes)}")
        else:
            # Create audit log for edit without version increment
            from models.database.item import ItemAuditLog
            from models.enums import ItemAuditAction

            audit_log = ItemAuditLog(
                item_id=item.id,
                editor_user_id=current_user.id,
                action=ItemAuditAction.EDIT.value,
                changes="Item edited (no version increment)",
            )
            db.session.add(audit_log)

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
@permission_required(permissions=["rules.items"])
def delete(id):
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


@items_bp.route("/<int:id>/<int:version>/view")
def view(id, version):
    item = Item.query.get_or_404(id)

    # Check for version mismatch warning
    version_warning = None
    if version != item.version:
        version_warning = (
            "The item version you provided is no longer current - if you obtained this link "
            "from a QR code on game lammy, please discard it."
        )

    # Check for unprinted warning
    printed_warning = None
    if not item.printed:
        printed_warning = (
            "This item has updated and has not yet been printed. If you require an up to "
            "date copy of this lammy, please contact the Game Team"
        )

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

    # Add custom filter for QR code generation with parameters
    def qr_code_filter(data, size=10, border=2):
        return generate_qr_code(data, size=size, border=border)

    template_context["qr_code"] = qr_code_filter

    # Pre-generate the item view URL and QR code
    try:
        item_view_url = url_for("items.view", id=item.id, version=item.version, _external=True)
        template_context["item_view_url"] = item_view_url
        template_context["item_qr_code"] = generate_qr_code(item_view_url, size=3)
    except Exception:
        # Fallback if URL generation fails
        template_context["item_view_url"] = f"/db/items/{item.id}/{item.version}/view"
        template_context["item_qr_code"] = generate_qr_code(
            template_context["item_view_url"], size=3
        )

    # Render the template
    front_rendered = template.get_front_page_render(template_context)
    back_rendered = template.get_back_page_render(template_context)
    css = template.get_css_render()
    css_b64 = base64.b64encode(css.encode("utf-8")).decode("ascii")

    # Determine edit URL based on permissions
    edit_url = None
    if current_user.is_authenticated and current_user.has_permission("rules.items"):
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
        version_warning=version_warning,
        printed_warning=printed_warning,
    )


@items_bp.route("/print_unprinted")
@login_required
@permission_required(permissions=["rules.items"])
def print_unprinted_items():
    """Print all unprinted items and mark them as printed."""
    # Get all unprinted items
    unprinted_items = Item.query.filter_by(printed=False).all()

    if not unprinted_items:
        flash("No unprinted items found.", "info")
        return redirect(url_for("items.list"))

    # Get the template for item cards
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.ITEM_CARD.value).first()
    if not template:
        flash("No item card template found. Please create one first.", "error")
        return redirect(url_for("items.list"))

    # Generate PDF
    from utils.print_layout import PrintLayout

    layout_manager = PrintLayout()
    try:
        pdf = layout_manager.generate_item_cards_pdf(unprinted_items, template)
        pdf.seek(0)

        # Mark all items as printed
        for item in unprinted_items:
            item.mark_as_printed(current_user.id)

        db.session.commit()

        # Return PDF for download
        from flask import send_file

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"unprinted_items_{timestamp}.pdf"

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("items.list"))


@items_bp.route("/<int:id>/mark_unprinted", methods=["POST"])
@login_required
@permission_required(permissions=["rules.items"])
def mark_item_unprinted(id):
    """Mark a specific item as unprinted so it will be included in the next batch."""
    item = Item.query.get_or_404(id)

    if not item.printed:
        flash(f"Item {item.full_code} is already marked as unprinted.", "info")
    else:
        item.printed = False
        # Create audit log
        from models.database.item import ItemAuditLog
        from models.enums import ItemAuditAction

        audit_log = ItemAuditLog(
            item_id=item.id,
            editor_user_id=current_user.id,
            action=ItemAuditAction.PRINTED.value,
            changes="Item marked as unprinted for re-printing",
        )
        db.session.add(audit_log)
        db.session.commit()
        flash(
            f"Item {item.full_code} has been marked as unprinted and will be "
            "included in the next batch.",
            "success",
        )

    return redirect(url_for("items.list"))


@items_bp.route("/<int:id>/mark_printed", methods=["POST"])
@login_required
@permission_required(permissions=["rules.items"])
def mark_item_printed(id):
    """Mark a specific item as printed."""
    item = Item.query.get_or_404(id)

    if item.printed:
        flash(f"Item {item.full_code} is already marked as printed.", "info")
    else:
        item.mark_as_printed(current_user.id)
        db.session.commit()
        flash(f"Item {item.full_code} has been marked as printed.", "success")

    return redirect(url_for("items.list"))
