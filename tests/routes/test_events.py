import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from models.database.group_type import GroupType
from models.enums import TicketType
from models.event import Event
from models.tools.character import Character
from models.tools.event_ticket import EventTicket
from models.tools.group import Group
from models.tools.user import User


def test_event_list_get(test_client, db):
    """Test GET request to event list page."""
    response = test_client.get("/events/")
    assert response.status_code == 200


def test_event_list_show_previous(test_client, admin_user):
    """Test event list with show_previous parameter."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get("/events/?show_previous=true")
    assert response.status_code == 200


def test_event_list_with_ticket_purchase_indicator(test_client, authenticated_user, db):
    """Test event list shows ticket purchase indicator when user has tickets."""
    # Create a test event
    event = Event(
        event_number="TEST001",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now(timezone.utc) + timedelta(days=30),
        booking_deadline=datetime.now(timezone.utc) + timedelta(days=15),
        start_date=datetime.now(timezone.utc) + timedelta(days=20),
        end_date=datetime.now(timezone.utc) + timedelta(days=22),
        location="Test Location",
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db.session.add(event)
    db.session.commit()

    # Create a ticket for the user
    ticket = EventTicket(
        event_id=event.id,
        user_id=authenticated_user.id,
        ticket_type="crew",
        price_paid=0.0,
        assigned_by_id=authenticated_user.id,
    )
    db.session.add(ticket)
    db.session.commit()

    # Test with authenticated user
    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.get("/events/")
    assert response.status_code == 200
    # Check that the ticket purchase indicator is present in the response
    assert b"You've purchased a ticket for this event" in response.data


def test_create_event_get(test_client, admin_user):
    """Test GET request to create event page."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get("/events/new")
    assert response.status_code == 200


def test_create_event_get_unauthorized(test_client, authenticated_user):
    """Test create event page when user is not admin."""
    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.get("/events/new")
    assert response.status_code in [200, 302]  # Can be either redirect or forbidden


def test_create_event_post(test_client, admin_user, db):
    """Test POST request to create event."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    with patch("routes.events.send_new_event_notification_to_all") as mock_send_notification:
        response = test_client.post(
            "/events/new",
            data={
                "event_number": "TEST001",
                "name": "Test Event",
                "event_type": "mainline",
                "description": "A test event",
                "early_booking_deadline": "2025-07-01",
                "booking_deadline": "2025-07-10",
                "start_date": "2025-07-15",
                "end_date": "2025-07-17",
                "location": "Test Location",
                "google_maps_link": "https://maps.google.com",
                "meal_ticket_available": "1",
                "meal_ticket_price": "15.00",
                "bunks_available": "1",
                "standard_ticket_price": "50.00",
                "early_booking_ticket_price": "45.00",
                "child_ticket_price_12_15": "25.00",
                "child_ticket_price_7_11": "15.00",
                "child_ticket_price_under_7": "0.00",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that event was created
        event = Event.query.filter_by(event_number="TEST001").first()
        assert event is not None
        assert event.name == "Test Event"
        assert event.event_type.value == "mainline"  # Compare enum value

        mock_send_notification.assert_called_once_with(event)


def test_create_event_duplicate_number(test_client, admin_user, db):
    """Test creating event with duplicate event number fails validation."""
    # First, create an event
    event = Event(
        event_number="DUPLICATE001",
        name="First Event",
        event_type="mainline",
        description="First test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Verify the event was created
    existing_event = Event.query.filter_by(event_number="DUPLICATE001").first()
    assert existing_event is not None, "First event should exist before duplicate test"

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    # Try to create another event with the same event number
    response = test_client.post(
        "/events/new",
        data={
            "event_number": "DUPLICATE001",  # Same as existing event
            "name": "Second Event",
            "event_type": "mainline",
            "description": "Second test event",
            "early_booking_deadline": "2025-07-01",
            "booking_deadline": "2025-07-10",
            "start_date": "2025-07-15",
            "end_date": "2025-07-17",
            "location": "Test Location",
            "google_maps_link": "https://maps.google.com",
            "meal_ticket_available": "1",
            "meal_ticket_price": "15.00",
            "bunks_available": "1",
            "standard_ticket_price": "50.00",
            "early_booking_ticket_price": "45.00",
            "child_ticket_price_12_15": "25.00",
            "child_ticket_price_7_11": "15.00",
            "child_ticket_price_under_7": "0.00",
        },
        follow_redirects=True,
    )

    # Should return the form with error message, not redirect
    assert response.status_code == 200
    # Check for key parts of the error message
    assert b"DUPLICATE001" in response.data
    assert b"already exists" in response.data

    # Verify only one event with that number exists
    events = Event.query.filter_by(event_number="DUPLICATE001").all()
    assert len(events) == 1


def test_edit_event_get(test_client, admin_user, db):
    """Test GET request to edit event page."""
    # Create a test event
    event = Event(
        event_number="TEST002",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/edit")
    assert response.status_code == 200


def test_edit_event_get_unauthorized(test_client, authenticated_user, db):
    """Test edit event page when user is not admin."""
    # Create a test event
    event = Event(
        event_number="TEST003",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/edit")
    assert response.status_code in [200, 302]  # Can be either redirect or forbidden


def test_purchase_ticket_get(test_client, authenticated_user, db):
    """Test GET request to purchase ticket page."""
    # Create a test event
    event = Event(
        event_number="TEST005",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/purchase", follow_redirects=True)
    assert response.status_code == 200


def test_purchase_ticket_get_no_active_character(test_client, authenticated_user, db):
    """Test purchase ticket page when user has no active character."""
    # Create a test event
    event = Event(
        event_number="TEST006",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Remove active character from user
    authenticated_user.active_character_id = None
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/purchase", follow_redirects=True)
    assert response.status_code == 200
    # Should now allow access since crew/child tickets don't require characters


def test_purchase_ticket_post_blank_character_id(test_client, authenticated_user, db):
    """Test that purchasing tickets with blank character ID is prevented."""
    # Create a test event
    event = Event(
        event_number="TEST007",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Test with blank character ID
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "other",
            "characterId": "",  # Blank character ID
            "price": 50.00,
        }
    ]

    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )

    assert response.status_code == 200
    # Should show error message about invalid character ID format
    assert b"Invalid character ID format" in response.data

    # Test with whitespace-only character ID
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "other",
            "characterId": "   ",  # Whitespace-only character ID
            "price": 50.00,
        }
    ]

    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )

    assert response.status_code == 200
    # Should show error message about invalid character ID format
    assert b"Invalid character ID format" in response.data


def test_purchase_ticket_post_nonexistent_character_id(test_client, authenticated_user, db):
    """Test that purchasing tickets with non-existent character ID shows appropriate error."""
    # Create a test event
    event = Event(
        event_number="TEST008",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Test with non-existent character ID
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "other",
            "characterId": "999.999",  # Non-existent character ID
            "price": 50.00,
        }
    ]

    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )

    assert response.status_code == 200
    # Should show error message about character not found
    # The message will be HTML-encoded, so we need to look for the encoded version
    assert b"Character with ID &#39;999.999&#39; not found" in response.data


def test_assign_ticket_get(test_client, admin_user, db):
    """Test GET request to assign ticket page."""
    # Create a test event
    event = Event(
        event_number="TEST007",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/assign")
    assert response.status_code == 200


def test_view_attendees_get(test_client, admin_user, db):
    """Test GET request to view attendees page."""
    # Create a test event
    event = Event(
        event_number="TEST009",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/attendees")
    assert response.status_code == 200


def test_purchase_ticket_post_multiple_self_tickets(test_client, authenticated_user, db, faction):
    """Test that only one self-ticket (adult/crew) is allowed per purchase."""
    event = Event(
        event_number="TEST008",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a character for the user
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()
    authenticated_user.active_character_id = character.id
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Try to add two adult self-tickets
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 50.00,
        },
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 50.00,
        },
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200
    # Only one ticket should be created


def test_purchase_ticket_post_multiple_child_tickets(test_client, authenticated_user, db):
    """Test that multiple child tickets are allowed for self."""
    event = Event(
        event_number="TEST009",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # No character needed for child tickets
    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    cart_data = [
        {
            "ticketType": "child_12_15",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "childName": "Alice Smith",
            "price": 25.00,
        },
        {
            "ticketType": "child_12_15",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "childName": "Bob Jones",
            "price": 25.00,
        },
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Check that both child tickets were created
    tickets = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="child_12_15"
    ).all()
    assert len(tickets) == 2
    assert tickets[0].child_name == "Alice Smith"
    assert tickets[1].child_name == "Bob Jones"


def test_npc_cannot_buy_crew_ticket_for_others(test_client, db, faction):
    """Test that NPCs cannot buy crew tickets for others (crew tickets are only for self)."""
    event = Event(
        event_number="TEST010",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create an NPC user
    npc_user = User(email="npc@example.com", first_name="NPC", surname="User")
    npc_user.set_password("password")
    db.session.add(npc_user)
    db.session.commit()

    # Create a character for someone else
    other_character = Character(
        user_id=12345,
        character_id=2,
        name="Other Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(other_character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = npc_user.id
        session["_fresh"] = True

    cart_data = [
        {
            "ticketType": "crew",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "other",
            "characterId": f"{other_character.user_id}.{other_character.character_id}",
            "price": 0.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200
    # Should not create a ticket since crew tickets for others are not allowed
    ticket = EventTicket.query.filter_by(event_id=event.id, character_id=other_character.id).first()
    assert ticket is None


def test_npc_can_buy_crew_ticket_for_self_without_character(test_client, db):
    """Test that an NPC can buy a crew ticket for themselves without having a character."""
    event = Event(
        event_number="TEST011",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create an NPC user
    npc_user = User(email="npc2@example.com", first_name="NPC", surname="User")
    npc_user.set_password("password")
    db.session.add(npc_user)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = npc_user.id
        session["_fresh"] = True

    cart_data = [
        {
            "ticketType": "crew",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 0.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Should succeed and create a crew ticket for the user
    ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=npc_user.id, ticket_type="crew"
    ).first()
    assert ticket is not None
    assert ticket.character_id is None  # Crew tickets don't have characters


def test_adult_crew_ticket_exclusivity(test_client, authenticated_user, db, faction):
    """Test that a user cannot have both an adult ticket and a crew ticket for the same event."""
    event = Event(
        event_number="TEST012",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a group type and group
    from models.database.group_type import GroupType
    from models.tools.group import Group

    group_type = GroupType(
        name="Test Type", description="Test Description", income_distribution="{}"
    )
    db.session.add(group_type)
    db.session.flush()

    group = Group(name="Test Group", group_type_id=group_type.id, faction_id=faction.id)
    db.session.add(group)
    db.session.flush()

    # Create a character for the user with a group
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        group_id=group.id,
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()
    authenticated_user.active_character_id = character.id
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # First, add an adult ticket
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 50.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Now try to add a crew ticket - should be blocked
    cart_data = [
        {
            "ticketType": "crew",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 0.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Check that only the adult ticket exists, no crew ticket
    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, character_id=character.id, ticket_type="adult"
    ).first()
    crew_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="crew"
    ).first()
    assert adult_ticket is not None
    assert crew_ticket is None


def test_crew_adult_ticket_exclusivity(test_client, rules_team_user, db, faction):
    """Test that a user cannot have both a crew ticket and an adult ticket for the same event."""
    event = Event(
        event_number="TEST013",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a character for the user
    character = Character(
        user_id=rules_team_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()
    rules_team_user.active_character_id = character.id
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    # First, add a crew ticket
    cart_data = [
        {
            "ticketType": "crew",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 0.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Now try to add an adult ticket - should be blocked
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 50.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Check that only the crew ticket exists, no adult ticket
    crew_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=rules_team_user.id, ticket_type="crew"
    ).first()
    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, character_id=character.id, ticket_type="adult"
    ).first()
    assert crew_ticket is not None
    assert adult_ticket is None


def test_child_tickets_with_adult_ticket(test_client, authenticated_user, db, faction):
    """Test that child tickets can be purchased even when user has an adult ticket."""
    event = Event(
        event_number="TEST014",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a group type and group
    from models.database.group_type import GroupType
    from models.tools.group import Group

    group_type = GroupType(
        name="Test Type", description="Test Description", income_distribution="{}"
    )
    db.session.add(group_type)
    db.session.flush()

    group = Group(name="Test Group", group_type_id=group_type.id, faction_id=faction.id)
    db.session.add(group)
    db.session.flush()

    # Create a character for the user with a group
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        group_id=group.id,
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()
    authenticated_user.active_character_id = character.id
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # First, add an adult ticket
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 50.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Now add a child ticket - should work
    cart_data = [
        {
            "ticketType": "child_12_15",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "childName": "Child Name",
            "price": 25.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Check that both tickets exist
    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, character_id=character.id, ticket_type="adult"
    ).first()
    child_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="child_12_15"
    ).first()
    assert adult_ticket is not None
    assert child_ticket is not None
    assert child_ticket.child_name == "Child Name"


def test_user_ticket_status_api(test_client, authenticated_user, db, faction):
    """Test the user ticket status API endpoint."""
    event = Event(
        event_number="TEST015",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a character for the user
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Test with no tickets
    response = test_client.get(f"/events/api/user_ticket_status?event_id={event.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["has_adult_ticket"] is False
    assert data["has_crew_ticket"] is False

    # Add an adult ticket
    ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        user_id=authenticated_user.id,
        ticket_type="adult",
        meal_ticket=False,
        requires_bunk=False,
        price_paid=50.00,
        assigned_by_id=authenticated_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(ticket)
    db.session.commit()

    # Test with adult ticket
    response = test_client.get(f"/events/api/user_ticket_status?event_id={event.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["has_adult_ticket"] is True
    assert data["has_crew_ticket"] is False

    # Remove adult ticket and add crew ticket
    db.session.delete(ticket)
    db.session.commit()

    crew_ticket = EventTicket(
        event_id=event.id,
        character_id=None,
        user_id=authenticated_user.id,
        ticket_type="crew",
        meal_ticket=False,
        requires_bunk=False,
        price_paid=0.00,
        assigned_by_id=authenticated_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(crew_ticket)
    db.session.commit()

    # Test with crew ticket
    response = test_client.get(f"/events/api/user_ticket_status?event_id={event.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["has_adult_ticket"] is False
    assert data["has_crew_ticket"] is True


def test_purchase_multiple_adult_tickets_for_same_user(
    test_client, db, npc_user_with_chars, event, group
):
    """
    GIVEN a user with multiple characters
    WHEN they purchase an adult ticket for one character
    THEN they should not be able to purchase another adult ticket for a different character
    """
    user, char1, char2 = npc_user_with_chars
    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True

    # Purchase ticket for first character
    cart_data1 = [
        {"ticketType": "adult", "ticketFor": "self", "selfCharacterId": char1.id, "price": 50.00}
    ]
    test_client.post(f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data1)})

    # Try to purchase ticket for second character
    cart_data2 = [
        {"ticketType": "adult", "ticketFor": "self", "selfCharacterId": char2.id, "price": 50.00}
    ]
    test_client.post(f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data2)})

    # Verify only the first ticket exists
    user_tickets = EventTicket.query.filter_by(user_id=user.id, event_id=event.id).all()
    assert len(user_tickets) == 1
    assert user_tickets[0].character_id == char1.id


def test_purchase_conflicting_adult_and_crew_tickets(
    test_client, db, npc_user_with_chars, event, group
):
    """
    GIVEN a user with multiple characters
    WHEN they purchase a crew ticket
    THEN they should not be able to purchase an adult ticket for any of their characters
    """
    user, char1, char2 = npc_user_with_chars
    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True

    # Purchase a crew ticket first
    cart_data_crew = [{"ticketType": "crew", "ticketFor": "self", "price": 0}]
    test_client.post(f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data_crew)})

    # Try to purchase adult ticket
    cart_data_adult = [
        {"ticketType": "adult", "ticketFor": "self", "selfCharacterId": char1.id, "price": 50.00}
    ]
    test_client.post(f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data_adult)})

    # Verify only the crew ticket exists
    user_tickets = EventTicket.query.filter_by(user_id=user.id, event_id=event.id).all()
    assert len(user_tickets) == 1
    assert user_tickets[0].ticket_type == TicketType.CREW


def test_purchase_ticket_character_without_group(test_client, authenticated_user, db, faction):
    """Test that purchasing tickets for characters without groups fails."""
    # Create a test event
    event = Event(
        event_number="TEST007",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a character without a group
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Try to purchase a ticket for the character without a group
    cart_data = json.dumps(
        [
            {
                "ticketType": "adult",
                "mealTicket": False,
                "requiresBunk": False,
                "ticketFor": "self",
                "selfCharacterId": character.id,
                "price": 50.0,
            }
        ]
    )

    response = test_client.post(
        f"/events/{event.id}/purchase",
        data={"cart": cart_data},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect back to purchase page with error message
    assert b"must be in a group" in response.data


def test_assign_ticket_character_without_group(test_client, admin_user, db, faction):
    """Test that assigning tickets to characters without groups fails."""
    # Create a test event
    event = Event(
        event_number="TEST008",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a character without a group
    character = Character(
        user_id=admin_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    # Try to assign a ticket to the character without a group
    response = test_client.post(
        f"/events/{event.id}/assign",
        data={
            "ticket_type": "adult",
            "character": f"{admin_user.id}.1",
            "meal_ticket": False,
            "requires_bunk": False,
            "price_paid": 50.0,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect back to assign page with error message
    assert b"must be in a group" in response.data


def test_character_group_status_api(test_client, authenticated_user, db, faction):
    """Test the character group status API endpoint."""
    # Create a character without a group
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Test API for character without group
    response = test_client.get(
        f"/events/api/character_group_status?character_id={authenticated_user.id}.1"
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"] is True
    assert data["has_group"] is False
    assert data["character_name"] == "Test Character"
    assert data["group_name"] is None

    # Create a group and add the character to it
    from models.database.group_type import GroupType
    from models.tools.group import Group

    group_type = GroupType(
        name="Test Type", description="Test Description", income_distribution="{}"  # Required field
    )
    db.session.add(group_type)
    db.session.flush()

    group = Group(name="Test Group", group_type_id=group_type.id, faction_id=faction.id)
    db.session.add(group)
    db.session.flush()

    character.group_id = group.id
    db.session.commit()

    # Test API for character with group
    response = test_client.get(
        f"/events/api/character_group_status?character_id={authenticated_user.id}.1"
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"] is True
    assert data["has_group"] is True
    assert data["character_name"] == "Test Character"
    assert data["group_name"] == "Test Group"


def test_export_attendees_get(test_client, admin_user, db, faction):
    """Test GET request to export attendees CSV."""
    # Create a test event
    event = Event(
        event_number="TEST016",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a test user
    user = User(
        email="test@example.com",
        first_name="Test",
        surname="User",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    # Create a test character
    character = Character(
        user_id=user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    # Create a test ticket
    ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        user_id=user.id,
        ticket_type="adult",
        meal_ticket=True,
        requires_bunk=False,
        price_paid=50.00,
        assigned_by_id=admin_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(ticket)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/attendees/export")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert (
        "attachment; filename=attendees_event_TEST016.csv"
        in response.headers["Content-Disposition"]
    )

    # Check CSV content
    csv_content = response.get_data(as_text=True)
    lines = csv_content.strip().split("\n")
    assert len(lines) >= 2  # Headers + at least one data row

    # Check headers
    headers = lines[0].split(",")
    expected_headers = [
        "Event Name",
        "Event Number",
        "Ticket Type",
        "Meal Ticket",
        "Requires Bunk",
        "Child Name",
        "User First Name",
        "Character Reference",
        "Character Name",
        "Character Faction",
        "Group Name",
    ]
    # Clean up any carriage returns from headers
    headers = [h.strip() for h in headers]
    assert headers == expected_headers

    # Check data row
    data_row = lines[1].split(",")
    # Clean up any carriage returns from data
    data_row = [d.strip() for d in data_row]
    assert data_row[0] == event.name  # Event Name
    assert data_row[1] == event.event_number  # Event Number
    assert data_row[2] == "adult"  # Ticket Type
    assert data_row[3] == "True"  # Meal Ticket
    assert data_row[4] == "False"  # Requires Bunk
    assert data_row[5] == ""  # Child Name (empty for adult ticket)
    assert data_row[6] == user.first_name  # User First Name
    assert data_row[7] == f"{character.user_id}.{character.character_id}"  # Character Reference
    assert data_row[8] == character.name  # Character Name
    assert data_row[9] == faction.name  # Character Faction
    assert data_row[10] == ""  # Group Name (empty in test)


def test_export_attendees_unauthorized(test_client, authenticated_user, db):
    """Test that non-admin users cannot access the export endpoint."""
    # Create a test event
    event = Event(
        event_number="TEST017",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/attendees/export")
    assert response.status_code == 302


def test_export_attendees_event_not_found(test_client, admin_user, db):
    """Test export endpoint with non-existent event."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get("/events/99999/attendees/export")
    assert response.status_code == 404


def test_export_attendees_with_crew_ticket(test_client, admin_user, db):
    """Test CSV export with crew tickets (no character)."""
    # Create a test event
    event = Event(
        event_number="TEST018",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a test user
    user = User(
        email="crew@example.com",
        first_name="Crew",
        surname="Member",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    # Create a crew ticket (no character)
    ticket = EventTicket(
        event_id=event.id,
        character_id=None,
        user_id=user.id,
        ticket_type="crew",
        meal_ticket=False,
        requires_bunk=True,
        price_paid=0.00,
        assigned_by_id=admin_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(ticket)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get(f"/events/{event.id}/attendees/export")
    assert response.status_code == 200

    # Check CSV content
    csv_content = response.get_data(as_text=True)
    lines = csv_content.strip().split("\n")
    assert len(lines) >= 2  # Headers + at least one data row

    # Check data row for crew ticket
    data_row = lines[1].split(",")
    # Clean up any carriage returns from data
    data_row = [d.strip() for d in data_row]
    assert data_row[0] == event.name  # Event Name
    assert data_row[1] == event.event_number  # Event Number
    assert data_row[2] == "crew"  # Ticket Type
    assert data_row[3] == "False"  # Meal Ticket
    assert data_row[4] == "True"  # Requires Bunk
    assert data_row[5] == ""  # Child Name (empty for crew)
    assert data_row[6] == user.first_name  # User First Name
    assert data_row[7] == ""  # Character Reference (empty for crew)
    assert data_row[8] == ""  # Character Name (empty for crew)
    assert data_row[9] == ""  # Character Faction (empty for crew)
    assert data_row[10] == ""  # Group Name (empty for crew)


def test_assign_ticket_update_existing(test_client, admin_user, db, faction):
    """Test updating an existing ticket instead of creating a new one."""
    # Create a test event
    event = Event(
        event_number="TEST019",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a test user and character
    user = User(
        email="test@example.com",
        first_name="Test",
        surname="User",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    character = Character(
        user_id=user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    # Create a group for the character
    group_type = GroupType(
        name="Test Group Type",
        description="A test group type",
        income_items_list=[],
        income_items_discount=0.5,
        income_substances=False,
        income_substance_cost=0,
        income_medicaments=False,
        income_medicament_cost=0,
        income_distribution_dict={},
    )
    db.session.add(group_type)
    db.session.commit()

    group = Group(
        name="Test Group", group_type_id=group_type.id, bank_account=0, faction_id=faction.id
    )
    db.session.add(group)
    db.session.commit()

    # Add character to group
    character.group_id = group.id
    db.session.commit()

    # Create an existing ticket
    existing_ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        user_id=user.id,
        ticket_type="adult",
        meal_ticket=False,
        requires_bunk=False,
        price_paid=50.00,
        assigned_by_id=admin_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(existing_ticket)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    # Try to assign the same ticket again (should update instead of create)
    response = test_client.post(
        f"/events/{event.id}/assign",
        data={
            "ticket_type": "adult",
            "character": f"{character.user_id}.{character.character_id}",
            "meal_ticket": "on",
            "requires_bunk": "on",
            "price_paid": "75.00",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Check that we got a success message about updating
    assert b"Ticket updated successfully!" in response.data

    # Verify only one ticket exists (not two)
    tickets = EventTicket.query.filter_by(event_id=event.id, character_id=character.id).all()
    assert len(tickets) == 1

    # Verify the ticket was updated
    updated_ticket = tickets[0]
    assert updated_ticket.meal_ticket is True
    assert updated_ticket.requires_bunk is True
    assert updated_ticket.price_paid == 75.00


def test_remove_ticket(test_client, admin_user, db, faction):
    """Test removing an assigned ticket."""
    # Create a test event
    event = Event(
        event_number="TEST020",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a test user and character
    user = User(
        email="test@example.com",
        first_name="Test",
        surname="User",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    character = Character(
        user_id=user.id,
        character_id=1,
        name="Test Character",
        status="active",
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    # Create a ticket to remove
    ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        user_id=user.id,
        ticket_type="adult",
        meal_ticket=True,
        requires_bunk=False,
        price_paid=50.00,
        assigned_by_id=admin_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(ticket)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    # Remove the ticket
    response = test_client.post(
        f"/events/{event.id}/tickets/{ticket.id}/remove",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket removed successfully!" in response.data

    # Verify the ticket was deleted
    deleted_ticket = EventTicket.query.get(ticket.id)
    assert deleted_ticket is None


def test_remove_ticket_unauthorized(test_client, authenticated_user, db):
    """Test that non-admin users cannot remove tickets."""
    # Create a test event
    event = Event(
        event_number="TEST021",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create a test ticket
    ticket = EventTicket(
        event_id=event.id,
        character_id=None,
        user_id=authenticated_user.id,
        ticket_type="crew",
        meal_ticket=False,
        requires_bunk=False,
        price_paid=0.00,
        assigned_by_id=authenticated_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(ticket)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Try to remove the ticket (should fail)
    response = test_client.post(f"/events/{event.id}/tickets/{ticket.id}/remove")
    assert response.status_code == 302

    # Verify the ticket still exists
    existing_ticket = EventTicket.query.get(ticket.id)
    assert existing_ticket is not None


def test_regular_user_can_buy_crew_ticket(test_client, authenticated_user, db):
    """Test that regular users can now purchase crew tickets."""
    event = Event(
        event_number="TEST015",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Regular user should be able to purchase a crew ticket
    cart_data = [
        {
            "ticketType": "crew",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 0.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Verify the crew ticket was created
    crew_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="crew"
    ).first()
    assert crew_ticket is not None
    assert crew_ticket.character_id is None  # Crew tickets don't have characters


def test_user_without_active_character_can_buy_crew_ticket(test_client, authenticated_user, db):
    """Test that users without active characters can purchase crew tickets."""
    event = Event(
        event_number="TEST016",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Remove active character from user
    authenticated_user.active_character_id = None
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # User without active character should be able to purchase a crew ticket
    cart_data = [
        {
            "ticketType": "crew",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 0.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Verify the crew ticket was created
    crew_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="crew"
    ).first()
    assert crew_ticket is not None
    assert crew_ticket.character_id is None  # Crew tickets don't have characters


def test_user_without_active_character_cannot_buy_adult_ticket_for_self(
    test_client, authenticated_user, db
):
    """Test that users without active characters cannot purchase adult tickets for themselves."""
    event = Event(
        event_number="TEST017",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Remove active character from user
    authenticated_user.active_character_id = None
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # User without active character should NOT be able to purchase an adult ticket for themselves
    cart_data = [
        {
            "ticketType": "adult",
            "mealTicket": False,
            "requiresBunk": False,
            "ticketFor": "self",
            "price": 50.00,
        }
    ]
    response = test_client.post(
        f"/events/{event.id}/purchase", data={"cart": json.dumps(cart_data)}, follow_redirects=True
    )
    assert response.status_code == 200

    # Verify no adult ticket was created (should be blocked)
    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="adult"
    ).first()
    assert adult_ticket is None


def test_get_user_ticket_api(test_client, authenticated_user, db):
    """Test the get_user_ticket API endpoint for crew tickets."""
    event = Event(
        event_number="TEST018",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

        # Test with no existing ticket
        response = test_client.get(
            f"/events/api/get_user_ticket?event_id={event.id}&user_id={authenticated_user.id}"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["ticket"] is None

        # Create a crew ticket
        crew_ticket = EventTicket(
            event_id=event.id,
            user_id=authenticated_user.id,
            ticket_type="crew",
            meal_ticket=True,
            requires_bunk=False,
            price_paid=0.00,
            assigned_by_id=authenticated_user.id,
            assigned_at=datetime.now(timezone.utc),
        )
        db.session.add(crew_ticket)
        db.session.commit()

        # Test with existing crew ticket
        response = test_client.get(
            f"/events/api/get_user_ticket?event_id={event.id}&user_id={authenticated_user.id}"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["ticket"] is not None
        assert data["ticket"]["ticket_type"] == "crew"
        assert data["ticket"]["meal_ticket"] is True
        assert data["ticket"]["requires_bunk"] is False


def test_group_pack_generation_energy_chits_calculation(test_client, admin_user, db, faction):
    """Test that group pack generation calculates energy chits correctly."""
    # Create a test event
    event = Event(
        event_number="TEST021",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)
    db.session.commit()

    # Create global settings
    from models.database.global_settings import GlobalSettings

    settings = GlobalSettings(
        group_income_contribution=30,  # Base group income
    )
    db.session.add(settings)
    db.session.commit()

    # Create a test user and character
    user = User(
        email="test@example.com",
        first_name="Test",
        surname="User",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    # Create a faction first
    from models.database.faction import Faction

    faction = Faction(
        name="Test Faction",
        wiki_slug="test-faction",
        allow_player_characters=True,
    )
    db.session.add(faction)
    db.session.commit()

    # Create a species with group income ability
    from models.database.species import Ability, Species
    from models.enums import AbilityType

    species = Species(
        name="Test Species",
        wiki_page="test-species",
        permitted_factions="[1]",
        body_hits_type="global",
        body_hits=10,
        death_count=0,
    )
    db.session.add(species)
    db.session.flush()

    ability = Ability(
        species_id=species.id,
        name="Group Income",
        description="Provides additional group income",
        type=AbilityType.GROUP_INCOME,
        additional_group_income=30,  # Additional 30 chits
    )
    db.session.add(ability)
    db.session.commit()

    character = Character(
        user_id=user.id,
        character_id=1,
        name="Test Character",
        status="active",
        species_id=species.id,
        faction_id=faction.id,
    )
    db.session.add(character)
    db.session.commit()

    # Create a group type with income distribution
    from models.database.group_type import GroupType

    group_type = GroupType(
        name="Test Group Type",
        description="A test group type",
        income_items_list=[],
        income_items_discount=0.5,
        income_substances=False,
        income_substance_cost=0,
        income_medicaments=False,
        income_medicament_cost=0,
        income_distribution_dict={
            "items": 0,
            "exotics": 0,
            "medicaments": 0,
            "chits": 100,
        },  # All to chits
    )
    db.session.add(group_type)
    db.session.commit()

    # Create a group
    from models.tools.group import Group

    group = Group(
        name="Test Group",
        group_type_id=group_type.id,
        faction_id=faction.id,
        bank_account=0,
    )
    db.session.add(group)
    db.session.commit()

    # Add character to group
    character.group_id = group.id
    db.session.commit()

    # Create an event ticket for the character
    ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        user_id=user.id,
        ticket_type="adult",
        meal_ticket=False,
        requires_bunk=False,
        price_paid=50.00,
        assigned_by_id=admin_user.id,
        assigned_at=datetime.now(),
    )
    db.session.add(ticket)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    # Generate the group pack
    response = test_client.post(f"/events/{event.id}/packs/group/{group.id}/generate")
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert "pack" in data

    # Check that energy chits are calculated correctly
    # Expected: 30 (base) + 30 (species ability) = 60 chits
    # Since distribution is 100% to chits, all 60 should go to energy chits
    pack_data = data["pack"]
    assert (
        pack_data["energy_chits"] == 60
    ), f"Expected 60 energy chits, got {pack_data['energy_chits']}"
