# Notification System

This document describes the notification system implemented for Orion Sphere LRP.

## Overview

The notification system allows users to configure email notifications for various events in the game. Users can enable or disable specific notification types through their account settings.

## Notification Types

The following notification types are available:

1. **Downtime Pack Enter** (`notify_downtime_pack_enter`)
   - Triggered when a character's downtime pack is set to `enter_downtime` status
   - Sent to the character's owner

2. **Downtime Completed** (`notify_downtime_completed`)
   - Triggered when a downtime period is marked as completed
   - Sent to users who had packs in that downtime

3. **New Event** (`notify_new_event`)
   - Triggered when a new event is created
   - Sent to all users who have enabled this notification

4. **Event Ticket Assigned** (`notify_event_ticket_assigned`)
   - Triggered when an event ticket is assigned or purchased for a character
   - Sent to the character's owner

5. **Event Details Updated** (`notify_event_details_updated`)
   - Triggered when event details are updated
   - Sent to users who have tickets for that event

6. **Wiki Published** (`notify_wiki_published`)
   - Triggered when a new wiki version is published
   - Sent to all users who have enabled this notification

## Database Schema

The notification preferences are stored in the `User` table with the following columns:

```sql
notify_downtime_pack_enter BOOLEAN DEFAULT 1
notify_downtime_completed BOOLEAN DEFAULT 1
notify_new_event BOOLEAN DEFAULT 1
notify_event_ticket_assigned BOOLEAN DEFAULT 1
notify_event_details_updated BOOLEAN DEFAULT 1
notify_wiki_published BOOLEAN DEFAULT 1
```

## User Interface

Users can manage their notification preferences through the Settings page (`/settings`). The notification settings are displayed as checkboxes in a dedicated section.

## Email Templates

Each notification type has corresponding HTML and text email templates located in `static/email_templates/`:

- `notification_downtime_pack_enter.html/.txt`
- `notification_downtime_completed.html/.txt`
- `notification_new_event.html/.txt`
- `notification_event_ticket_assigned.html/.txt`
- `notification_event_details_updated.html/.txt`
- `notification_wiki_published.html/.txt`

## Implementation

### User Model Methods

The `User` model includes the following methods for notification management:

- `should_notify(notification_type)`: Check if user should receive a specific notification
- `update_notification_preferences(preferences)`: Update notification preferences from a dictionary

### Email Utility Functions

The `utils/email.py` module provides functions for sending notifications:

- `send_notification_email(user, notification_type, **kwargs)`: Send notification to a specific user
- `send_notification_to_all_users(notification_type, **kwargs)`: Send notification to all users who have enabled it
- Specific functions for each notification type (e.g., `send_downtime_pack_enter_notification`)

### Integration Points

To integrate notifications into existing functionality, add calls to the appropriate notification functions:

#### Downtime Pack Status Changes
```python
from utils.email import send_downtime_pack_enter_notification

# When setting pack status to enter_downtime
if pack.status == DowntimeTaskStatus.ENTER_DOWNTIME:
    send_downtime_pack_enter_notification(pack.character.user, pack)
```

#### Downtime Completion
```python
from utils.email import send_downtime_completed_notification_to_all

# When marking downtime as completed
send_downtime_completed_notification_to_all(downtime)
```

#### New Event Creation
```python
from utils.email import send_new_event_notification_to_all

# When creating a new event
send_new_event_notification_to_all(event)
```

#### Event Ticket Assignment
```python
from utils.email import send_event_ticket_assigned_notification_to_user

# When assigning a ticket
send_event_ticket_assigned_notification_to_user(user, event_ticket, event, character)
```

#### Event Details Update
```python
from utils.email import send_event_details_updated_notification_to_all

# When updating event details
send_event_details_updated_notification_to_all(event, character)
```

#### Wiki Publication
```python
from utils.email import send_wiki_published_notification_to_all

# When publishing a wiki version
send_wiki_published_notification_to_all(wiki_version)
```

## Database Migration

To add the notification columns to an existing database, run the migration script:

```bash
python add_notification_columns.py
```

This script will:
1. Check if the notification columns already exist
2. Add any missing columns with appropriate default values
3. Verify the changes were applied successfully

## Configuration

The notification system uses the existing email configuration from the Flask app. Ensure the following settings are configured:

- `MAIL_SERVER`: SMTP server address
- `MAIL_PORT`: SMTP server port
- `MAIL_USE_TLS`: Whether to use TLS
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password
- `BASE_URL`: Base URL for generating links in emails

## Testing

To test the notification system:

1. Update notification preferences in the settings page
2. Trigger the relevant events (create events, update downtime, etc.)
3. Check that emails are sent to the appropriate users
4. Verify email content and links work correctly

## Troubleshooting

### Common Issues

1. **Emails not being sent**: Check email configuration and SMTP settings
2. **Template errors**: Verify email templates exist and are properly formatted
3. **Database errors**: Ensure notification columns exist in the User table
4. **Permission issues**: Check that the application has write access to the email template directory

### Debugging

Enable debug logging to see notification system activity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

The notification system logs errors when email sending fails, which can help identify issues. 