import json
from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.enums import CharacterStatus, EventType, Role, TicketType
from models.event import Event
from models.extensions import db
from models.tools.character import Character
from models.tools.event_ticket import EventTicket
from models.tools.user import User
from utils.decorators import user_admin_required
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
        # Only send notification if ticket is for a character with a user
        if character_id:
            character = db.session.get(Character, character_id)
            if character and character.user:
                send_event_ticket_assigned_notification_to_user(
                    character.user, ticket, event, character
                )
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
    event = Event.query.get_or_404(event_id)
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
    # Only send notification if ticket is for a character with a user
    if character_id:
        character = db.session.get(Character, character_id)
        if character and character.user:
            send_event_ticket_assigned_notification_to_user(
                character.user, ticket, event, character
            )
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
