from datetime import datetime, timezone

from models.enums import TicketType
from models.extensions import db


class EventTicket(db.Model):
    __tablename__ = "event_tickets"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ticket_type = db.Column(
        db.Enum(
            TicketType,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    meal_ticket = db.Column(db.Boolean, default=False)
    requires_bunk = db.Column(db.Boolean, default=False)
    price_paid = db.Column(db.Float, nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    child_name = db.Column(db.String(255), nullable=True)

    # Relationships
    event = db.relationship("Event", back_populates="tickets")
    character = db.relationship("Character", back_populates="event_tickets")
    user = db.relationship("User", foreign_keys=[user_id])
    assigned_by = db.relationship(
        "User", foreign_keys=[assigned_by_id], back_populates="assigned_tickets"
    )

    def get_ticket_price(self):
        if self.ticket_type == TicketType.ADULT.value:
            return self.event.get_adult_ticket_price()
        elif self.ticket_type == TicketType.CHILD_12_15.value:
            return self.event.child_ticket_price_12_15
        elif self.ticket_type == TicketType.CHILD_7_11.value:
            return self.event.child_ticket_price_7_11
        elif self.ticket_type == TicketType.CHILD_UNDER_7.value:
            return self.event.child_ticket_price_under_7
        return 0
