from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.item_type import ItemType
from models.database.mods import Mod
from models.extensions import db
from models.wiki import WikiPage
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required

mods_bp = Blueprint("mods", __name__)


@mods_bp.route("/")
def list():
    # Get all mods
    mods = Mod.query.all()

    # Custom sort: by count of type restrictions, then by sorted type restriction names,
    # then by name
    def mod_sort_key(mod):
        type_names = sorted([t.name for t in mod.item_types])
        return (len(type_names), type_names, mod.name)

    mods = sorted(mods, key=mod_sort_key)
    can_edit = current_user.is_authenticated and current_user.has_permission("rules.mods")
    return render_template("rules/mods/list.html", mods=mods, can_edit=can_edit)


@mods_bp.route("/new", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.mods"])
def create():
    wiki_pages = [
        {"title": page.title, "slug": page.slug}
        for page in WikiPage.query.order_by(WikiPage.title).all()
    ]
    item_types = ItemType.query.order_by(ItemType.name).all()
    return render_template("rules/mods/edit.html", wiki_pages=wiki_pages, item_types=item_types)


@mods_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.mods"])
def create_post():
    name = request.form.get("name")
    wiki_slug = request.form.get("wiki_slug")
    description = request.form.get("description", "").strip()
    item_type_ids = request.form.getlist("item_types")

    if not all([name, wiki_slug]):
        flash("Name and wiki page are required", "error")
        wiki_pages = [
            {"title": page.title, "slug": page.slug}
            for page in WikiPage.query.order_by(WikiPage.title).all()
        ]
        item_types = ItemType.query.order_by(ItemType.name).all()
        return render_template("rules/mods/edit.html", wiki_pages=wiki_pages, item_types=item_types)

    mod = Mod(name=name, wiki_slug=wiki_slug, description=description if description else None)

    if item_type_ids:
        mod.item_types = ItemType.query.filter(ItemType.id.in_(item_type_ids)).all()

    db.session.add(mod)
    db.session.commit()

    flash("Mod created successfully", "success")
    return redirect(url_for("mods.list"))


@mods_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.mods"])
def edit(id):
    mod = Mod.query.get_or_404(id)
    wiki_pages = [
        {"title": page.title, "slug": page.slug}
        for page in WikiPage.query.order_by(WikiPage.title).all()
    ]
    item_types = ItemType.query.order_by(ItemType.name).all()
    return render_template(
        "rules/mods/edit.html", mod=mod, wiki_pages=wiki_pages, item_types=item_types
    )


@mods_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.mods"])
def edit_post(id):
    mod = Mod.query.get_or_404(id)

    name = request.form.get("name")
    wiki_slug = request.form.get("wiki_slug")
    description = request.form.get("description", "").strip()
    item_type_ids = request.form.getlist("item_types")

    if not all([name, wiki_slug]):
        flash("Name and wiki page are required", "error")
        wiki_pages = [
            {"title": page.title, "slug": page.slug}
            for page in WikiPage.query.order_by(WikiPage.title).all()
        ]
        item_types = ItemType.query.order_by(ItemType.name).all()
        return render_template(
            "rules/mods/edit.html", mod=mod, wiki_pages=wiki_pages, item_types=item_types
        )

    mod.name = name
    mod.wiki_slug = wiki_slug
    mod.description = description if description else None

    if item_type_ids:
        mod.item_types = ItemType.query.filter(ItemType.id.in_(item_type_ids)).all()
    else:
        mod.item_types = []

    db.session.commit()

    flash("Mod updated successfully", "success")
    return redirect(url_for("mods.list"))
