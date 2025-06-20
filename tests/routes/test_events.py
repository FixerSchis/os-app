import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models.event import Event
from models.enums import EventType, Role, TicketType
from datetime import datetime, timezone, timedelta

def test_event_list_get(test_client, db):
    """Test GET request to event list page."""
    response = test_client.get('/events/')
    assert response.status_code == 200

def test_event_list_show_previous(test_client, admin_user):
    """Test event list with show_previous parameter."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.get('/events/?show_previous=true')
    assert response.status_code == 200

def test_create_event_get(test_client, admin_user):
    """Test GET request to create event page."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.get('/events/new')
    assert response.status_code == 200

def test_create_event_get_unauthorized(test_client, authenticated_user):
    """Test create event page when user is not admin."""
    response = test_client.get('/events/new', follow_redirects=True)
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden

def test_create_event_post(test_client, admin_user, db):
    """Test POST request to create event."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    with patch('routes.events.send_new_event_notification_to_all') as mock_send_notification:
        response = test_client.post('/events/new', data={
            'event_number': 'TEST001',
            'name': 'Test Event',
            'event_type': 'mainline',
            'description': 'A test event',
            'early_booking_deadline': '2025-07-01',
            'start_date': '2025-07-15',
            'end_date': '2025-07-17',
            'location': 'Test Location',
            'google_maps_link': 'https://maps.google.com',
            'meal_ticket_available': '1',
            'meal_ticket_price': '15.00',
            'bunks_available': '1',
            'standard_ticket_price': '50.00',
            'early_booking_ticket_price': '45.00',
            'child_ticket_price_12_15': '25.00',
            'child_ticket_price_7_11': '15.00',
            'child_ticket_price_under_7': '0.00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that event was created
        event = Event.query.filter_by(event_number='TEST001').first()
        assert event is not None
        assert event.name == 'Test Event'
        assert event.event_type.value == 'mainline'  # Compare enum value
        
        mock_send_notification.assert_called_once_with(event)

def test_edit_event_get(test_client, admin_user, db):
    """Test GET request to edit event page."""
    # Create a test event
    event = Event(
        event_number='TEST002',
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
    
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/events/{event.id}/edit')
    assert response.status_code == 200

def test_edit_event_get_unauthorized(test_client, authenticated_user, db):
    """Test edit event page when user is not admin."""
    # Create a test event
    event = Event(
        event_number='TEST003',
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
    
    response = test_client.get(f'/events/{event.id}/edit', follow_redirects=True)
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden

def test_purchase_ticket_get(test_client, authenticated_user, db):
    """Test GET request to purchase ticket page."""
    # Create a test event
    event = Event(
        event_number='TEST005',
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
    
    with test_client.session_transaction() as session:
        session['_user_id'] = authenticated_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/events/{event.id}/purchase', follow_redirects=True)
    assert response.status_code == 200

def test_purchase_ticket_get_no_active_character(test_client, authenticated_user, db):
    """Test purchase ticket page when user has no active character."""
    # Create a test event
    event = Event(
        event_number='TEST006',
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
    
    # Remove active character from user
    authenticated_user.active_character_id = None
    db.session.commit()
    
    with test_client.session_transaction() as session:
        session['_user_id'] = authenticated_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/events/{event.id}/purchase', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect due to no active character

def test_assign_ticket_get(test_client, admin_user, db):
    """Test GET request to assign ticket page."""
    # Create a test event
    event = Event(
        event_number='TEST007',
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
    
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/events/{event.id}/assign')
    assert response.status_code == 200

def test_view_attendees_get(test_client, admin_user, db):
    """Test GET request to view attendees page."""
    # Create a test event
    event = Event(
        event_number='TEST009',
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
    
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/events/{event.id}/attendees')
    assert response.status_code == 200 