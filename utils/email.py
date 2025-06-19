from flask import current_app
from flask_mail import Mail, Message
import os
from threading import Thread
from jinja2 import Environment, FileSystemLoader

mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None):
    """Send an email using the configured mail server."""
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # Send email asynchronously
    Thread(target=send_async_email, args=(app, msg)).start()

def render_email_template(template_name, **kwargs):
    """Render both HTML and text versions of an email template."""
    template_dir = os.path.join(current_app.static_folder, 'email_templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Render HTML template
    html_template = env.get_template(f'{template_name}.html')
    html_body = html_template.render(**kwargs)
    
    # Render text template
    text_template = env.get_template(f'{template_name}.txt')
    text_body = text_template.render(**kwargs)
    
    return text_body, html_body

def send_verification_email(user):
    """Send a verification email to the user."""
    token = user.generate_verification_token()
    verification_url = f"{current_app.config['BASE_URL']}/auth/verify/{token}"
    
    subject = "Orion Sphere LRP - Verify Your Email"
    text_body, html_body = render_email_template(
        'verification_email',
        user=user,
        verification_url=verification_url
    )
    
    send_email(subject, [user.email], text_body, html_body)

def send_email_change_verification(user, token, new_email):
    """Send a verification email for email address change."""
    verification_url = f"{current_app.config['BASE_URL']}/settings/change-email/{token}"
    
    subject = "Orion Sphere LRP - Confirm Email Change"
    text_body, html_body = render_email_template(
        'email_change_email',
        user=user,
        new_email=new_email,
        verification_url=verification_url
    )
    
    # Send to the new email address to verify it's valid
    send_email(subject, [new_email], text_body, html_body)

def send_password_reset_email(user):
    """Send a password reset email to the user."""
    token = user.generate_reset_token()
    reset_url = f"{current_app.config['BASE_URL']}/auth/reset-password/{token}"
    
    subject = "Orion Sphere LRP - Password Reset"
    text_body, html_body = render_email_template(
        'password_reset_email',
        user=user,
        reset_url=reset_url
    )
    
    send_email(subject, [user.email], text_body, html_body)

def send_notification_email(user, notification_type, **kwargs):
    """Send a notification email to the user based on their preferences."""
    if not user.should_notify(notification_type):
        return False
    
    # Map notification types to email templates and subjects
    notification_config = {
        'downtime_pack_enter': {
            'subject': 'Orion Sphere LRP - Downtime Pack Status Update',
            'template': 'notification_downtime_pack_enter'
        },
        'downtime_completed': {
            'subject': 'Orion Sphere LRP - Downtime Completed',
            'template': 'notification_downtime_completed'
        },
        'new_event': {
            'subject': 'Orion Sphere LRP - New Event Created',
            'template': 'notification_new_event'
        },
        'event_ticket_assigned': {
            'subject': 'Orion Sphere LRP - Event Ticket Assigned',
            'template': 'notification_event_ticket_assigned'
        },
        'event_details_updated': {
            'subject': 'Orion Sphere LRP - Event Details Updated',
            'template': 'notification_event_details_updated'
        },
        'wiki_published': {
            'subject': 'Orion Sphere LRP - Wiki Version Published',
            'template': 'notification_wiki_published'
        }
    }
    
    config = notification_config.get(notification_type)
    if not config:
        return False
    
    try:
        text_body, html_body = render_email_template(
            config['template'],
            user=user,
            **kwargs
        )
        
        send_email(config['subject'], [user.email], text_body, html_body)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send notification email: {str(e)}")
        return False

def send_downtime_pack_enter_notification(user, character, downtime_pack):
    """Send notification when a downtime pack is set to enter_downtime status."""
    return send_notification_email(
        user, 
        'downtime_pack_enter',
        character=character,
        downtime_pack=downtime_pack
    )

def send_downtime_completed_notification(user, downtime, character=None):
    """Send notification when a downtime is marked as completed."""
    return send_notification_email(
        user, 
        'downtime_completed',
        downtime=downtime,
        character=character
    )

def send_new_event_notification(user, event):
    """Send notification when a new event is created."""
    return send_notification_email(
        user, 
        'new_event',
        event=event
    )

def send_event_ticket_assigned_notification(user, event_ticket, event, character):
    """Send notification when an event ticket is assigned/purchased."""
    return send_notification_email(
        user, 
        'event_ticket_assigned',
        event_ticket=event_ticket,
        event=event,
        character=character
    )

def send_event_details_updated_notification(user, event, character):
    """Send notification when event details are updated."""
    return send_notification_email(
        user, 
        'event_details_updated',
        event=event,
        character=character
    )

def send_wiki_published_notification(user, changelog):
    """Send notification when a wiki changelog is published."""
    return send_notification_email(
        user, 
        'wiki_published',
        changelog=changelog
    )

def send_notification_to_all_users(notification_type, **kwargs):
    """Send a notification to all users who have enabled the specified notification type."""
    from models.user import User
    
    users = User.query.filter_by(**{f'notify_{notification_type}': True}).all()
    
    success_count = 0
    for user in users:
        if send_notification_email(user, notification_type, **kwargs):
            success_count += 1
    
    return success_count, len(users)

def send_downtime_pack_enter_notification_to_all(character, downtime_pack):
    """Send downtime pack enter notification to all users who have enabled it."""
    return send_notification_to_all_users(
        'downtime_pack_enter',
        character=character,
        downtime_pack=downtime_pack
    )

def send_downtime_completed_notification_to_all(downtime, character=None):
    """Send downtime completed notification to all users who have enabled it."""
    return send_notification_to_all_users(
        'downtime_completed',
        downtime=downtime,
        character=character
    )

def send_new_event_notification_to_all(event):
    """Send new event notification to all users who have enabled it."""
    return send_notification_to_all_users(
        'new_event',
        event=event
    )

def send_event_ticket_assigned_notification_to_user(user, event_ticket, event, character):
    """Send event ticket assigned notification to a specific user."""
    return send_event_ticket_assigned_notification(user, event_ticket, event, character)

def send_event_details_updated_notification_to_all(event, character):
    """Send event details updated notification to all users who have enabled it."""
    return send_notification_to_all_users(
        'event_details_updated',
        event=event,
        character=character
    )

def send_wiki_published_notification_to_all(changelog):
    """Send wiki published notification to all users who have enabled it."""
    return send_notification_to_all_users(
        'wiki_published',
        changelog=changelog
    ) 