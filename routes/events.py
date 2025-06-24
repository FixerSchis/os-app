import json
import logging
import random
from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.exotic_substances import ExoticSubstance
from models.database.global_settings import GlobalSettings
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.medicaments import Medicament
from models.database.sample import Sample
from models.enums import CharacterStatus, EventType, Role, TicketType
from models.event import Event
from models.extensions import db
from models.tools.character import Character
from models.tools.event_ticket import EventTicket
from models.tools.group import Group
from models.tools.pack import Pack
from models.tools.user import User
from utils.decorators import admin_required, user_admin_required
from utils.email import (
    send_event_details_updated_notification,
    send_event_ticket_assigned_notification_to_user,
    send_new_event_notification_to_all,
)

events_bp = Blueprint("events", __name__)


@events_bp.route("/")
def event_list():
    show_previous = request.args.get("show_previous", "false").lower() == "true"

    if show_previous and current_user.has_role("user_admin"):
        events = (
            Event.query.filter(Event.end_date <= datetime.now())
            .order_by(Event.start_date.desc())
            .all()
        )
    else:
        events = (
            Event.query.filter(Event.end_date > datetime.now()).order_by(Event.start_date).all()
        )

    return render_template(
        "events/index.html",
        events=events,
        EventType=EventType,
        show_previous=show_previous,
    )


@events_bp.route("/new", methods=["GET"])
@login_required
@user_admin_required
def create_event():
    return render_template("events/edit.html", EventType=EventType)


@events_bp.route("/new", methods=["POST"])
@login_required
@user_admin_required
def create_event_post():
    event = Event(
        event_number=request.form["event_number"],
        name=request.form["name"],
        event_type=request.form["event_type"],
        description=request.form["description"],
        early_booking_deadline=datetime.strptime(
            request.form["early_booking_deadline"], "%Y-%m-%d"
        ),
        booking_deadline=datetime.strptime(request.form["booking_deadline"], "%Y-%m-%d"),
        start_date=datetime.strptime(request.form["start_date"], "%Y-%m-%d"),
        end_date=datetime.strptime(request.form["end_date"], "%Y-%m-%d"),
        location=request.form["location"],
        google_maps_link=(
            request.form["google_maps_link"]
            if request.form["event_type"] in ["mainline", "sanctioned"]
            else None
        ),
        meal_ticket_available=bool(request.form.get("meal_ticket_available")),
        meal_ticket_price=(
            float(request.form["meal_ticket_price"])
            if request.form.get("meal_ticket_available")
            else None
        ),
        bunks_available=bool(request.form.get("bunks_available")),
        standard_ticket_price=float(request.form["standard_ticket_price"]),
        early_booking_ticket_price=float(request.form["early_booking_ticket_price"]),
        child_ticket_price_12_15=float(request.form["child_ticket_price_12_15"]),
        child_ticket_price_7_11=float(request.form["child_ticket_price_7_11"]),
        child_ticket_price_under_7=float(request.form["child_ticket_price_under_7"]),
    )
    db.session.add(event)
    db.session.commit()
    send_new_event_notification_to_all(event)
    flash("Event created successfully!", "success")
    return redirect(url_for("events.event_list"))


@events_bp.route("/<int:event_id>/edit", methods=["GET"])
@login_required
@user_admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("events/edit.html", event=event, EventType=EventType)


@events_bp.route("/<int:event_id>/edit", methods=["POST"])
@login_required
@user_admin_required
def edit_event_post(event_id):
    event = Event.query.get_or_404(event_id)
    event.event_number = request.form["event_number"]
    event.name = request.form["name"]
    event.event_type = request.form["event_type"]
    event.description = request.form["description"]
    event.early_booking_deadline = datetime.strptime(
        request.form["early_booking_deadline"], "%Y-%m-%d"
    )
    event.booking_deadline = datetime.strptime(request.form["booking_deadline"], "%Y-%m-%d")
    event.start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d")
    event.end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d")
    event.location = request.form["location"]
    event.google_maps_link = (
        request.form["google_maps_link"]
        if request.form["event_type"] in ["mainline", "sanctioned"]
        else None
    )
    event.meal_ticket_available = bool(request.form.get("meal_ticket_available"))
    event.meal_ticket_price = (
        float(request.form["meal_ticket_price"])
        if request.form.get("meal_ticket_available")
        else None
    )
    event.bunks_available = bool(request.form.get("bunks_available"))
    event.standard_ticket_price = float(request.form["standard_ticket_price"])
    event.early_booking_ticket_price = float(request.form["early_booking_ticket_price"])
    event.child_ticket_price_12_15 = float(request.form["child_ticket_price_12_15"])
    event.child_ticket_price_7_11 = float(request.form["child_ticket_price_7_11"])
    event.child_ticket_price_under_7 = float(request.form["child_ticket_price_under_7"])
    db.session.commit()
    for ticket in event.tickets:
        send_event_details_updated_notification(ticket.character.user, event, ticket.character)
    flash("Event updated successfully!", "success")
    return redirect(url_for("events.event_list"))


@events_bp.route("/<int:event_id>/purchase", methods=["GET"])
@login_required
def purchase_ticket(event_id):
    event = Event.query.get_or_404(event_id)

    # Check if booking is still available
    if not event.is_booking_available():
        if event.booking_deadline:
            deadline_msg = f"The booking deadline was {event.booking_deadline.strftime('%d %b %Y')}"
        else:
            deadline_msg = "The event has already started"
        flash(
            f"Booking for this event has closed. {deadline_msg}.",
            "error",
        )
        return redirect(url_for("events.event_list"))

    user_characters = Character.query.filter_by(
        user_id=current_user.id, status=CharacterStatus.ACTIVE.value
    ).all()

    if not user_characters:
        flash("You need an active character to purchase tickets.", "error")
        return redirect(url_for("events.event_list"))

    return render_template(
        "events/purchase.html",
        event=event,
        TicketType=TicketType,
        EventType=EventType,
        user_characters=user_characters,
    )


@events_bp.route("/<int:event_id>/purchase", methods=["POST"])
@login_required
def purchase_ticket_post(event_id):
    event = Event.query.get_or_404(event_id)

    # Check if booking is still available
    if not event.is_booking_available():
        if event.booking_deadline:
            deadline_msg = f"The booking deadline was {event.booking_deadline.strftime('%d %b %Y')}"
        else:
            deadline_msg = "The event has already started"
        flash(
            f"Booking for this event has closed. {deadline_msg}.",
            "error",
        )
        return redirect(url_for("events.event_list"))

    cart_data = request.form.get("cart")
    if not cart_data:
        flash("No tickets in cart.", "error")
        return redirect(url_for("events.purchase_ticket", event_id=event_id))

    try:
        cart = json.loads(cart_data)
    except Exception:
        flash("Invalid cart data.", "error")
        return redirect(url_for("events.purchase_ticket", event_id=event_id))

    tickets_created = 0
    self_ticket_added = False
    for item in cart:
        ticket_type = item.get("ticketType")
        meal_ticket = bool(item.get("mealTicket"))
        requires_bunk = bool(item.get("requiresBunk"))
        ticket_for = item.get("ticketFor")  # 'self' or 'other'
        character_id = None
        user_id = None
        child_name = None
        # --- Adult Ticket ---
        if ticket_type == "adult":
            character_to_check = None
            if ticket_for == "self":
                self_char_id = item.get("selfCharacterId")
                if self_char_id:
                    character_to_check = Character.query.get(self_char_id)
                    if not character_to_check or character_to_check.user_id != current_user.id:
                        continue
                else:
                    character_to_check = current_user.get_active_character()
            else:  # ticket_for == 'other'
                char_id_str = item.get("characterId")
                if not char_id_str or "." not in char_id_str or not char_id_str.strip():
                    continue
                u_id, c_id = char_id_str.split(".")
                try:
                    character_to_check = Character.query.filter_by(
                        user_id=int(u_id), character_id=int(c_id)
                    ).first()
                except ValueError:
                    continue

            if not character_to_check:
                continue

            target_user = User.query.get(character_to_check.user_id)
            if not target_user:
                continue

            # Rule: User can't have a Crew ticket for this event
            existing_crew = EventTicket.query.filter_by(
                event_id=event_id, user_id=target_user.id, ticket_type="crew"
            ).first()
            if existing_crew:
                continue

            # Rule: User can't have more than one Adult ticket for this event
            # (across all their characters)
            user_character_ids = [c.id for c in target_user.characters]
            if user_character_ids:
                existing_adult = EventTicket.query.filter(
                    EventTicket.event_id == event_id,
                    EventTicket.character_id.in_(user_character_ids),
                    EventTicket.ticket_type == "adult",
                ).first()
                if existing_adult:
                    continue

            character_id = character_to_check.id
            user_id = target_user.id

        # --- Crew Ticket ---
        elif ticket_type == "crew":
            # Only users with allowed roles can purchase
            if not current_user.has_any_role(
                [
                    Role.USER_ADMIN.value,
                    Role.RULES_TEAM.value,
                    Role.PLOT_TEAM.value,
                    Role.DOWNTIME_TEAM.value,
                    Role.NPC.value,
                ]
            ):
                continue
            if ticket_for == "self":
                if self_ticket_added:
                    continue
                self_ticket_added = True
                user_id = current_user.id
                character_id = None  # Crew tickets never require a character
                # Check for any adult ticket for this user (any character) for this event
                user_characters = Character.query.filter_by(user_id=current_user.id).all()
                character_ids = [char.id for char in user_characters]
                if character_ids:
                    existing_adult = EventTicket.query.filter(
                        EventTicket.event_id == event_id,
                        EventTicket.character_id.in_(character_ids),
                        EventTicket.ticket_type == "adult",
                    ).first()
                    if existing_adult:
                        continue
            else:
                # Assigning crew to another user is not allowed in purchase flow
                continue
            # Only one crew ticket per user/event
            existing = EventTicket.query.filter_by(
                event_id=event_id, user_id=user_id, ticket_type="crew"
            ).first()
            if existing:
                continue
        # --- Child Tickets ---
        elif ticket_type in ["child_12_15", "child_7_11", "child_under_7"]:
            user_id = current_user.id
            character_id = None
            child_name = item.get("childName", "").strip()
            if not child_name:
                continue
            # Allow multiple child tickets per user/event/child_name
        else:
            continue  # Unknown ticket type

        price_paid = float(item.get("price", 0))
        ticket = EventTicket(
            event_id=event_id,
            character_id=character_id,
            user_id=user_id,
            ticket_type=ticket_type,
            meal_ticket=meal_ticket,
            requires_bunk=requires_bunk,
            price_paid=price_paid,
            assigned_by_id=current_user.id,
            assigned_at=datetime.now(timezone.utc),
            child_name=child_name,
        )
        db.session.add(ticket)

        # Reset group pack if character has a group
        if character_id:
            character = db.session.get(Character, character_id)
            if character and character.group:
                # Reset the group pack - unmark as generated and clear contents except items
                if not character.group.pack:
                    character.group.pack = Pack()
                character.group.pack.is_generated = False

        tickets_created += 1

    db.session.commit()
    if tickets_created:
        flash(f"{tickets_created} ticket(s) purchased successfully!", "success")
    else:
        flash("No tickets were purchased.", "error")
    return redirect(url_for("events.event_list"))


@events_bp.route("/<int:event_id>/assign", methods=["GET"])
@login_required
@user_admin_required
def assign_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    users = User.query.order_by(User.first_name, User.surname).all()
    return render_template("events/assign.html", event=event, TicketType=TicketType, users=users)


@events_bp.route("/<int:event_id>/assign", methods=["POST"])
@login_required
@user_admin_required
def assign_ticket_post(event_id):
    ticket_type = request.form["ticket_type"]
    price_paid = 0 if ticket_type == "crew" else float(request.form["price_paid"])
    user_id = None
    character_id = None
    child_name = None

    # --- Adult ---
    if ticket_type == "adult":
        user_id_str, character_id_str = request.form["character"].split(".")
        character = Character.query.filter_by(
            user_id=user_id_str, character_id=character_id_str
        ).first_or_404()
        user_id = character.user_id
        character_id = character.id
        # Only one adult ticket per character/event
        existing = EventTicket.query.filter_by(
            event_id=event_id, character_id=character_id, ticket_type="adult"
        ).first()
        if existing:
            flash("This character already has an adult ticket for this event.", "error")
            return redirect(url_for("events.assign_ticket", event_id=event_id))
    # --- Crew ---
    elif ticket_type == "crew":
        user_id = int(request.form["user_id"])  # New field for crew assignment
        character_id = None
        # Only one crew ticket per user/event
        existing = EventTicket.query.filter_by(
            event_id=event_id, user_id=user_id, ticket_type="crew"
        ).first()
        if existing:
            flash("This user already has a crew ticket for this event.", "error")
            return redirect(url_for("events.assign_ticket", event_id=event_id))
    # --- Child ---
    elif ticket_type in ["child_12_15", "child_7_11", "child_under_7"]:
        user_id = int(request.form["user_id"])  # New field for child assignment
        character_id = None
        child_name = request.form.get("child_name", "").strip()
        if not child_name:
            flash("Please enter the child's name.", "error")
            return redirect(url_for("events.assign_ticket", event_id=event_id))
        # Allow multiple child tickets per user/event/child_name
    else:
        flash("Unknown ticket type.", "error")
        return redirect(url_for("events.assign_ticket", event_id=event_id))

    ticket = EventTicket(
        event_id=event_id,
        character_id=character_id,
        user_id=user_id,
        ticket_type=ticket_type,
        meal_ticket=bool(request.form.get("meal_ticket")),
        requires_bunk=bool(request.form.get("requires_bunk")),
        price_paid=price_paid,
        assigned_by_id=current_user.id,
        assigned_at=datetime.now(timezone.utc),
        child_name=child_name,
    )
    db.session.add(ticket)

    # Reset group pack if character has a group
    if character_id:
        character = db.session.get(Character, character_id)
        if character and character.group:
            # Reset the group pack - unmark as generated and clear contents except items
            if not character.group.pack:
                character.group.pack = Pack()
            character.group.pack.is_generated = False

    db.session.commit()
    flash("Ticket assigned successfully!", "success")
    return redirect(url_for("events.view_attendees", event_id=event_id))


@events_bp.route("/<int:event_id>/attendees", methods=["GET"])
@login_required
@user_admin_required
def view_attendees(event_id):
    event = Event.query.get_or_404(event_id)
    tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .outerjoin(EventTicket.character)  # Use left join for tickets without characters
        .join(EventTicket.user)  # Always join with user
        .add_entity(Character)
        .add_entity(User)
        .all()
    )
    return render_template(
        "events/attendees.html", event=event, tickets=tickets, TicketType=TicketType
    )


@events_bp.route("/<int:event_id>/packs", methods=["GET"])
@login_required
@admin_required
def view_packs(event_id):
    event = Event.query.get_or_404(event_id)

    # Get all characters with tickets for this event
    character_tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .filter(EventTicket.character_id.isnot(None))
        .all()
    )
    character_packs = []

    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character:
            pack = character.pack or Pack()
            character_packs.append(
                {
                    "character": character,
                    "ticket": ticket,
                    "pack": pack,
                    "user": character.user,
                    "faction": character.faction,
                }
            )

    # Sort character packs: incomplete first, then by user name
    character_packs.sort(
        key=lambda x: (
            x["pack"].is_completed,  # False (incomplete) comes before True (complete)
            x["user"].first_name + " " + x["user"].surname,
        )
    )

    # Get all groups with members who have tickets for this event
    group_packs = []
    groups_with_tickets = set()

    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character and character.group:
            groups_with_tickets.add(character.group.id)

    for group_id in groups_with_tickets:
        group = Group.query.get(group_id)
        if group:
            pack = group.pack or Pack()

            # Get characters from this group attending the event
            group_characters = []
            for ticket in character_tickets:
                character = Character.query.get(ticket.character_id)
                if character and character.group_id == group_id:
                    group_characters.append(
                        {
                            "user": character.user,
                            "character": character,
                            "species": character.species,
                        }
                    )

            group_packs.append({"group": group, "pack": pack, "characters": group_characters})

    # Sort group packs: incomplete first, then by group name
    group_packs.sort(
        key=lambda x: (
            x["pack"].is_completed,  # False (incomplete) comes before True (complete)
            x["group"].name,
        )
    )

    # Get global settings for character income
    settings = GlobalSettings.query.first()
    character_income_ec = settings.character_income_ec if settings else 0

    # Get all item blueprints, exotics, and medicaments for lookup
    # Convert to dictionaries for JSON serialization
    item_blueprints = {}
    for bp in ItemBlueprint.query.all():
        item_blueprints[bp.id] = {"name": bp.name, "full_code": bp.full_code}

    # Get all items for lookup (to get item full_code)
    items = {}
    for item in Item.query.all():
        items[item.id] = {
            "blueprint_name": item.blueprint.name if item.blueprint else "Unknown",
            "full_code": item.full_code,
        }

    exotic_substances = {}
    for ex in ExoticSubstance.query.all():
        exotic_substances[ex.id] = {"name": ex.name}

    medicaments = {}
    for med in Medicament.query.all():
        medicaments[med.id] = {"name": med.name}

    # Get all samples for lookup
    samples = {}
    for sample in Sample.query.all():
        samples[sample.id] = {"name": sample.name}

    return render_template(
        "events/packs.html",
        event=event,
        character_packs=character_packs,
        group_packs=group_packs,
        item_blueprints=item_blueprints,
        items=items,
        exotic_substances=exotic_substances,
        medicaments=medicaments,
        samples=samples,
        character_income_ec=character_income_ec,
    )


@events_bp.route("/<int:event_id>/packs/character/<int:character_id>/update", methods=["POST"])
@login_required
@admin_required
def update_character_pack(event_id, character_id):
    """Update character pack completion status."""
    character = Character.query.get_or_404(character_id)

    logging.debug(f"[PACK UPDATE] Raw request.data: {request.data}")
    data = request.get_json(force=True, silent=True) or {}
    logging.debug(f"[PACK UPDATE] Raw data: {data}")
    completion = data.get("completion", {})
    logging.debug(f"[PACK UPDATE] Before: {character.pack.completion}")
    pack = character.pack
    pack.completion = completion
    character.pack = pack  # This triggers the setter and updates character_pack
    logging.debug(f"[PACK UPDATE] After: {character.pack.completion}")
    db.session.commit()

    return jsonify({"success": True, "is_completed": character.pack.is_completed})


@events_bp.route("/<int:event_id>/packs/group/<int:group_id>/generate", methods=["POST"])
@login_required
@admin_required
def generate_group_pack(event_id, group_id):
    """Generate group pack contents based on group type settings."""
    group = Group.query.get_or_404(group_id)
    _ = Event.query.get_or_404(event_id)

    if not group.pack:
        group.pack = Pack()

    # Mark as generated
    group.pack.is_generated = True

    # Get global settings
    settings = GlobalSettings.query.first()
    if not settings:
        flash("Global settings not found", "error")
        return jsonify({"success": False, "error": "Global settings not found"})

    # Get characters from this group attending the event
    group_characters = (
        Character.query.filter_by(group_id=group_id)
        .join(EventTicket)
        .filter(EventTicket.event_id == event_id)
        .all()
    )

    if not group_characters:
        flash("No characters from this group are attending the event", "error")
        return jsonify({"success": False, "error": "No characters attending"})

    # Calculate EC pool based on global settings and species abilities
    ec_pool = 0
    for character in group_characters:
        # Base character income
        character_ec = settings.character_income_ec

        # Add species additional group income
        if character.species:
            for ability in character.species.abilities:
                if ability.type == "group_income" and ability.additional_group_income:
                    character_ec += ability.additional_group_income

        ec_pool += character_ec

    # Apply income distribution from group type
    if group.group_type and group.group_type.income_distribution_dict:
        distribution = group.group_type.income_distribution_dict

        # Calculate budget for each category
        items_budget = int(ec_pool * (distribution.get("items", 0) / 100))
        exotics_budget = int(ec_pool * (distribution.get("exotics", 0) / 100))
        medicaments_budget = int(ec_pool * (distribution.get("medicaments", 0) / 100))
        chits_budget = int(ec_pool * (distribution.get("chits", 0) / 100))

        # Add items randomly until budget is exhausted
        if items_budget > 0 and group.group_type.income_items_list:
            available_blueprints = ItemBlueprint.query.filter(
                ItemBlueprint.id.in_(group.group_type.income_items_list),
                ItemBlueprint.purchaseable,
            ).all()

            # Count the cost of existing items in the pack
            for item in group.pack.items:
                item_blueprint = ItemBlueprint.query.get(item)
                if item_blueprint:
                    item_cost = int(
                        item_blueprint.base_cost * (1 - group.group_type.income_items_discount)
                    )
                    items_budget -= item_cost

            if available_blueprints and items_budget > 0:
                # Shuffle blueprints for randomness
                random.shuffle(available_blueprints)

                for blueprint in available_blueprints:
                    # Calculate cost with group type discount
                    discounted_cost = int(
                        blueprint.base_cost * (1 - group.group_type.income_items_discount)
                    )

                    if discounted_cost <= items_budget:
                        # Add item to pack
                        group.pack.items.append(blueprint.id)
                        items_budget -= discounted_cost
                    else:
                        # Can't afford this item, stop adding items
                        break

        # Clear exotics and add them randomly
        group.pack.exotics = []
        if exotics_budget > 0 and group.group_type.income_substances:
            available_exotics = ExoticSubstance.query.all()

            if available_exotics:
                # Shuffle exotics for randomness
                random.shuffle(available_exotics)

                for exotic in available_exotics:
                    exotic_cost = group.group_type.income_substance_cost

                    if exotic_cost <= exotics_budget:
                        # Add exotic to pack
                        group.pack.exotics.append(exotic.id)
                        exotics_budget -= exotic_cost
                    else:
                        # Can't afford this exotic, stop adding exotics
                        break

        # Clear medicaments and add them randomly
        group.pack.medicaments = []
        if medicaments_budget > 0 and group.group_type.income_medicaments:
            available_medicaments = Medicament.query.all()

            if available_medicaments:
                # Shuffle medicaments for randomness
                random.shuffle(available_medicaments)

                for medicament in available_medicaments:
                    medicament_cost = group.group_type.income_medicament_cost

                    if medicament_cost <= medicaments_budget:
                        # Add medicament to pack
                        group.pack.medicaments.append(medicament.id)
                        medicaments_budget -= medicament_cost
                    else:
                        # Can't afford this medicament, stop adding medicaments
                        break

        # Add remaining EC to the pack
        remaining_ec = items_budget + exotics_budget + medicaments_budget + chits_budget
        group.pack.energy_chits = remaining_ec

    db.session.commit()

    return jsonify({"success": True, "pack": group.pack.to_dict()})


@events_bp.route("/<int:event_id>/packs/group/<int:group_id>/update", methods=["POST"])
@login_required
@admin_required
def update_group_pack(event_id, group_id):
    """Update group pack completion status."""
    group = Group.query.get_or_404(group_id)

    # Get completion data from request
    data = request.get_json()
    completion = data.get("completion", {})

    # Update pack completion
    if not group.pack:
        group.pack = Pack()

    group.pack.completion = completion
    db.session.commit()

    return jsonify({"success": True, "is_completed": group.pack.is_completed})


@events_bp.route("/<int:event_id>/packs/print/character-sheets")
@login_required
@admin_required
def print_character_sheets(event_id):
    """Print character sheets for incomplete character packs."""
    import base64

    from models.enums import PrintTemplateType
    from models.tools.print_template import PrintTemplate
    from utils.print_layout import PrintLayout

    event = Event.query.get_or_404(event_id)

    # Get all characters with tickets for this event
    character_tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .filter(EventTicket.character_id.isnot(None))
        .all()
    )
    characters_to_print = []

    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character:
            pack = character.pack or Pack()
            # Only include characters whose character sheet is not marked as complete
            if not pack.completion.get("character_sheet", False):
                characters_to_print.append(character)

    if not characters_to_print:
        flash("No character sheets to print - all are marked as complete.", "info")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Get the template for character sheets
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CHARACTER_SHEET).first()
    if not template:
        flash("No character sheet template found. Please create one first.", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Generate PDF
    layout_manager = PrintLayout()
    try:
        pdf = layout_manager.generate_character_sheets_pdf(characters_to_print, template)
        pdf.seek(0)

        # Return PDF for inline preview
        from flask import send_file

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"character_sheets_event_{event.event_number}.pdf",
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))


@events_bp.route("/<int:event_id>/packs/print/character-id-badges")
@login_required
@admin_required
def print_character_id_badges(event_id):
    """Print character ID badges for incomplete character packs."""
    from models.enums import PrintTemplateType
    from models.tools.print_template import PrintTemplate
    from utils.print_layout import PrintLayout

    event = Event.query.get_or_404(event_id)

    # Get all characters with tickets for this event
    character_tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .filter(EventTicket.character_id.isnot(None))
        .all()
    )
    characters_to_print = []

    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character:
            pack = character.pack or Pack()
            # Only include characters whose ID badge is not marked as complete
            if not pack.completion.get("character_id_badge", False):
                characters_to_print.append(character)

    if not characters_to_print:
        flash("No character ID badges to print - all are marked as complete.", "info")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Get the template for character ID badges
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CHARACTER_ID).first()
    if not template:
        flash("No character ID badge template found. Please create one first.", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Generate PDF
    layout_manager = PrintLayout()
    try:
        pdf = layout_manager.generate_character_id_pdf(characters_to_print, template)
        pdf.seek(0)

        # Return PDF for inline preview
        from flask import send_file

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"character_id_badges_event_{event.event_number}.pdf",
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))


@events_bp.route("/<int:event_id>/packs/print/items")
@login_required
@admin_required
def print_items(event_id):
    """Print items for incomplete character and group packs."""
    from models.database.item_blueprint import ItemBlueprint
    from models.enums import PrintTemplateType
    from models.tools.print_template import PrintTemplate
    from utils.print_layout import PrintLayout

    event = Event.query.get_or_404(event_id)

    # Get all characters with tickets for this event
    character_tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .filter(EventTicket.character_id.isnot(None))
        .all()
    )
    items_to_print = []

    # Character items
    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character:
            pack = character.pack or Pack()
            # Only include characters whose items are not marked as complete
            if not pack.completion.get("items", False) and pack.items:
                for item_id in pack.items:
                    # Get the item blueprint
                    item = Item.query.get(item_id)
                    if item:
                        items_to_print.append(item)

    # Group items
    groups_with_tickets = set()
    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character and character.group:
            groups_with_tickets.add(character.group.id)

    for group_id in groups_with_tickets:
        group = Group.query.get(group_id)
        if group:
            pack = group.pack or Pack()
            # Only include groups whose items are not marked as complete
            if not pack.completion.get("items", False) and pack.items:
                for item_id in pack.items:
                    # Get the item blueprint
                    item = Item.query.get(item_id)
                    if item:
                        items_to_print.append(item)

    if not items_to_print:
        flash("No items to print - all are marked as complete.", "info")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Get the template for item cards
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.ITEM_CARD).first()
    if not template:
        flash("No item card template found. Please create one first.", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Generate PDF
    layout_manager = PrintLayout()
    try:
        pdf = layout_manager.generate_item_cards_pdf(items_to_print, template)
        pdf.seek(0)

        # Return PDF for inline preview
        from flask import send_file

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"items_event_{event.event_number}.pdf",
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))


@events_bp.route("/<int:event_id>/packs/print/medicaments")
@login_required
@admin_required
def print_medicaments(event_id):
    """Print medicaments for incomplete character and group packs."""
    from models.database.medicaments import Medicament
    from models.enums import PrintTemplateType
    from models.tools.print_template import PrintTemplate
    from utils.print_layout import PrintLayout

    event = Event.query.get_or_404(event_id)

    # Get all characters with tickets for this event
    character_tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .filter(EventTicket.character_id.isnot(None))
        .all()
    )
    medicaments_to_print = []

    # Character medicaments
    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character:
            pack = character.pack or Pack()
            # Only include characters whose medicaments are not marked as complete
            if not pack.completion.get("medicaments", False) and pack.medicaments:
                for medicament_id in pack.medicaments:
                    medicament = Medicament.query.get(medicament_id)
                    if medicament:
                        medicaments_to_print.append(medicament)

    # Group medicaments
    groups_with_tickets = set()
    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character and character.group:
            groups_with_tickets.add(character.group.id)

    for group_id in groups_with_tickets:
        group = Group.query.get(group_id)
        if group:
            pack = group.pack or Pack()
            # Only include groups whose medicaments are not marked as complete
            if not pack.completion.get("medicaments", False) and pack.medicaments:
                for medicament_id in pack.medicaments:
                    medicament = Medicament.query.get(medicament_id)
                    if medicament:
                        medicaments_to_print.append(medicament)

    if not medicaments_to_print:
        flash("No medicaments to print - all are marked as complete.", "info")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Get the template for medicament cards
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.MEDICAMENT_CARD).first()
    if not template:
        flash("No medicament card template found. Please create one first.", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))

    # Generate PDF
    layout_manager = PrintLayout()
    try:
        pdf = layout_manager.generate_medicament_sheet_pdf(medicaments_to_print, template)
        pdf.seek(0)

        # Return PDF for inline preview
        from flask import send_file

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"medicaments_event_{event.event_number}.pdf",
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("events.view_packs", event_id=event_id))


@events_bp.route("/api/get_character_ticket")
@login_required
def get_character_ticket():
    event_id = request.args.get("event_id")
    char_id_str = request.args.get("character_id")
    if not event_id or not char_id_str or "." not in char_id_str:
        return (
            jsonify({"success": False, "error": "Missing or invalid parameters"}),
            400,
        )
    user_id, character_id = char_id_str.split(".")
    character = Character.query.filter_by(user_id=user_id, character_id=character_id).first()
    if not character:
        return jsonify({"success": False, "error": "Character not found"}), 404
    ticket = EventTicket.query.filter_by(event_id=event_id, character_id=character.id).first()
    if not ticket:
        return jsonify({"success": True, "ticket": None})
    return jsonify(
        {
            "success": True,
            "ticket": {
                "ticket_type": (
                    ticket.ticket_type.value
                    if hasattr(ticket.ticket_type, "value")
                    else ticket.ticket_type
                ),
                "meal_ticket": ticket.meal_ticket,
                "requires_bunk": getattr(ticket, "requires_bunk", False),
                "price_paid": ticket.price_paid,
            },
        }
    )


@events_bp.route("/api/events")
@login_required
def get_events():
    """Get list of events with optional filters."""
    # Get filter parameters
    has_started = request.args.get("has_started", type=lambda v: v.lower() == "true")
    has_finished = request.args.get("has_finished", type=lambda v: v.lower() == "true")
    early_booking_available = request.args.get(
        "early_booking_available", type=lambda v: v.lower() == "true"
    )
    has_downtime = request.args.get("has_downtime", type=lambda v: v.lower() == "true")
    event_type = request.args.get("event_type")

    # Start with base query
    query = Event.query

    # Apply filters
    if has_started is not None:
        if has_started:
            query = query.filter(Event.start_date <= datetime.now())

    if has_finished is not None:
        if has_finished:
            query = query.filter(Event.end_date <= datetime.now())

    if early_booking_available is not None:
        if early_booking_available:
            query = query.filter(Event.early_booking_deadline > datetime.now())

    if has_downtime is not None:
        from models.tools.downtime import DowntimePeriod

        if has_downtime:
            query = query.filter(
                Event.id.in_(
                    db.session.query(DowntimePeriod.event_id).filter(
                        DowntimePeriod.event_id.isnot(None)
                    )
                )
            )

    if event_type:
        query = query.filter(Event.event_type == event_type)

    # Order by end date descending
    events = query.order_by(Event.end_date.desc()).all()

    return jsonify(
        {
            "events": [
                {
                    "id": event.id,
                    "event_number": event.event_number,
                    "name": event.name,
                    "start_date": event.start_date.strftime("%Y-%m-%d"),
                    "end_date": event.end_date.strftime("%Y-%m-%d"),
                    "early_booking_deadline": event.early_booking_deadline.strftime("%Y-%m-%d"),
                    "booking_deadline": (
                        event.booking_deadline.strftime("%Y-%m-%d")
                        if event.booking_deadline
                        else None
                    ),
                    "event_type": event.event_type.value,
                }
                for event in events
            ]
        }
    )


@events_bp.route("/api/user_ticket_status")
@login_required
def user_ticket_status():
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({"success": False, "error": "Missing event_id"}), 400
    # Check for adult ticket (any character)
    user_characters = Character.query.filter_by(user_id=current_user.id).all()
    character_ids = [char.id for char in user_characters]
    has_adult_ticket = False
    if character_ids:
        has_adult_ticket = (
            EventTicket.query.filter(
                EventTicket.event_id == event_id,
                EventTicket.character_id.in_(character_ids),
                EventTicket.ticket_type == "adult",
            ).first()
            is not None
        )
    # Check for crew ticket
    has_crew_ticket = (
        EventTicket.query.filter_by(
            event_id=event_id, user_id=current_user.id, ticket_type="crew"
        ).first()
        is not None
    )
    return jsonify(
        {"success": True, "has_adult_ticket": has_adult_ticket, "has_crew_ticket": has_crew_ticket}
    )


@events_bp.route("/get-user-event-status", methods=["GET"])
@login_required
def get_user_event_status():
    event_id = request.args.get("event_id")
    user_id = request.args.get("user_id")

    if not event_id or not user_id:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid user ID"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check for existing crew ticket
    has_crew_ticket = (
        EventTicket.query.filter_by(event_id=event_id, user_id=user_id, ticket_type="crew").first()
        is not None
    )

    # Check for existing adult ticket across all of the user's characters
    user_character_ids = [c.id for c in user.characters]
    has_adult_ticket = False
    if user_character_ids:
        has_adult_ticket = (
            EventTicket.query.filter(
                EventTicket.event_id == event_id,
                EventTicket.character_id.in_(user_character_ids),
                EventTicket.ticket_type == "adult",
            ).first()
            is not None
        )

    return jsonify(
        {"success": True, "has_crew_ticket": has_crew_ticket, "has_adult_ticket": has_adult_ticket}
    )


@events_bp.route("/<int:event_id>/packs/debug", methods=["GET"])
@login_required
@admin_required
def debug_packs(event_id):
    """Debug route to see what pack data looks like."""
    # event = Event.query.get_or_404(event_id)  # Remove unused variable

    # Get all characters with tickets for this event
    character_tickets = (
        EventTicket.query.filter_by(event_id=event_id)
        .filter(EventTicket.character_id.isnot(None))
        .all()
    )

    debug_data = []
    for ticket in character_tickets:
        character = Character.query.get(ticket.character_id)
        if character:
            pack = character.pack or Pack()
            try:
                pack_dict = pack.to_dict()
                import json

                json_str = json.dumps(pack_dict)
                debug_data.append(
                    {
                        "character_id": character.id,
                        "character_name": character.name,
                        "pack_dict": pack_dict,
                        "json_str": json_str,
                        "json_length": len(json_str),
                    }
                )
            except Exception as e:
                debug_data.append(
                    {
                        "character_id": character.id,
                        "character_name": character.name,
                        "error": str(e),
                    }
                )

    return jsonify(debug_data)
