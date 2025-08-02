from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.medicaments import Medicament
from models.extensions import db
from models.wiki import WikiPage, get_or_create_wiki_page
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required

medicaments_bp = Blueprint("medicaments", __name__)


@medicaments_bp.route("/")
def list():
    # Get all medicaments and order by name
    medicaments = Medicament.query.order_by(Medicament.name).all()
    can_edit = current_user.is_authenticated and current_user.has_permission("rules.medicaments")
    return render_template(
        "rules/medicaments/list.html", medicaments=medicaments, can_edit=can_edit
    )


@medicaments_bp.route("/new", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.medicaments"])
def create():
    return render_template("rules/medicaments/edit.html", initial_title="")


@medicaments_bp.route("/new", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.medicaments"])
def create_post():
    name = request.form.get("name")
    wiki_slug = request.form.get("wiki_slug")
    if not all([name, wiki_slug]):
        flash("Name and wiki page are required", "error")
        return render_template("rules/medicaments/edit.html", initial_title="")
    get_or_create_wiki_page(wiki_slug, f"{name} - Medicament", created_by=current_user.id)
    medicament = Medicament(name=name, wiki_slug=wiki_slug)
    db.session.add(medicament)
    db.session.commit()
    flash("Medicament created successfully", "success")
    return redirect(url_for("medicaments.list"))


@medicaments_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.medicaments"])
def edit(id):
    medicament = Medicament.query.get_or_404(id)
    initial_title = ""
    if medicament.wiki_slug:
        wiki_page_obj = WikiPage.query.filter_by(slug=medicament.wiki_slug).first()
        if wiki_page_obj:
            initial_title = wiki_page_obj.title
    return render_template(
        "rules/medicaments/edit.html",
        medicament=medicament,
        initial_title=initial_title,
    )


@medicaments_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.medicaments"])
def edit_post(id):
    medicament = Medicament.query.get_or_404(id)
    name = request.form.get("name")
    wiki_slug = request.form.get("wiki_slug")
    if not all([name, wiki_slug]):
        flash("Name and wiki page are required", "error")
        initial_title = ""
        if medicament.wiki_slug:
            wiki_page_obj = WikiPage.query.filter_by(slug=medicament.wiki_slug).first()
            if wiki_page_obj:
                initial_title = wiki_page_obj.title
        return render_template(
            "rules/medicaments/edit.html",
            medicament=medicament,
            initial_title=initial_title,
        )
    get_or_create_wiki_page(wiki_slug, f"{name} - Medicament", created_by=current_user.id)
    medicament.name = name
    medicament.wiki_slug = wiki_slug
    db.session.commit()
    flash("Medicament updated successfully", "success")
    return redirect(url_for("medicaments.list"))
