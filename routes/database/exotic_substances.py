from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.exotic_substances import ExoticSubstance
from models.enums import ScienceType
from models.extensions import db
from models.wiki import WikiPage
from utils.decorators import email_verified_required

exotic_substances_bp = Blueprint("exotic_substances", __name__)


@exotic_substances_bp.route("/")
def list():
    # Get all substances and order by type and name
    substances = ExoticSubstance.query.order_by(ExoticSubstance.type, ExoticSubstance.name).all()
    can_edit = current_user.is_authenticated and current_user.has_role("rules_team")
    type_friendly_names = ScienceType.descriptions()
    return render_template(
        "rules/exotic_substances/list.html",
        substances=substances,
        can_edit=can_edit,
        type_friendly_names=type_friendly_names,
    )


@exotic_substances_bp.route("/new", methods=["GET"])
@login_required
@email_verified_required
def create():
    if not current_user.has_role("rules_team"):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    types = [t for t in ScienceType]
    wiki_pages = [
        {"title": page.title, "slug": page.slug}
        for page in WikiPage.query.order_by(WikiPage.title).all()
    ]
    return render_template(
        "rules/exotic_substances/edit.html",
        types=types,
        wiki_pages=wiki_pages,
        ScienceType=ScienceType,
    )


@exotic_substances_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
def create_post():
    if not current_user.has_role("rules_team"):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    name = request.form.get("name")
    substance_type = request.form.get("type")
    wiki_slug = request.form.get("wiki_slug")

    if not all([name, substance_type, wiki_slug]):
        flash("All fields are required", "error")
        types = [t for t in ScienceType]
        wiki_pages = [
            {"title": page.title, "slug": page.slug}
            for page in WikiPage.query.order_by(WikiPage.title).all()
        ]
        return render_template(
            "rules/exotic_substances/edit.html",
            types=types,
            wiki_pages=wiki_pages,
            ScienceType=ScienceType,
        )

    try:
        substance_type = ScienceType(substance_type)
    except ValueError:
        flash("Invalid substance type", "error")
        types = [t for t in ScienceType]
        wiki_pages = [
            {"title": page.title, "slug": page.slug}
            for page in WikiPage.query.order_by(WikiPage.title).all()
        ]
        return render_template(
            "rules/exotic_substances/edit.html",
            types=types,
            wiki_pages=wiki_pages,
            ScienceType=ScienceType,
        )

    substance = ExoticSubstance(name=name, type=substance_type, wiki_slug=wiki_slug)

    db.session.add(substance)
    db.session.commit()

    flash("Exotic substance created successfully", "success")
    return redirect(url_for("exotic_substances.list"))


@exotic_substances_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
@email_verified_required
def edit(id):
    if not current_user.has_role("rules_team"):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    substance = ExoticSubstance.query.get_or_404(id)
    types = [t for t in ScienceType]
    wiki_pages = [
        {"title": page.title, "slug": page.slug}
        for page in WikiPage.query.order_by(WikiPage.title).all()
    ]
    return render_template(
        "rules/exotic_substances/edit.html",
        substance=substance,
        types=types,
        wiki_pages=wiki_pages,
        ScienceType=ScienceType,
    )


@exotic_substances_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
@email_verified_required
def edit_post(id):
    if not current_user.has_role("rules_team"):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    substance = ExoticSubstance.query.get_or_404(id)

    name = request.form.get("name")
    substance_type = request.form.get("type")
    wiki_slug = request.form.get("wiki_slug")

    if not all([name, substance_type, wiki_slug]):
        flash("All fields are required", "error")
        types = [t for t in ScienceType]
        wiki_pages = [
            {"title": page.title, "slug": page.slug}
            for page in WikiPage.query.order_by(WikiPage.title).all()
        ]
        return render_template(
            "rules/exotic_substances/edit.html",
            substance=substance,
            types=types,
            wiki_pages=wiki_pages,
            ScienceType=ScienceType,
        )

    try:
        substance_type = ScienceType(substance_type)
    except ValueError:
        flash("Invalid substance type", "error")
        types = [t for t in ScienceType]
        wiki_pages = [
            {"title": page.title, "slug": page.slug}
            for page in WikiPage.query.order_by(WikiPage.title).all()
        ]
        return render_template(
            "rules/exotic_substances/edit.html",
            substance=substance,
            types=types,
            wiki_pages=wiki_pages,
            ScienceType=ScienceType,
        )

    substance.name = name
    substance.type = substance_type
    substance.wiki_slug = wiki_slug

    db.session.commit()

    flash("Exotic substance updated successfully", "success")
    return redirect(url_for("exotic_substances.list"))
