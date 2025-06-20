import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models.tools.user import User

def test_settings_get(test_client, authenticated_user):
    """Test GET request to settings page."""
    response = test_client.get('/settings/')
    assert response.status_code == 200

def test_settings_update_profile(test_client, authenticated_user, db):
    """Test updating profile information."""
    response = test_client.post('/settings/', data={
        'form_type': 'profile',
        'first_name': 'Updated',
        'surname': 'Name',
        'pronouns_subject': 'they',
        'pronouns_object': 'them'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Check that user was updated by querying the database
    db.session.refresh(authenticated_user)
    assert authenticated_user.first_name == 'Updated'
    assert authenticated_user.surname == 'Name'
    assert authenticated_user.pronouns_subject == 'they'
    assert authenticated_user.pronouns_object == 'them'

def test_settings_update_notifications(test_client, authenticated_user, db):
    """Test updating notification preferences."""
    response = test_client.post('/settings/', data={
        'form_type': 'notifications',
        'notify_downtime_pack_enter': '1',
        'notify_downtime_completed': '0',
        'notify_new_event': '1',
        'notify_event_ticket_assigned': '0',
        'notify_event_details_updated': '1',
        'notify_wiki_published': '0'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Check that notification preferences were updated
    db.session.refresh(authenticated_user)
    assert authenticated_user.notify_downtime_pack_enter is True
    assert authenticated_user.notify_downtime_completed is False
    assert authenticated_user.notify_new_event is True
    assert authenticated_user.notify_event_ticket_assigned is False
    assert authenticated_user.notify_event_details_updated is True
    assert authenticated_user.notify_wiki_published is False

def test_change_email_get(test_client, authenticated_user):
    """Test GET request to change email page."""
    response = test_client.get('/settings/change-email')
    assert response.status_code == 200

def test_change_email_success(test_client, authenticated_user):
    """Test successful email change request."""
    with patch('routes.settings.send_email_change_verification') as mock_send_email:
        with patch.object(authenticated_user, 'request_email_change', return_value=(True, 'test_token_123')):
            with patch.object(authenticated_user, 'check_password', return_value=True):
                response = test_client.post('/settings/change-email', data={
                    'new_email': 'unique_new_email@example.com',
                    'password': 'password123'
                }, follow_redirects=True)
                
                assert response.status_code == 200
                mock_send_email.assert_called_once()

def test_change_email_missing_fields(test_client, authenticated_user):
    """Test email change with missing fields."""
    response = test_client.post('/settings/change-email', data={
        'new_email': 'newemail@example.com'
        # Missing password
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should show error message

def test_change_email_wrong_password(test_client, authenticated_user):
    """Test email change with wrong password."""
    response = test_client.post('/settings/change-email', data={
        'new_email': 'newemail@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should show error message

def test_change_email_invalid_email(test_client, authenticated_user):
    """Test email change with invalid email."""
    with patch.object(authenticated_user, 'request_email_change', return_value=(False, 'Invalid email format')):
        response = test_client.post('/settings/change-email', data={
            'new_email': 'invalid-email',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message

def test_change_email_duplicate_email(test_client, authenticated_user):
    """Test email change with duplicate email."""
    with patch.object(authenticated_user, 'request_email_change', return_value=(False, 'Email already registered')):
        response = test_client.post('/settings/change-email', data={
            'new_email': 'existing@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message

def test_change_email_send_failure(test_client, authenticated_user):
    """Test email change when sending verification email fails."""
    with patch.object(authenticated_user, 'request_email_change', return_value=(True, 'token123')):
        with patch('routes.settings.send_email_change_verification', side_effect=Exception('Email service down')):
            response = test_client.post('/settings/change-email', data={
                'new_email': 'newemail@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should show error message about email sending failure

def test_confirm_email_change_success(test_client, authenticated_user):
    """Test successful email change confirmation."""
    with patch.object(authenticated_user, 'confirm_email_change', return_value=(True, 'old@example.com')):
        response = test_client.get('/settings/change-email/valid_token', follow_redirects=True)
        assert response.status_code == 200

def test_confirm_email_change_invalid_token(test_client, authenticated_user):
    """Test email change confirmation with invalid token."""
    with patch.object(authenticated_user, 'confirm_email_change', return_value=(False, None)):
        response = test_client.get('/settings/change-email/invalid_token', follow_redirects=True)
        assert response.status_code == 200
        # Should show error message

def test_settings_unauthenticated(test_client):
    """Test settings page when user is not authenticated."""
    response = test_client.get('/settings/', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login

def test_change_email_unauthenticated(test_client):
    """Test change email page when user is not authenticated."""
    response = test_client.get('/settings/change-email', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login

def test_confirm_email_change_unauthenticated(test_client):
    """Test confirm email change when user is not authenticated."""
    response = test_client.get('/settings/change-email/token', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login 
