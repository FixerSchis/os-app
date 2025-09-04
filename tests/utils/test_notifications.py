from unittest.mock import Mock, patch

import pytest
from flask import g
from flask_login import current_user

from models.enums import CharacterStatus, DowntimeStatus, DowntimeTaskStatus
from models.event import Event
from models.tools.character import Character, CharacterBackground
from models.tools.character_inventory import ItemTransferRequest, ItemTransferStatus
from models.tools.group import GroupBackground
from utils.notifications import get_user_notifications, has_notifications


class TestNotifications:
    """Test cases for the notification system utilities."""

    def test_get_user_notifications_no_user(self, app):
        """Test that notifications return empty list when no user is authenticated."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = False

            with patch("utils.notifications.current_user", mock_user):
                notifications = get_user_notifications()

                assert notifications == []

    def test_get_user_notifications_no_active_character(self, app):
        """Test that notifications return empty list when user has no active character."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = False  # No admin permissions

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert notifications == []

    def test_get_user_notifications_character_with_group(self, app):
        """Test that notifications return empty list when active character has a group."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = False  # No admin permissions

            # Mock character with group
            mock_character = Mock()
            mock_character.group_id = 1
            mock_character.name = "Test Character"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert notifications == []

    def test_get_user_notifications_character_needs_group(self, app):
        """Test that notification is returned when active character needs a group."""
        with app.test_request_context():
            # Create a proper mock user
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = False  # No admin permissions

            # Mock character without group
            mock_character = Mock()
            mock_character.group_id = None
            mock_character.name = "Test Character"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "character_needs_group"
                    assert notification["title"] == "Character Needs Group"
                    assert (
                        notification["message"]
                        == 'Your character "Test Character" is not in a group'
                    )
                    assert notification["url"] == "/groups/"
                    assert notification["priority"] == "high"

    def test_get_user_notifications_character_with_empty_group_id(self, app):
        """Test that notification is returned when character has empty group_id."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = False  # No admin permissions

            # Mock character with empty group_id (falsy but not None)
            mock_character = Mock()
            mock_character.group_id = 0  # Empty group_id
            mock_character.name = "Test Character"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "character_needs_group"

    def test_has_notifications_no_notifications(self):
        """Test that has_notifications returns False when no notifications exist."""
        with patch("utils.notifications.get_user_notifications") as mock_get_notifications:
            mock_get_notifications.return_value = []

            result = has_notifications()

            assert result is False

    def test_has_notifications_with_notifications(self):
        """Test that has_notifications returns True when notifications exist."""
        with patch("utils.notifications.get_user_notifications") as mock_get_notifications:
            mock_notification = {
                "type": "character_needs_group",
                "title": "Test Notification",
                "message": "Test message",
                "url": "/test",
                "priority": "high",
            }
            mock_get_notifications.return_value = [mock_notification]

            result = has_notifications()

            assert result is True

    def test_notification_structure(self, app):
        """Test that notification objects have the correct structure."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = False  # No admin permissions

            mock_character = Mock()
            mock_character.group_id = None
            mock_character.name = "Test Character"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]

                    # Check all required fields are present
                    required_fields = ["type", "title", "message", "url", "priority"]
                    for field in required_fields:
                        assert field in notification
                        assert notification[field] is not None
                        assert notification[field] != ""

    def test_multiple_notifications(self):
        """Test that multiple notifications can be returned (for future expansion)."""
        # This test verifies that the system can handle multiple notification types
        # by directly testing the has_notifications function with multiple notifications
        mock_notifications = [
            {
                "type": "character_needs_group",
                "title": "Character Needs Group",
                "message": 'Your character "Test Character" is not in a group',
                "url": "/groups/",
                "priority": "high",
            },
            {
                "type": "future_notification",
                "title": "Future Notification",
                "message": "This is a future notification type",
                "url": "/future",
                "priority": "medium",
            },
        ]

        with patch("utils.notifications.get_user_notifications") as mock_get_notifications:
            mock_get_notifications.return_value = mock_notifications

            # Test that has_notifications works with multiple notifications
            result = has_notifications()
            assert result is True

            # Test that the mocked function returns the expected notifications
            notifications = mock_get_notifications.return_value
            assert len(notifications) == 2
            assert notifications[0]["type"] == "character_needs_group"
            assert notifications[1]["type"] == "future_notification"

    def test_character_name_escaping(self, app):
        """Test that character names with special characters are handled properly."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = False  # No admin permissions

            mock_character = Mock()
            mock_character.group_id = None
            mock_character.name = "Character with 'quotes' & symbols"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert "Character with 'quotes' & symbols" in notification["message"]

    def test_priority_levels(self, app):
        """Test that different priority levels are handled correctly."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = False  # No admin permissions

            mock_character = Mock()
            mock_character.group_id = None
            mock_character.name = "Test Character"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["priority"] == "high"

                    # Test that priority is one of the expected values
                    valid_priorities = ["low", "medium", "high"]
                    assert notification["priority"] in valid_priorities

    def test_group_backgrounds_review_notification(self, app):
        """Test that group backgrounds review notification is shown for users with permission."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None  # No active character
            mock_user.has_permission.return_value = True

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 3
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "group_backgrounds_review"
                    assert notification["title"] == "Group Backgrounds Need Review"
                    assert notification["message"] == "3 group backgrounds need review"
                    assert notification["url"] == "/groups/backgrounds/"
                    assert notification["priority"] == "medium"

    def test_character_backgrounds_review_notification(self, app):
        """Test that character backgrounds review notification is shown for users with permission."""  # noqa: E501
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None  # No active character
            mock_user.has_permission.return_value = True

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 1
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "character_backgrounds_review"
                    assert notification["title"] == "Character Backgrounds Need Review"
                    assert notification["message"] == "1 character background needs review"
                    assert notification["url"] == "/tools/character-backgrounds/"
                    assert notification["priority"] == "medium"

    def test_item_transfer_requests_notification(self, app):
        """Test that item transfer requests notification is shown for users with permission."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None  # No active character
            mock_user.has_permission.return_value = True

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 5
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "item_transfer_requests"
                    assert notification["title"] == "Item Transfer Requests"
                    assert notification["message"] == "5 item transfer requests need approval"
                    assert notification["url"] == "/tools/items/"
                    assert notification["priority"] == "medium"

    def test_no_admin_notifications_without_permission(self, app):
        """Test that admin notifications are not shown without proper permissions."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None  # No active character
            mock_user.has_permission.return_value = False  # No permissions

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return counts (but user has no permissions)
                    mock_group_bg.query.filter_by.return_value.count.return_value = 1
                    mock_char_bg.query.filter_by.return_value.count.return_value = 1
                    mock_transfer.query.filter_by.return_value.count.return_value = 1
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 0

    def test_multiple_admin_notifications(self, app):
        """Test that multiple admin notifications can be shown simultaneously."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None  # No active character
            mock_user.has_permission.return_value = True  # Has all permissions

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return counts
                    mock_group_bg.query.filter_by.return_value.count.return_value = 2
                    mock_char_bg.query.filter_by.return_value.count.return_value = 1
                    mock_transfer.query.filter_by.return_value.count.return_value = 3
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 3

                    # Check that all three notification types are present
                    notification_types = [n["type"] for n in notifications]
                    assert "group_backgrounds_review" in notification_types
                    assert "character_backgrounds_review" in notification_types
                    assert "item_transfer_requests" in notification_types

    def test_admin_notifications_with_user_notification(self, app):
        """Test that admin notifications work alongside user notifications."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.has_permission.return_value = True

            # User has active character without group
            mock_character = Mock()
            mock_character.group_id = None
            mock_character.name = "Test Character"
            mock_user.get_active_character.return_value = mock_character

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 1
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 2

                    # Check that both user and admin notifications are present
                    notification_types = [n["type"] for n in notifications]
                    assert "character_needs_group" in notification_types
                    assert "group_backgrounds_review" in notification_types

    def test_downtime_packs_need_entering_notification(self, app):
        """Test notification for packs that need entering."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0

                    # Mock active downtime period
                    mock_active_period = Mock()
                    mock_active_period.id = 1
                    mock_period.query.filter_by.return_value.first.return_value = mock_active_period

                    # Mock packs that need entering (only ENTER_PACK status returns 3, others return 0)  # noqa: E501
                    def mock_filter_by(**kwargs):
                        mock_query = Mock()
                        if kwargs.get("status") == DowntimeTaskStatus.ENTER_PACK:
                            mock_query.count.return_value = 3
                        else:
                            mock_query.count.return_value = 0
                        return mock_query

                    mock_pack.query.filter_by.side_effect = mock_filter_by

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "downtime_packs_need_entering"
                    assert notification["title"] == "Downtime Packs Need Entering"
                    assert notification["message"] == "3 packs need entering"
                    assert notification["url"] == "/downtime/"
                    assert notification["priority"] == "high"

    def test_downtime_users_need_entering_notification(self, app):
        """Test notification for users that need to enter downtime."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0

                    # Mock active downtime period
                    mock_active_period = Mock()
                    mock_active_period.id = 1
                    mock_period.query.filter_by.return_value.first.return_value = mock_active_period

                    # Mock packs that need entering (0) and users that need downtime (2)
                    mock_pack.query.filter_by.side_effect = lambda **kwargs: Mock(
                        count=lambda: (
                            2 if kwargs.get("status") == DowntimeTaskStatus.ENTER_DOWNTIME else 0
                        )
                    )

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "downtime_users_need_entering"
                    assert notification["title"] == "Users Need to Enter Downtime"
                    assert notification["message"] == "2 users need to enter downtime"
                    assert notification["url"] == "/downtime/"
                    assert notification["priority"] == "medium"

    def test_downtime_packs_need_review_notification(self, app):
        """Test notification for packs that need review."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0

                    # Mock active downtime period
                    mock_active_period = Mock()
                    mock_active_period.id = 1
                    mock_period.query.filter_by.return_value.first.return_value = mock_active_period

                    # Mock packs that need review
                    mock_pack.query.filter_by.side_effect = lambda **kwargs: Mock(
                        count=lambda: (
                            1 if kwargs.get("status") == DowntimeTaskStatus.MANUAL_REVIEW else 0
                        )
                    )

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "downtime_packs_need_review"
                    assert notification["title"] == "Downtime Packs Need Review"
                    assert notification["message"] == "1 pack needs review"
                    assert notification["url"] == "/downtime/"
                    assert notification["priority"] == "medium"

    def test_downtime_ready_to_process_notification(self, app):
        """Test notification when downtime is ready to process."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0

                    # Mock active downtime period
                    mock_active_period = Mock()
                    mock_active_period.id = 1
                    mock_period.query.filter_by.return_value.first.return_value = mock_active_period

                    # Mock all packs completed (total=5, completed=5)
                    def mock_filter_by(**kwargs):
                        mock_query = Mock()
                        if kwargs.get("status") == DowntimeTaskStatus.COMPLETED:
                            mock_query.count.return_value = 5
                        elif "period_id" in kwargs and "status" not in kwargs:
                            # This is the total packs query
                            mock_query.count.return_value = 5
                        else:
                            mock_query.count.return_value = 0
                        return mock_query

                    mock_pack.query.filter_by.side_effect = mock_filter_by

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "downtime_ready_to_process"
                    assert notification["title"] == "Downtime Ready to Process"
                    assert (
                        notification["message"]
                        == "All downtime packs are completed and ready to process"
                    )
                    assert notification["url"] == "/downtime/"
                    assert notification["priority"] == "high"

    def test_downtime_user_needs_entering_notification(self, app):
        """Test notification for regular users who need to enter downtime."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None

            # Mock has_permission to return False for downtime.manage but True for others
            def mock_has_permission(permission):
                return permission != "downtime.manage"

            mock_user.has_permission.side_effect = mock_has_permission
            mock_user.id = 123

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0

                    # Mock active downtime period
                    mock_active_period = Mock()
                    mock_active_period.id = 1
                    mock_period.query.filter_by.return_value.first.return_value = mock_active_period

                    # Mock user has characters that need downtime
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 2

                    notifications = get_user_notifications()

                    assert notifications is not None
                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "downtime_user_needs_entering"
                    assert notification["title"] == "Enter Downtime"
                    assert (
                        notification["message"]
                        == "You have 2 characters that need to enter downtime"
                    )
                    assert notification["url"] == "/downtime/"
                    assert notification["priority"] == "high"

    def test_no_downtime_notifications_without_active_period(self, app):
        """Test that no downtime notifications are shown when there's no active period."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0

                    # Mock no active downtime period
                    mock_period.query.filter_by.return_value.first.return_value = None
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 0

    def test_events_available_for_downtime_notification(self, app):
        """Test notification for events available for downtime."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = (
                        None  # No active period
                    )
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    # Mock the available events count
                    mock_get_events.return_value = 2

                    notifications = get_user_notifications()

                    assert len(notifications) == 1
                    notification = notifications[0]
                    assert notification["type"] == "events_available_for_downtime"
                    assert notification["title"] == "Events Available for Downtime"
                    assert notification["message"] == "2 events are available to start downtime"
                    assert notification["url"] == "/downtime/"
                    assert notification["priority"] == "medium"

    def test_no_events_available_for_downtime_notification(self, app):
        """Test that no notification is shown when no events are available for downtime."""
        with app.test_request_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.get_active_character.return_value = None
            mock_user.has_permission.return_value = True  # Has downtime.manage permission

            with patch("utils.notifications.current_user", mock_user):
                with (
                    patch("utils.notifications.GroupBackground") as mock_group_bg,
                    patch("utils.notifications.CharacterBackground") as mock_char_bg,
                    patch("utils.notifications.ItemTransferRequest") as mock_transfer,
                    patch("utils.notifications.DowntimePeriod") as mock_period,
                    patch("utils.notifications.DowntimePack") as mock_pack,  # noqa: F841
                    patch("utils.notifications.Character") as mock_character,  # noqa: F841
                    patch(
                        "utils.notifications._get_available_events_count"
                    ) as mock_get_events,  # noqa: F841
                ):

                    # Mock all queries to return 0 for other models
                    mock_group_bg.query.filter_by.return_value.count.return_value = 0
                    mock_char_bg.query.filter_by.return_value.count.return_value = 0
                    mock_transfer.query.filter_by.return_value.count.return_value = 0
                    mock_period.query.filter_by.return_value.first.return_value = (
                        None  # No active period
                    )
                    mock_pack.query.join.return_value.filter.return_value.count.return_value = 0

                    # Mock no available events
                    mock_get_events.return_value = 0

                    notifications = get_user_notifications()

                    assert len(notifications) == 0
