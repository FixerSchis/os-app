import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models.tools.event_ticket import EventTicket
from models.event import Event
from models.enums import TicketType
from models.tools.character import Character
from models.enums import CharacterStatus
from models.tools.user import User
from datetime import datetime, timedelta

def test_list_tickets_get(test_client, authenticated_user):
    """Test GET request to tickets list page."""
    response = test_client.get('/tickets/')
    assert response.status_code == 200

def test_list_tickets_unauthenticated(test_client):
    """Test tickets list page when user is not authenticated."""
    response = test_client.get('/tickets/', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login

def test_list_tickets_with_character_tickets(test_client, authenticated_user, db):
    """Test tickets list with character tickets."""
    # Create a test event
    event = Event(
        event_number='TICKET001',
        name='Test Event',
        event_type='mainline',
        description='A test event',
        early_booking_deadline=datetime.now() + timedelta(days=30),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location='Test Location',
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00
    )
    db.session.add(event)
    db.session.commit()
    
    # Create a test character for the user
    character = Character(
        user_id=authenticated_user.id,
        character_id=1,
        name='Test Character',
        status=CharacterStatus.ACTIVE.value
    )
    db.session.add(character)
    db.session.commit()
    
    # Create a ticket for the character
    ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        ticket_type=TicketType.ADULT.value,
        price_paid=50.00,
        assigned_by_id=authenticated_user.id,
        assigned_at=datetime.now()
    )
    db.session.add(ticket)
    db.session.commit()
    
    with test_client.session_transaction() as session:
        session['_user_id'] = authenticated_user.id
        session['_fresh'] = True
    
    response = test_client.get('/tickets/')
    assert response.status_code == 200

def test_list_tickets_with_assigned_tickets(test_client, authenticated_user, db):
    """Test tickets list with tickets assigned by user."""
    # Create a test event
    event = Event(
        event_number='TICKET002',
        name='Test Event',
        event_type='mainline',
        description='A test event',
        early_booking_deadline=datetime.now() + timedelta(days=30),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location='Test Location',
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00
    )
    db.session.add(event)
    db.session.commit()
    
    # Create a test character for another user
    other_user = User(
        email='other@example.com',
        first_name='Other',
        surname='User'
    )
    other_user.set_password('password123')
    db.session.add(other_user)
    db.session.commit()
    
    character = Character(
        user_id=other_user.id,
        character_id=2,
        name='Other Character',
        status=CharacterStatus.ACTIVE.value
    )
    db.session.add(character)
    db.session.commit()
    
    # Create a ticket assigned by the authenticated user
    ticket = EventTicket(
        event_id=event.id,
        character_id=character.id,
        ticket_type=TicketType.ADULT.value,
        price_paid=50.00,
        assigned_by_id=authenticated_user.id,
        assigned_at=datetime.now()
    )
    db.session.add(ticket)
    db.session.commit()
    
    with test_client.session_transaction() as session:
        session['_user_id'] = authenticated_user.id
        session['_fresh'] = True
    
    response = test_client.get('/tickets/')
    assert response.status_code == 200

def test_list_tickets_with_past_event(test_client, authenticated_user, db):
    """Test tickets list with past event tickets."""
    # Create a past event
    past_event = Event(
        event_number='PAST001',
        name='Past Event',
        event_type='mainline',
        description='A past event',
        early_booking_deadline=datetime.now() - timedelta(days=60),
        start_date=datetime.now() - timedelta(days=45),
        end_date=datetime.now() - timedelta(days=43),
        location='Past Location',
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00
    )
    db.session.add(past_event)
    db.session.commit()
    
    # Create a test character for the user
    character = Character(
        user_id=authenticated_user.id,
        character_id=3,
        name='Test Character',
        status=CharacterStatus.ACTIVE.value
    )
    db.session.add(character)
    db.session.commit()
    
    # Create a ticket for the past event
    ticket = EventTicket(
        event_id=past_event.id,
        character_id=character.id,
        ticket_type=TicketType.ADULT.value,
        price_paid=50.00,
        assigned_by_id=authenticated_user.id,
        assigned_at=datetime.now() - timedelta(days=50)
    )
    db.session.add(ticket)
    db.session.commit()
    
    with test_client.session_transaction() as session:
        session['_user_id'] = authenticated_user.id
        session['_fresh'] = True
    
    response = test_client.get('/tickets/')
    assert response.status_code == 200

def test_list_tickets_no_tickets(test_client, authenticated_user):
    """Test tickets list when user has no tickets."""
    with test_client.session_transaction() as session:
        session['_user_id'] = authenticated_user.id
        session['_fresh'] = True
    
    response = test_client.get('/tickets/')
    assert response.status_code == 200 
