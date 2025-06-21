import json
from datetime import datetime, timedelta
from unittest.mock import patch

from models.enums import Role
from models.event import Event
from models.tools.character import Character
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


def test_create_event_get(test_client, admin_user):
    """Test GET request to create event page."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get("/events/new")
    assert response.status_code == 200


def test_create_event_get_unauthorized(test_client, authenticated_user):
    """Test create event page when user is not admin."""
    response = test_client.get("/events/new", follow_redirects=True)
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden


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


def test_edit_event_get(test_client, admin_user, db):
    """Test GET request to edit event page."""
    # Create a test event
    event = Event(
        event_number="TEST002",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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

    response = test_client.get(f"/events/{event.id}/edit", follow_redirects=True)
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden


def test_purchase_ticket_get(test_client, authenticated_user, db):
    """Test GET request to purchase ticket page."""
    # Create a test event
    event = Event(
        event_number="TEST005",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    # Should redirect due to no active character


def test_assign_ticket_get(test_client, admin_user, db):
    """Test GET request to assign ticket page."""
    # Create a test event
    event = Event(
        event_number="TEST007",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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


def test_purchase_ticket_post_multiple_self_tickets(test_client, authenticated_user, db):
    """Test that only one self-ticket (adult/crew) is allowed per purchase."""
    event = Event(
        event_number="TEST008",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    from models.tools.event_ticket import EventTicket

    tickets = EventTicket.query.filter_by(event_id=event.id, character_id=character.id).all()
    assert len(tickets) == 1


def test_purchase_ticket_post_multiple_child_tickets(test_client, authenticated_user, db):
    """Test that multiple child tickets are allowed for self."""
    event = Event(
        event_number="TEST009",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    from models.tools.event_ticket import EventTicket

    tickets = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="child_12_15"
    ).all()
    assert len(tickets) == 2
    assert tickets[0].child_name == "Alice Smith"
    assert tickets[1].child_name == "Bob Jones"


def test_npc_cannot_buy_crew_ticket_for_others(test_client, db):
    """Test that NPCs cannot buy crew tickets for others (crew tickets are only for self)."""
    event = Event(
        event_number="TEST010",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    npc_user = User(
        email="npc@example.com", roles="npc", player_id=9999, first_name="NPC", surname="User"
    )
    db.session.add(npc_user)
    db.session.commit()

    # Create a character for someone else
    other_character = Character(
        user_id=12345,
        character_id=2,
        name="Other Character",
        status="active",
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
    from models.tools.event_ticket import EventTicket

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
    npc_user = User(
        email="npc2@example.com", roles="npc", player_id=9998, first_name="NPC", surname="User"
    )
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
    from models.tools.event_ticket import EventTicket

    ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=npc_user.id, ticket_type="crew"
    ).first()
    assert ticket is not None
    assert ticket.character_id is None  # Crew tickets don't have characters


def test_adult_crew_ticket_exclusivity(test_client, authenticated_user, db):
    """Test that a user cannot have both an adult ticket and a crew ticket for the same event."""
    event = Event(
        event_number="TEST012",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    from models.tools.event_ticket import EventTicket

    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, character_id=character.id, ticket_type="adult"
    ).first()
    crew_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="crew"
    ).first()
    assert adult_ticket is not None
    assert crew_ticket is None


def test_crew_adult_ticket_exclusivity(test_client, rules_team_user, db):
    """Test that a user cannot have both a crew ticket and an adult ticket for the same event."""
    event = Event(
        event_number="TEST013",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    from models.tools.event_ticket import EventTicket

    crew_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=rules_team_user.id, ticket_type="crew"
    ).first()
    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, character_id=character.id, ticket_type="adult"
    ).first()
    assert crew_ticket is not None
    assert adult_ticket is None


def test_child_tickets_with_adult_ticket(test_client, authenticated_user, db):
    """Test that child tickets can be purchased even when user has an adult ticket."""
    event = Event(
        event_number="TEST014",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    from models.tools.event_ticket import EventTicket

    adult_ticket = EventTicket.query.filter_by(
        event_id=event.id, character_id=character.id, ticket_type="adult"
    ).first()
    child_ticket = EventTicket.query.filter_by(
        event_id=event.id, user_id=authenticated_user.id, ticket_type="child_12_15"
    ).first()
    assert adult_ticket is not None
    assert child_ticket is not None
    assert child_ticket.child_name == "Child Name"


def test_user_ticket_status_api(test_client, authenticated_user, db):
    """Test the user ticket status API endpoint."""
    event = Event(
        event_number="TEST015",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now() + timedelta(days=30),
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
    from models.tools.event_ticket import EventTicket

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
