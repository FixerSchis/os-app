from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.cybernetic import (
    Cybernetic,
    canonical_label,
    distinct_labels,
    slot_change_conflict_message,
)
from models.enums import ScienceType
from models.extensions import db
from models.wiki import WikiPage, get_or_create_wiki_page
from utils.decorators import email_verified_required
from utils.permission_decorators import permission_required

cybernetics_bp = Blueprint("cybernetics", __name__)


def _form_context(cyber=None, initial_title="", posted_type=None, posted_slot=None):
    return {
        "cyber": cyber,
        "initial_title": initial_title,
        "science_types": ScienceType.values(),
        "implant_types": distinct_labels(Cybernetic.implant_type),
        "implant_slots": distinct_labels(Cybernetic.slot),
        "posted_type": posted_type,
        "posted_slot": posted_slot,
    }


def _wiki_title(cyber):
    initial_title = ""
    if cyber and cyber.wiki_slug:
        wiki_page_obj = WikiPage.query.filter_by(slug=cyber.wiki_slug).first()
        if wiki_page_obj:
            initial_title = wiki_page_obj.title
    return initial_title


def _read_implant_fields():
    implant_type = canonical_label(
        request.form.get("implant_type"), distinct_labels(Cybernetic.implant_type)
    )
    slot = canonical_label(request.form.get("slot"), distinct_labels(Cybernetic.slot))
    return implant_type, slot


@cybernetics_bp.route("/")
@login_required
@email_verified_required
@permission_required(permissions=["rules.cybernetics"])
def list():
    cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    return render_template("rules/cybernetics/list.html", cybernetics=cybernetics)


@cybernetics_bp.route("/new", methods=["GET", "POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.cybernetics"])
def create():
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
        implant_type, slot = _read_implant_fields()

        if not name or neural_shock_value is None or not wiki_slug:
            flash("All fields are required", "error")
            return render_template(
                "rules/cybernetics/edit.html",
                **_form_context(posted_type=implant_type, posted_slot=slot),
            )
        if not implant_type or not slot:
            flash("Type and slot are required.", "error")
            return render_template(
                "rules/cybernetics/edit.html",
                **_form_context(posted_type=implant_type, posted_slot=slot),
            )

        get_or_create_wiki_page(wiki_slug, f"{name} - Implant", created_by=current_user.id)
        cyber = Cybernetic(
            name=name,
            neural_shock_value=neural_shock_value,
            wiki_slug=wiki_slug,
            adds_engineering_mods=adds_engineering_mods,
            adds_engineering_downtime=adds_engineering_downtime,
            adds_science_downtime=adds_science_downtime,
            science_type=science_type,
            implant_type=implant_type,
            slot=slot,
        )
        db.session.add(cyber)
        db.session.commit()
        flash("Implant created", "success")
        return redirect(url_for("cybernetics.list"))
    return render_template("rules/cybernetics/edit.html", **_form_context())


@cybernetics_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.cybernetics"])
def edit(id):
    cyber = Cybernetic.query.get_or_404(id)
    initial_title = _wiki_title(cyber)
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
        implant_type, slot = _read_implant_fields()

        if not name or neural_shock_value is None or not wiki_slug:
            flash("All fields are required", "error")
            return render_template(
                "rules/cybernetics/edit.html",
                **_form_context(
                    cyber=cyber,
                    initial_title=initial_title,
                    posted_type=implant_type,
                    posted_slot=slot,
                ),
            )
        if not implant_type or not slot:
            flash("Type and slot are required.", "error")
            return render_template(
                "rules/cybernetics/edit.html",
                **_form_context(
                    cyber=cyber,
                    initial_title=initial_title,
                    posted_type=implant_type,
                    posted_slot=slot,
                ),
            )

        conflict = slot_change_conflict_message(cyber, slot)
        if conflict:
            flash(conflict, "error")
            return render_template(
                "rules/cybernetics/edit.html",
                **_form_context(
                    cyber=cyber,
                    initial_title=initial_title,
                    posted_type=implant_type,
                    posted_slot=slot,
                ),
            )

        get_or_create_wiki_page(wiki_slug, f"{name} - Implant", created_by=current_user.id)
        cyber.name = name
        cyber.neural_shock_value = neural_shock_value
        cyber.wiki_slug = wiki_slug
        cyber.adds_engineering_mods = adds_engineering_mods
        cyber.adds_engineering_downtime = adds_engineering_downtime
        cyber.adds_science_downtime = adds_science_downtime
        cyber.science_type = ScienceType(science_type) if science_type else None
        cyber.implant_type = implant_type
        cyber.slot = slot
        db.session.commit()
        flash("Implant updated", "success")
        return redirect(url_for("cybernetics.list"))
    return render_template(
        "rules/cybernetics/edit.html",
        **_form_context(cyber=cyber, initial_title=initial_title),
    )


@cybernetics_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@email_verified_required
@permission_required(permissions=["rules.cybernetics"])
def delete(id):
    cyber = Cybernetic.query.get_or_404(id)
    db.session.delete(cyber)
    db.session.commit()
    flash("Implant deleted", "success")
    return redirect(url_for("cybernetics.list"))
