import base64
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.conditions import Condition
from models.database.exotic_substances import ExoticSubstance
from models.database.item import Item
from models.database.medicaments import Medicament
from models.enums import PrintTemplateType
from models.extensions import db
from models.tools.character import Character
from models.tools.event_ticket import EventTicket
from models.tools.print_template import PrintTemplate
from models.tools.samples.character import get_sample_character
from models.tools.samples.condition import get_sample_condition
from models.tools.samples.exotic import get_sample_exotic_substance
from models.tools.samples.item import get_sample_item
from models.tools.samples.medicament import get_sample_medicament
from utils import generate_qr_code, generate_web_qr_code
from utils.decorators import admin_required
from utils.print_layout import PrintLayout

templates_bp = Blueprint("templates", __name__)


@templates_bp.route("/list")
@login_required
@admin_required
def template_list():
    """List all available templates"""
    templates = PrintTemplate.query.all()
    return render_template(
        "templates/list.html", templates=templates, PrintTemplateType=PrintTemplateType
    )


@templates_bp.route("/new", methods=["GET"])
@login_required
@admin_required
def template_new():
    """Create a new template"""
    return render_template(
        "templates/edit.html", template=None, PrintTemplateType=PrintTemplateType
    )


@templates_bp.route("/new", methods=["POST"])
@login_required
@admin_required
def template_new_post():
    """Handle new template creation"""
    # TODO: Implement template creation logic when model is created
    flash("Template creation not yet implemented.", "info")
    return redirect(url_for("templates.template_list"))


@templates_bp.route("/<int:template_id>/edit", methods=["GET"])
@login_required
@admin_required
def template_edit(template_id):
    """Edit an existing template"""
    template = PrintTemplate.query.get(template_id)
    if not template:
        flash("Template not found.", "error")
        return redirect(url_for("templates.template_list"))

    # Generate completions based on template type
    completions = generate_template_completions(template.type)

    return render_template(
        "templates/edit.html",
        template=template,
        PrintTemplateType=PrintTemplateType,
        completions=completions,
    )


@templates_bp.route("/<int:template_id>/edit", methods=["POST"])
@login_required
@admin_required
def template_edit_post(template_id):
    """Handle template editing"""
    template = PrintTemplate.query.get(template_id)
    if not template:
        flash("Template not found.", "error")
        return redirect(url_for("templates.template_list"))

    template.front_html = request.form.get("front_html", "")
    template.back_html = request.form.get("back_html", "")
    template.css_styles = request.form.get("css_styles", "")
    template.updated_at = datetime.now()
    db.session.commit()
    flash("Template updated successfully.", "success")
    return redirect(url_for("templates.template_list"))


@templates_bp.route("/api/<int:template_id>/render", methods=["POST"])
@login_required
@admin_required
def render_template_preview(template_id):
    """API endpoint to render a template preview with sample data"""
    template = PrintTemplate.query.get(template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404

    # Get the template content from the request
    data = request.get_json()
    template.front_html = data.get("front_html", template.front_html)
    template.back_html = data.get("back_html", template.back_html)
    template.css_styles = data.get("css_styles", template.css_styles)

    # Generate sample data based on template type
    if template.type == PrintTemplateType.CHARACTER_SHEET:
        sample_data = {"character": get_sample_character()}
    elif template.type == PrintTemplateType.CHARACTER_ID:
        sample_data = {"character": get_sample_character()}
    elif template.type == PrintTemplateType.ITEM_CARD:
        sample_data = {"item": get_sample_item()}
    elif template.type == PrintTemplateType.MEDICAMENT_CARD:
        sample_data = {"medicament": get_sample_medicament()}
    elif template.type == PrintTemplateType.CONDITION_CARD:
        sample_data = {"condition": get_sample_condition()}
    elif template.type == PrintTemplateType.EXOTIC_SUBSTANCE_LABEL:
        sample_data = {"substance": get_sample_exotic_substance()}
    else:
        sample_data = {}

    # Add QR code utilities to the template context
    template_context = {
        **sample_data,
        "generate_qr_code": generate_qr_code,
        "generate_web_qr_code": generate_web_qr_code,
    }

    try:
        front_rendered = template.get_front_page_render(template_context)
        back_rendered = template.get_back_page_render(template_context)
        css = template.get_css_render()
        css_b64 = base64.b64encode(css.encode("utf-8")).decode("ascii")

        return jsonify(
            {
                "front_html": front_rendered,
                "back_html": back_rendered,
                "css_b64": css_b64,
                "success": True,
            }
        )

    except Exception as e:
        print(e)
        return (
            jsonify({"error": f"Template rendering error: {str(e)}", "success": False}),
            400,
        )


@templates_bp.route("/<type>/<int:id>/print")
@login_required
def print_item_sheet(type, id):
    """Generate PDF for a single item (character sheet, item card, etc.)"""
    if not current_user.has_role("admin"):
        flash("Access denied. Admin role required.", "error")
        return jsonify({"error": "Access denied"}), 403

    layout_manager = PrintLayout()
    try:
        if type == "characters":
            # Get character and generate PDF
            character = Character.query.get_or_404(id)
            if not (current_user.has_role("user_admin") or current_user.id == character.user_id):
                return jsonify({"error": "Access denied"}), 403
            pdf = layout_manager.generate_character_sheets_pdf([character])
        elif type == "items":
            # Get item and generate PDF
            item = Item.query.get_or_404(id)
            pdf = layout_manager.generate_item_cards_pdf([item])
        elif type == "conditions":
            # Get condition and generate PDF
            condition = Condition.query.get_or_404(id)
            pdf = layout_manager.generate_condition_sheet_pdf(condition)
        elif type == "medicaments":
            # Get medicament and generate PDF
            medicament = Medicament.query.get_or_404(id)
            pdf = layout_manager.generate_medicament_sheet_pdf(medicament)
        elif type == "exotics":
            # Get exotic substance and generate PDF
            exotic = ExoticSubstance.query.get_or_404(id)
            pdf = layout_manager.generate_exotic_substance_labels_pdf(exotic)
        else:
            return jsonify({"error": "Invalid type"}), 400

        return jsonify({"pdf": base64.b64encode(pdf.read()).decode("utf-8")})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@templates_bp.route("/events/<int:event_id>/print/<type>")
@login_required
def print_event_items(event_id, type):
    """Generate PDFs for all items of a given type in an event."""
    if not current_user.has_role("admin"):
        flash("Access denied. Admin role required.", "error")
        return jsonify({"error": "Access denied"}), 403

    layout_manager = PrintLayout()
    try:
        if type == "characters":
            # Get all characters in the event
            characters = (
                Character.query.join(EventTicket).filter(EventTicket.event_id == event_id).all()
            )
            if not characters:
                return jsonify({"error": "No characters found in this event."}), 404
            pdf = layout_manager.generate_character_sheets_pdf(characters)
        elif type == "items":
            # Get all items in the event
            items = Item.query.join(EventTicket).filter(EventTicket.event_id == event_id).all()
            if not items:
                return jsonify({"error": "No items found in this event."}), 404
            pdf = layout_manager.generate_item_cards_pdf(items)
        else:
            return jsonify({"error": "Invalid type"}), 400

        return jsonify({"pdf": base64.b64encode(pdf.read()).decode("utf-8")})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def generate_template_completions(template_type):
    """Generate Jinja completions based on template type"""
    completions = {}

    if template_type == PrintTemplateType.CHARACTER_SHEET:
        # Import character model and get its fields
        from models.database.faction import Faction
        from models.database.species import Species
        from models.tools.character import Character

        character_fields = {}
        for column in Character.__table__.columns:
            if column.name not in ["id", "created_by_user_id"]:
                character_fields[column.name] = f"{column.type} - {column.name}"

        # Add relationship fields
        character_fields["species"] = "object - Character species"
        character_fields["faction"] = "object - Character faction"
        character_fields["skills"] = "list - Character skills"
        character_fields["tags"] = "list - Character tags"

        # Add nested fields
        species_fields = {}
        for column in Species.__table__.columns:
            if column.name not in ["id"]:
                species_fields[f"species.{column.name}"] = f"{column.type} - {column.name}"

        faction_fields = {}
        for column in Faction.__table__.columns:
            if column.name not in ["id"]:
                faction_fields[f"faction.{column.name}"] = f"{column.type} - {column.name}"

        completions = {
            "character": {**character_fields, **species_fields, **faction_fields},
            "jinja": get_jinja_completions(),
            "generate_qr_code": "function - Generate QR code for any data",
            "generate_web_qr_code": "function - Generate QR code for web route",
        }

    elif template_type == PrintTemplateType.ITEM_CARD:
        # Import item model and get its fields
        from models.database.item import Item

        item_fields = {}
        for column in Item.__table__.columns:
            if column.name not in ["id", "created_by_user_id"]:
                item_fields[column.name] = str(column.type)

        completions["item"] = item_fields
        # Also include blueprint and type fields
        from models.database.item_blueprint import ItemBlueprint
        from models.database.item_type import ItemType

        blueprint_fields = {}
        for column in ItemBlueprint.__table__.columns:
            if column.name not in ["id"]:
                blueprint_fields[f"blueprint.{column.name}"] = f"{column.type} - {column.name}"

        item_type_fields = {}
        for column in ItemType.__table__.columns:
            if column.name not in ["id"]:
                item_type_fields[
                    f"blueprint.item_type.{column.name}"
                ] = f"{column.type} - {column.name}"

        completions = {
            "item": {**item_fields, **blueprint_fields, **item_type_fields},
            "jinja": get_jinja_completions(),
            "generate_qr_code": "function - Generate QR code for any data",
            "generate_web_qr_code": "function - Generate QR code for web route",
        }

    elif template_type == PrintTemplateType.MEDICAMENT_CARD:
        # Import medicament model and get its fields
        from models.database.medicaments import Medicament

        medicament_fields = {}
        for column in Medicament.__table__.columns:
            if column.name not in ["id"]:
                medicament_fields[column.name] = str(column.type)

        completions = {
            "medicament": medicament_fields,
            "jinja": get_jinja_completions(),
            "generate_qr_code": "function - Generate QR code for any data",
            "generate_web_qr_code": "function - Generate QR code for web route",
        }

    elif template_type == PrintTemplateType.CONDITION_CARD:
        # Import condition model and get its fields
        from models.database.conditions import Condition

        condition_fields = {}
        for column in Condition.__table__.columns:
            if column.name not in ["id"]:
                condition_fields[column.name] = f"{column.type} - {column.name}"

        completions = {
            "condition": condition_fields,
            "jinja": get_jinja_completions(),
            "generate_qr_code": "function - Generate QR code for any data",
            "generate_web_qr_code": "function - Generate QR code for web route",
        }

    elif template_type == PrintTemplateType.EXOTIC_SUBSTANCE_LABEL:
        # Import exotic substance model and get its fields
        from models.database.exotic_substances import ExoticSubstance

        exotic_fields = {}
        for column in ExoticSubstance.__table__.columns:
            if column.name not in ["id"]:
                exotic_fields[column.name] = f"{column.type} - {column.name}"

        completions = {
            "substance": exotic_fields,
            "jinja": get_jinja_completions(),
            "generate_qr_code": "function - Generate QR code for any data",
            "generate_web_qr_code": "function - Generate QR code for web route",
        }

    return completions


@templates_bp.route("/api/<int:template_id>/print_preview", methods=["POST"])
@login_required
@admin_required
def print_template_preview(template_id):
    """Generate a full page preview PDF of the template with sample data."""
    template = PrintTemplate.query.get(template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404

    # Get the template content and layout settings from the request
    data = request.get_json()

    # Store original values to restore later
    original_values = {
        "width_mm": template.width_mm,
        "height_mm": template.height_mm,
        "is_landscape": template.is_landscape,
        "items_per_row": template.items_per_row,
        "items_per_column": template.items_per_column,
        "margin_top_mm": template.margin_top_mm,
        "margin_bottom_mm": template.margin_bottom_mm,
        "margin_left_mm": template.margin_left_mm,
        "margin_right_mm": template.margin_right_mm,
        "gap_horizontal_mm": template.gap_horizontal_mm,
        "gap_vertical_mm": template.gap_vertical_mm,
        "front_html": template.front_html,
        "back_html": template.back_html,
        "css_styles": template.css_styles,
    }

    try:
        # Update template with preview values
        template.width_mm = data.get("width_mm", template.width_mm)
        template.height_mm = data.get("height_mm", template.height_mm)
        template.is_landscape = data.get("is_landscape", False)
        template.has_back_side = data.get("has_back_side", False)
        template.items_per_row = data.get("items_per_row", 1)
        template.items_per_column = data.get("items_per_column", 1)
        template.margin_top_mm = data.get("margin_top_mm", 10.0)
        template.margin_bottom_mm = data.get("margin_bottom_mm", 10.0)
        template.margin_left_mm = data.get("margin_left_mm", 10.0)
        template.margin_right_mm = data.get("margin_right_mm", 10.0)
        template.gap_horizontal_mm = data.get("gap_horizontal_mm", 2.0)
        template.gap_vertical_mm = data.get("gap_vertical_mm", 2.0)
        template.front_html = data.get("front_html", template.front_html)
        template.back_html = data.get("back_html", template.back_html)
        template.css_styles = data.get("css_styles", template.css_styles)

        # Create layout manager
        layout_manager = PrintLayout()

        # Generate PDF based on template type
        if template.type == PrintTemplateType.CHARACTER_SHEET:
            sample = get_sample_character()
            pdf = layout_manager.generate_character_sheets_pdf(
                [sample for _ in range(template.items_per_row * template.items_per_column)]
            )
        elif template.type == PrintTemplateType.CHARACTER_ID:
            sample = get_sample_character()
            pdf = layout_manager.generate_character_id_pdf(
                [sample for _ in range(template.items_per_row * template.items_per_column)]
            )
        elif template.type == PrintTemplateType.ITEM_CARD:
            sample = get_sample_item()
            pdf = layout_manager.generate_item_cards_pdf(
                [sample for _ in range(template.items_per_row * template.items_per_column)]
            )
        elif template.type == PrintTemplateType.MEDICAMENT_CARD:
            sample = get_sample_medicament()
            pdf = layout_manager.generate_medicament_sheet_pdf(
                [sample for _ in range(template.items_per_row * template.items_per_column)]
            )
        elif template.type == PrintTemplateType.CONDITION_CARD:
            sample = get_sample_condition()
            pdf = layout_manager.generate_condition_sheet_pdf(
                [sample for _ in range(template.items_per_row * template.items_per_column)]
            )
        elif template.type == PrintTemplateType.EXOTIC_SUBSTANCE_LABEL:
            sample = get_sample_exotic_substance()
            pdf = layout_manager.generate_exotic_substance_labels_pdf(
                [sample for _ in range(template.items_per_row * template.items_per_column)]
            )
        else:
            return jsonify({"error": "Invalid template type"}), 400

        # Return the PDF
        return jsonify(
            {
                "pdf": base64.b64encode(pdf.read()).decode("utf-8"),
                "double_sided": bool(template.back_html),
            }
        )

    except Exception as e:
        print(f"Error generating preview: {str(e)}")
        return jsonify({"error": str(e)}), 400

    finally:
        # Restore original values
        for key, value in original_values.items():
            setattr(template, key, value)


def get_jinja_completions():
    """Get standard Jinja template completions"""
    return {
        "if": "Conditional statement",
        "for": "Loop statement",
        "endif": "End conditional",
        "endfor": "End loop",
        "else": "Else clause",
        "elif": "Else if clause",
        "block": "Template block",
        "extends": "Template inheritance",
        "include": "Include template",
        "macro": "Define macro",
        "call": "Call macro",
        "filter": "Apply filter",
        "set": "Set variable",
        "with": "Context manager",
    }


@templates_bp.route("/<int:template_id>/layout", methods=["GET", "POST"])
@login_required
@admin_required
def template_layout(template_id):
    """Edit layout settings for a template"""
    template = PrintTemplate.query.get_or_404(template_id)

    if request.method == "POST":
        data = request.get_json()

        # Update template layout settings
        template.width_mm = data.get("width_mm", template.width_mm)
        template.height_mm = data.get("height_mm", template.height_mm)
        template.is_landscape = data.get("is_landscape", False)
        template.has_back_side = data.get("has_back_side", False)
        template.items_per_row = data.get("items_per_row", 1)
        template.items_per_column = data.get("items_per_column", 1)
        template.margin_top_mm = data.get("margin_top_mm", 10.0)
        template.margin_bottom_mm = data.get("margin_bottom_mm", 10.0)
        template.margin_left_mm = data.get("margin_left_mm", 10.0)
        template.margin_right_mm = data.get("margin_right_mm", 10.0)
        template.gap_horizontal_mm = data.get("gap_horizontal_mm", 2.0)
        template.gap_vertical_mm = data.get("gap_vertical_mm", 2.0)

        db.session.commit()
        return jsonify({"success": True})

    return render_template(
        "templates/layout.html", template=template, PrintTemplateType=PrintTemplateType
    )
