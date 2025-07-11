from datetime import datetime, timezone

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models.enums import TicketType
from models.event import Event
from models.tools.event_ticket import EventTicket

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/")
@login_required
def list_tickets():
    now = datetime.now(timezone.utc)

    # Get tickets for user's characters (adult tickets)
    character_ids = [char.id for char in current_user.characters]

    # Upcoming tickets for characters
    upcoming_character_tickets = (
        EventTicket.query.join(Event)
        .filter(EventTicket.character_id.in_(character_ids), Event.end_date >= now)
        .order_by(Event.start_date.asc())
        .all()
    )

    # Past tickets for characters
    past_character_tickets = (
        EventTicket.query.join(Event)
        .filter(EventTicket.character_id.in_(character_ids), Event.end_date < now)
        .order_by(Event.start_date.desc())
        .all()
    )

    character_tickets = upcoming_character_tickets + past_character_tickets

    # Get tickets where user is the recipient (crew tickets, child tickets purchased by user)
    # Upcoming tickets where user is recipient
    upcoming_user_tickets = (
        EventTicket.query.join(Event)
        .filter(EventTicket.user_id == current_user.id, Event.end_date >= now)
        .filter(EventTicket.character_id.is_(None))  # Only tickets without characters
        .order_by(Event.start_date.asc())
        .all()
    )

    # Past tickets where user is recipient
    past_user_tickets = (
        EventTicket.query.join(Event)
        .filter(EventTicket.user_id == current_user.id, Event.end_date < now)
        .filter(EventTicket.character_id.is_(None))  # Only tickets without characters
        .order_by(Event.start_date.desc())
        .all()
    )

    user_tickets = upcoming_user_tickets + past_user_tickets

    # Get tickets assigned by user
    # Upcoming tickets assigned by user
    upcoming_assigned_tickets = (
        EventTicket.query.join(Event)
        .filter(EventTicket.assigned_by_id == current_user.id, Event.end_date >= now)
        .order_by(Event.start_date.asc())
        .all()
    )

    # Past tickets assigned by user
    past_assigned_tickets = (
        EventTicket.query.join(Event)
        .filter(EventTicket.assigned_by_id == current_user.id, Event.end_date < now)
        .order_by(Event.start_date.desc())
        .all()
    )

    assigned_tickets = upcoming_assigned_tickets + past_assigned_tickets

    return render_template(
        "tickets/list.html",
        character_tickets=character_tickets + user_tickets,  # Combine character and user tickets
        assigned_tickets=assigned_tickets,
        TicketType=TicketType,
    )
