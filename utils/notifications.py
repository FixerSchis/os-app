from flask_login import current_user

from models.enums import CharacterStatus, DowntimeStatus, DowntimeTaskStatus
from models.event import Event
from models.extensions import db
from models.tools.character import Character, CharacterBackground
from models.tools.character_inventory import ItemTransferRequest, ItemTransferStatus
from models.tools.downtime import DowntimePack, DowntimePeriod
from models.tools.group import GroupBackground


def _get_available_events_count():
    """Get count of events that are available for downtime."""
    from datetime import datetime

    return Event.query.filter(
        Event.end_date <= datetime.now(),
        Event.event_type == "mainline",
        ~Event.id.in_(
            db.session.query(DowntimePeriod.event_id).filter(DowntimePeriod.event_id.isnot(None))
        ),
    ).count()


def get_user_notifications():
    """Get all notifications for the current user."""
    if not current_user.is_authenticated:
        return []

    notifications = []

    # Check if user has an active character without a group
    active_character = current_user.get_active_character()
    if active_character and (active_character.group_id is None or active_character.group_id == 0):
        notifications.append(
            {
                "type": "character_needs_group",
                "title": "Character Needs Group",
                "message": f'Your character "{active_character.name}" is not in a group',
                "url": "/groups/",
                "priority": "high",
            }
        )

    # Admin notifications - only show if user has appropriate permissions

    # Group backgrounds needing review
    if current_user.has_permission("group.background_approve"):
        group_backgrounds_count = GroupBackground.query.filter_by(needs_review=True).count()
        if group_backgrounds_count > 0:
            notifications.append(
                {
                    "type": "group_backgrounds_review",
                    "title": "Group Backgrounds Need Review",
                    "message": (
                        f"{group_backgrounds_count} group background"
                        f'{"s" if group_backgrounds_count != 1 else ""} '
                        f'need{"s" if group_backgrounds_count == 1 else ""} review'
                    ),
                    "url": "/groups/backgrounds/",
                    "priority": "medium",
                }
            )

    # Character backgrounds needing review
    if current_user.has_permission("character.background_approve"):
        character_backgrounds_count = CharacterBackground.query.filter_by(needs_review=True).count()
        if character_backgrounds_count > 0:
            notifications.append(
                {
                    "type": "character_backgrounds_review",
                    "title": "Character Backgrounds Need Review",
                    "message": (
                        f"{character_backgrounds_count} character background"
                        f'{"s" if character_backgrounds_count != 1 else ""} '
                        f'need{"s" if character_backgrounds_count == 1 else ""} review'
                    ),
                    "url": "/tools/character-backgrounds/",
                    "priority": "medium",
                }
            )

    # Item transfer requests needing approval
    if current_user.has_permission("character.edit_all"):
        transfer_requests_count = ItemTransferRequest.query.filter_by(
            status=ItemTransferStatus.PENDING
        ).count()
        if transfer_requests_count > 0:
            notifications.append(
                {
                    "type": "item_transfer_requests",
                    "title": "Item Transfer Requests",
                    "message": (
                        f"{transfer_requests_count} item transfer request"
                        f'{"s" if transfer_requests_count != 1 else ""} '
                        f'need{"s" if transfer_requests_count == 1 else ""} approval'
                    ),
                    "url": "/tools/items/",
                    "priority": "medium",
                }
            )

    # Downtime notifications for admin users
    if current_user.has_permission("downtime.manage"):
        # Check if there's an active downtime period
        active_period = DowntimePeriod.query.filter_by(status=DowntimeStatus.PENDING).first()

        # If no active downtime period, check for events available for downtime
        if not active_period:
            available_events_count = _get_available_events_count()

            if available_events_count > 0:
                notifications.append(
                    {
                        "type": "events_available_for_downtime",
                        "title": "Events Available for Downtime",
                        "message": (
                            f"{available_events_count} event"
                            f'{"s" if available_events_count != 1 else ""} '
                            f'{"are" if available_events_count != 1 else "is"} '
                            f"available to start downtime"
                        ),
                        "url": "/downtime/",
                        "priority": "medium",
                    }
                )

        if active_period:
            # Packs that need entering
            packs_need_entering = DowntimePack.query.filter_by(
                period_id=active_period.id, status=DowntimeTaskStatus.ENTER_PACK
            ).count()

            if packs_need_entering > 0:
                notifications.append(
                    {
                        "type": "downtime_packs_need_entering",
                        "title": "Downtime Packs Need Entering",
                        "message": (
                            f"{packs_need_entering} pack"
                            f'{"s" if packs_need_entering != 1 else ""} '
                            f'need{"s" if packs_need_entering == 1 else ""} entering'
                        ),
                        "url": "/downtime/",
                        "priority": "high",
                    }
                )

            # Users need to enter downtime
            users_need_downtime = DowntimePack.query.filter_by(
                period_id=active_period.id, status=DowntimeTaskStatus.ENTER_DOWNTIME
            ).count()

            if users_need_downtime > 0:
                notifications.append(
                    {
                        "type": "downtime_users_need_entering",
                        "title": "Users Need to Enter Downtime",
                        "message": (
                            f"{users_need_downtime} user"
                            f'{"s" if users_need_downtime != 1 else ""} '
                            f'need{"s" if users_need_downtime == 1 else ""} to enter downtime'
                        ),
                        "url": "/downtime/",
                        "priority": "medium",
                    }
                )

            # Packs need review
            packs_need_review = DowntimePack.query.filter_by(
                period_id=active_period.id, status=DowntimeTaskStatus.MANUAL_REVIEW
            ).count()

            if packs_need_review > 0:
                notifications.append(
                    {
                        "type": "downtime_packs_need_review",
                        "title": "Downtime Packs Need Review",
                        "message": (
                            f"{packs_need_review} pack"
                            f'{"s" if packs_need_review != 1 else ""} '
                            f'need{"s" if packs_need_review == 1 else ""} review'
                        ),
                        "url": "/downtime/",
                        "priority": "medium",
                    }
                )

            # Check if downtime is ready to process (all packs completed)
            total_packs = DowntimePack.query.filter_by(period_id=active_period.id).count()
            completed_packs = DowntimePack.query.filter_by(
                period_id=active_period.id, status=DowntimeTaskStatus.COMPLETED
            ).count()

            if total_packs > 0 and completed_packs == total_packs:
                notifications.append(
                    {
                        "type": "downtime_ready_to_process",
                        "title": "Downtime Ready to Process",
                        "message": "All downtime packs are completed and ready to process",
                        "url": "/downtime/",
                        "priority": "high",
                    }
                )

    # Downtime notifications for regular users
    else:
        # Check if user has characters that need to enter downtime
        active_period = DowntimePeriod.query.filter_by(status=DowntimeStatus.PENDING).first()

        if active_period:
            user_downtime_packs = (
                DowntimePack.query.join(Character)
                .filter(
                    DowntimePack.period_id == active_period.id,
                    DowntimePack.status == DowntimeTaskStatus.ENTER_DOWNTIME,
                    Character.user_id == current_user.id,
                )
                .count()
            )

            if user_downtime_packs > 0:
                notifications.append(
                    {
                        "type": "downtime_user_needs_entering",
                        "title": "Enter Downtime",
                        "message": (
                            f"You have {user_downtime_packs} character"
                            f'{"s" if user_downtime_packs != 1 else ""} that '
                            f'need{"s" if user_downtime_packs == 1 else ""} to enter downtime'
                        ),
                        "url": "/downtime/",
                        "priority": "high",
                    }
                )

    return notifications


def has_notifications():
    """Check if the current user has any notifications."""
    return len(get_user_notifications()) > 0
