from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.cybernetic import Cybernetic
from models.enums import Role, ScienceType
from models.extensions import db
from models.wiki import WikiPage, get_or_create_wiki_page

cybernetics_bp = Blueprint("cybernetics", __name__)


@cybernetics_bp.route("/")
@login_required
def list():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    return render_template("rules/cybernetics/list.html", cybernetics=cybernetics)


@cybernetics_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name")
        neural_shock_value = request.form.get("neural_shock_value", type=int)
        wiki_slug = request.form.get("wiki_slug")
        adds_engineering_mods = request.form.get("adds_engineering_mods", type=int, default=0)
        adds_engineering_downtime = request.form.get(
            "adds_engineering_downtime", type=int, default=0
        )
        adds_science_downtime = request.form.get("adds_science_downtime", type=int, default=0)
        science_type = request.form.get("science_type") if adds_science_downtime > 0 else None

        if not name or neural_shock_value is None or not wiki_slug:
            flash("All fields are required", "error")
            return render_template(
                "rules/cybernetics/edit.html",
                initial_title="",
                science_types=ScienceType.values(),
            )

        get_or_create_wiki_page(wiki_slug, f"{name} - Cybernetic", created_by=current_user.id)
        cyber = Cybernetic(
            name=name,
            neural_shock_value=neural_shock_value,
            wiki_slug=wiki_slug,
            adds_engineering_mods=adds_engineering_mods,
            adds_engineering_downtime=adds_engineering_downtime,
            adds_science_downtime=adds_science_downtime,
            science_type=science_type,
        )
        db.session.add(cyber)
        db.session.commit()
        flash("Cybernetic created", "success")
        return redirect(url_for("cybernetics.list"))
    return render_template(
        "rules/cybernetics/edit.html",
        initial_title="",
        science_types=ScienceType.values(),
    )


@cybernetics_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    cyber = Cybernetic.query.get_or_404(id)
    initial_title = ""
    if cyber.wiki_slug:
        wiki_page_obj = WikiPage.query.filter_by(slug=cyber.wiki_slug).first()
        if wiki_page_obj:
            initial_title = wiki_page_obj.title
    if request.method == "POST":
        name = request.form.get("name")
        neural_shock_value = request.form.get("neural_shock_value", type=int)
        wiki_slug = request.form.get("wiki_slug")
        adds_engineering_mods = request.form.get("adds_engineering_mods", type=int, default=0)
        adds_engineering_downtime = request.form.get(
            "adds_engineering_downtime", type=int, default=0
        )
        adds_science_downtime = request.form.get("adds_science_downtime", type=int, default=0)
        science_type = request.form.get("science_type")

        if not name or neural_shock_value is None or not wiki_slug:
            flash("All fields are required", "error")
            return render_template(
                "rules/cybernetics/edit.html",
                cyber=cyber,
                initial_title=initial_title,
                science_types=ScienceType.values(),
            )

        get_or_create_wiki_page(wiki_slug, f"{name} - Cybernetic", created_by=current_user.id)
        cyber.name = name
        cyber.neural_shock_value = neural_shock_value
        cyber.wiki_slug = wiki_slug
        cyber.adds_engineering_mods = adds_engineering_mods
        cyber.adds_engineering_downtime = adds_engineering_downtime
        cyber.adds_science_downtime = adds_science_downtime
        cyber.science_type = ScienceType(science_type) if science_type else None
        db.session.commit()
        flash("Cybernetic updated", "success")
        return redirect(url_for("cybernetics.list"))
    return render_template(
        "rules/cybernetics/edit.html",
        cyber=cyber,
        initial_title=initial_title,
        science_types=ScienceType.values(),
    )


@cybernetics_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))
    cyber = Cybernetic.query.get_or_404(id)
    db.session.delete(cyber)
    db.session.commit()
    flash("Cybernetic deleted", "success")
    return redirect(url_for("cybernetics.list"))
