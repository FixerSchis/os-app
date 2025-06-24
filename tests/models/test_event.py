from datetime import datetime, timedelta

from models.enums import EventType
from models.event import Event


def test_new_event_with_methods(db):
    """Test creation of a new Event and its methods."""
    # Create dates for testing
    now = datetime.now()
    early_deadline = now + timedelta(days=30)
    booking_deadline = now + timedelta(days=45)
    start_date = now + timedelta(days=60)
    end_date = now + timedelta(days=63)

    event = Event(
        event_number="EV004",
        name="Test Event",
        event_type=EventType.MAINLINE,
        description="A test event for testing purposes",
        early_booking_deadline=early_deadline,
        booking_deadline=booking_deadline,
        start_date=start_date,
        end_date=end_date,
        location="Test Location",
        google_maps_link="https://maps.google.com/test",
        meal_ticket_available=True,
        meal_ticket_price=15.0,
        bunks_available=True,
        standard_ticket_price=100.0,
        early_booking_ticket_price=80.0,
        child_ticket_price_12_15=50.0,
        child_ticket_price_7_11=25.0,
        child_ticket_price_under_7=0.0,
    )

    db.session.add(event)
    db.session.commit()

    # Retrieve and assert
    retrieved_event = Event.query.filter_by(event_number="EV004").first()

    assert retrieved_event is not None
    assert retrieved_event.event_number == "EV004"
    assert retrieved_event.name == "Test Event"
    assert retrieved_event.event_type == EventType.MAINLINE
    assert retrieved_event.description == "A test event for testing purposes"
    assert retrieved_event.location == "Test Location"
    assert retrieved_event.google_maps_link == "https://maps.google.com/test"
    assert retrieved_event.meal_ticket_available is True
    assert retrieved_event.meal_ticket_price == 15.0
    assert retrieved_event.bunks_available is True
    assert retrieved_event.standard_ticket_price == 100.0
    assert retrieved_event.early_booking_ticket_price == 80.0
    assert retrieved_event.child_ticket_price_12_15 == 50.0
    assert retrieved_event.child_ticket_price_7_11 == 25.0
    assert retrieved_event.child_ticket_price_under_7 == 0.0
    assert retrieved_event.id is not None

    # Test methods
    assert retrieved_event.is_upcoming() is True  # End date is in the future
    assert retrieved_event.is_early_booking_available() is True  # Early deadline is in the future
    assert retrieved_event.get_adult_ticket_price() == 80.0  # Should return early booking price

    # Test with past early booking deadline
    past_event = Event(
        event_number="EV005",
        name="Past Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=now - timedelta(days=1),  # Past deadline
        booking_deadline=now + timedelta(days=15),  # Still in future
        start_date=start_date,
        end_date=end_date,
        standard_ticket_price=100.0,
        early_booking_ticket_price=80.0,
        child_ticket_price_12_15=50.0,
        child_ticket_price_7_11=25.0,
        child_ticket_price_under_7=0.0,
    )

    db.session.add(past_event)
    db.session.commit()

    assert past_event.is_early_booking_available() is False
    assert past_event.get_adult_ticket_price() == 100.0  # Should return standard price
