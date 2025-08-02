"""
Template helper functions for the permissions system.
"""

from flask import current_app
from flask_login import current_user


def has_permission(permission_name):
    """Check if the current user has a specific permission."""
    if not current_user.is_authenticated:
        return False
    return current_user.has_permission(permission_name)


def has_any_permission(permission_names):
    """Check if the current user has any of the specified permissions."""
    if not current_user.is_authenticated:
        return False
    return current_user.has_any_permission(permission_names)


def has_all_permissions(permission_names):
    """Check if the current user has all of the specified permissions."""
    if not current_user.is_authenticated:
        return False
    return current_user.has_all_permissions(permission_names)


# Legacy can_manage_* helper functions removed - use has_permission() directly in templates


def can_approve_character_backgrounds():
    """Check if user can approve character backgrounds."""
    return has_permission("character.background_approve")


def can_approve_group_backgrounds():
    """Check if user can approve group backgrounds."""
    return has_permission("group.background_approve")
