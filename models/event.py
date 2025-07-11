from datetime import datetime

from models.enums import EventType
from models.extensions import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    event_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    event_type = db.Column(
        db.Enum(
            EventType,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    description = db.Column(db.String(1000))
    early_booking_deadline = db.Column(db.DateTime, nullable=False)
    booking_deadline = db.Column(db.DateTime, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(500))
    google_maps_link = db.Column(db.String(500))
    meal_ticket_available = db.Column(db.Boolean, default=False)
    meal_ticket_price = db.Column(db.Float)
    bunks_available = db.Column(db.Boolean, default=False)

    # Ticket prices
    standard_ticket_price = db.Column(db.Float, nullable=False)
    early_booking_ticket_price = db.Column(db.Float, nullable=False)
    child_ticket_price_12_15 = db.Column(db.Float, nullable=False)
    child_ticket_price_7_11 = db.Column(db.Float, nullable=False)
    child_ticket_price_under_7 = db.Column(db.Float, nullable=False)

    # Relationships
    tickets = db.relationship("EventTicket", back_populates="event")

    def is_upcoming(self):
        return self.end_date > datetime.now()

    def is_early_booking_available(self):
        return datetime.now() < self.early_booking_deadline

    def is_booking_available(self):
        # Handle case where booking_deadline might be null during migration
        # If booking_deadline is null, booking is available until the event starts
        if self.booking_deadline is None:
            return datetime.now() < self.start_date
        return datetime.now() < self.booking_deadline

    def get_adult_ticket_price(self):
        if self.is_early_booking_available():
            return self.early_booking_ticket_price
        return self.standard_ticket_price
