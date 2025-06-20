import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from utils.email import (
    send_email,
    render_email_template,
    send_verification_email,
    send_password_reset_email,
    send_notification_email
)

@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['BASE_URL'] = 'https://example.com'
    app.config['static_folder'] = '/static'
    return app

@patch('utils.email.Thread')
@patch('utils.email.Message')
def test_send_email(mock_message, mock_thread, app):
    """Test send_email function."""
    with app.app_context():
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Test sending email
        send_email("Test Subject", ["test@example.com"], "Test body", "<p>Test HTML</p>")
        
        # Verify Message was created correctly
        mock_message.assert_called_once_with("Test Subject", recipients=["test@example.com"])
        assert mock_msg.body == "Test body"
        assert mock_msg.html == "<p>Test HTML</p>"
        
        # Verify thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

@patch('utils.email.FileSystemLoader')
@patch('utils.email.Environment')
def test_render_email_template(mock_env, mock_loader, app):
    """Test render_email_template function."""
    with app.app_context():
        mock_env_instance = MagicMock()
        mock_env.return_value = mock_env_instance
        
        mock_html_template = MagicMock()
        mock_text_template = MagicMock()
        mock_html_template.render.return_value = "<p>HTML content</p>"
        mock_text_template.render.return_value = "Text content"
        
        mock_env_instance.get_template.side_effect = [mock_html_template, mock_text_template]
        
        # Test rendering template
        text_body, html_body = render_email_template(
            'test_template',
            user={'name': 'Test User'},
            url='https://example.com'
        )
        
        # Verify environment was created correctly
        mock_env.assert_called_once()
        # Check that FileSystemLoader was called with a path containing email_templates
        mock_loader.assert_called_once()
        assert 'email_templates' in mock_loader.call_args[0][0]
        
        # Verify templates were rendered
        mock_html_template.render.assert_called_once_with(
            user={'name': 'Test User'},
            url='https://example.com'
        )
        mock_text_template.render.assert_called_once_with(
            user={'name': 'Test User'},
            url='https://example.com'
        )
        
        assert text_body == "Text content"
        assert html_body == "<p>HTML content</p>"

@patch('utils.email.send_email')
@patch('utils.email.render_email_template')
def test_send_verification_email(mock_render, mock_send, app):
    """Test send_verification_email function."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.generate_verification_token.return_value = "test_token"
        mock_user.email = "test@example.com"
        
        mock_render.return_value = ("Text body", "<p>HTML body</p>")
        
        # Test sending verification email
        send_verification_email(mock_user)
        
        # Verify token was generated
        mock_user.generate_verification_token.assert_called_once()
        
        # Verify template was rendered
        mock_render.assert_called_once_with(
            'verification_email',
            user=mock_user,
            verification_url='https://example.com/auth/verify/test_token'
        )
        
        # Verify email was sent
        mock_send.assert_called_once_with(
            "Orion Sphere LRP - Verify Your Email",
            ["test@example.com"],
            "Text body",
            "<p>HTML body</p>"
        )

@patch('utils.email.send_email')
@patch('utils.email.render_email_template')
def test_send_password_reset_email(mock_render, mock_send, app):
    """Test send_password_reset_email function."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.generate_reset_token.return_value = "reset_token"
        mock_user.email = "test@example.com"
        
        mock_render.return_value = ("Text body", "<p>HTML body</p>")
        
        # Test sending password reset email
        send_password_reset_email(mock_user)
        
        # Verify token was generated
        mock_user.generate_reset_token.assert_called_once()
        
        # Verify template was rendered
        mock_render.assert_called_once_with(
            'password_reset_email',
            user=mock_user,
            reset_url='https://example.com/auth/reset-password/reset_token'
        )
        
        # Verify email was sent
        mock_send.assert_called_once_with(
            "Orion Sphere LRP - Password Reset",
            ["test@example.com"],
            "Text body",
            "<p>HTML body</p>"
        )

@patch('utils.email.send_email')
@patch('utils.email.render_email_template')
def test_send_notification_email_success(mock_render, mock_send, app):
    """Test send_notification_email function with successful notification."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.should_notify.return_value = True
        mock_user.email = "test@example.com"
        
        mock_render.return_value = ("Text body", "<p>HTML body</p>")
        
        # Test sending notification email
        result = send_notification_email(mock_user, 'downtime_completed', downtime={'id': 1})
        
        # Verify user notification preference was checked
        mock_user.should_notify.assert_called_once_with('downtime_completed')
        
        # Verify template was rendered
        mock_render.assert_called_once_with(
            'notification_downtime_completed',
            user=mock_user,
            downtime={'id': 1}
        )
        
        # Verify email was sent
        mock_send.assert_called_once_with(
            "Orion Sphere LRP - Downtime Completed",
            ["test@example.com"],
            "Text body",
            "<p>HTML body</p>"
        )
        
        assert result is True

def test_send_notification_email_user_disabled(app):
    """Test send_notification_email function when user has disabled notifications."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.should_notify.return_value = False
        
        # Test sending notification email when disabled
        result = send_notification_email(mock_user, 'downtime_completed')
        
        # Verify user notification preference was checked
        mock_user.should_notify.assert_called_once_with('downtime_completed')
        
        # Should return False when notifications are disabled
        assert result is False

@patch('utils.email.send_email')
@patch('utils.email.render_email_template')
def test_send_notification_email_invalid_type(mock_render, mock_send, app):
    """Test send_notification_email function with invalid notification type."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.should_notify.return_value = True
        
        # Test sending notification email with invalid type
        result = send_notification_email(mock_user, 'invalid_type')
        
        # Should return False for invalid notification types
        assert result is False
        
        # Verify no email was sent
        mock_send.assert_not_called()
        mock_render.assert_not_called()

@patch('utils.email.send_email')
@patch('utils.email.render_email_template')
def test_send_notification_email_template_error(mock_render, mock_send, app):
    """Test send_notification_email function when template rendering fails."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.should_notify.return_value = True
        mock_user.email = "test@example.com"
        
        mock_render.side_effect = Exception("Template error")
        
        # Test sending notification email when template fails
        result = send_notification_email(mock_user, 'downtime_completed')
        
        # Should return False when template rendering fails
        assert result is False 
