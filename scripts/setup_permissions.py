#!/usr/bin/env python3
"""
Script to set up the default permissions and roles for the new granular permissions system.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# flake8: noqa: E402
from app import create_app
from models.database.permissions import Permission, Role
from models.extensions import db


def create_default_permissions():
    """Create all the default permissions."""
    permissions_data = [
        # User Management Permissions
        ("user.view", "View user list", "user"),
        ("user.edit", "Edit user details", "user"),
        ("user.roles", "Manage user roles", "user"),
        ("owner.promote", "Promote users to owner", "owner"),
        # Character Management Permissions
        ("character.view_all", "View all characters", "character"),
        ("character.edit_all", "Edit any character", "character"),
        ("character.background_approve", "Approve character backgrounds", "character"),
        ("character.refund", "Refund character skills from active characters", "character"),
        # Banking Permissions
        ("banking.view_all", "View all bank accounts", "banking"),
        ("banking.manage", "Manage banking operations", "banking"),
        # Event Management Permissions
        ("event.create", "Create events", "event"),
        ("event.edit", "Edit events", "event"),
        ("event.delete", "Delete events", "event"),
        ("event.assign_tickets", "Assign event tickets", "event"),
        ("event.manage_attendees", "Manage event attendees", "event"),
        # Database Management Permissions
        ("database.backup", "Create database backups", "database"),
        ("database.restore", "Restore database backups", "database"),
        # Rules Database Permissions
        ("rules.conditions", "Manage conditions", "rules"),
        ("rules.skills", "Manage skills", "rules"),
        ("rules.species", "Manage species", "rules"),
        ("rules.cybernetics", "Manage cybernetics", "rules"),
        ("rules.exotic_substances", "Manage exotic substances", "rules"),
        ("rules.items", "Manage items", "rules"),
        ("rules.medicaments", "Manage medicaments", "rules"),
        ("rules.mods", "Manage mods", "rules"),
        ("rules.item_types", "Manage item types", "rules"),
        ("rules.item_blueprints", "Manage item blueprints", "rules"),
        ("rules.global_settings", "Manage global settings", "rules"),
        ("rules.group_types", "Manage group types", "rules"),
        ("rules.factions", "Manage factions", "rules"),
        # Research Permissions
        ("research.create", "Create research projects", "research"),
        ("research.edit", "Edit research projects", "research"),
        ("research.delete", "Delete research projects", "research"),
        ("research.assign", "Assign research projects", "research"),
        # Wiki Permissions
        ("wiki.create", "Create wiki pages", "wiki"),
        ("wiki.edit", "Edit wiki pages", "wiki"),
        ("wiki.delete", "Delete wiki pages", "wiki"),
        ("wiki.publish", "Publish wiki pages", "wiki"),
        ("wiki.manage_sections", "Manage wiki sections", "wiki"),
        # Plot Permissions
        ("plot.reputation_briefings", "Manage reputation briefings", "plot"),
        # Downtime Permissions
        ("downtime.manage", "Manage downtime packs", "downtime"),
        # Group Management Permissions
        ("group.view_all", "View all groups", "group"),
        ("group.edit", "Edit groups", "group"),
        ("group.background_approve", "Approve group backgrounds", "group"),
        # Template Permissions
        ("template.create", "Create templates", "template"),
        ("template.edit", "Edit templates", "template"),
        # Messages Permissions (Spacer Messaging System)
        ("messages.view_all", "View all messages", "messages"),
        ("messages.respond", "Respond to messages", "messages"),
        ("messages.send_for_character", "Send messages for characters", "messages"),
        ("messages.send_for_other", "Send messages on behalf of other users", "messages"),
    ]

    permissions = {}
    for name, description, category in permissions_data:
        permission = Permission.query.filter_by(name=name).first()
        if not permission:
            permission = Permission(name=name, description=description, category=category)
            db.session.add(permission)
        permissions[name] = permission

    db.session.commit()
    return permissions


def create_default_roles(permissions):
    """Create the default roles with appropriate permissions."""

    # Create owner role (all permissions)
    owner_role = Role.query.filter_by(name="owner").first()
    if not owner_role:
        owner_role = Role(
            name="owner", description="System owner with all permissions", is_system_role=True
        )
        db.session.add(owner_role)

    # Create admin role (all permissions except user management)
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin", description="Administrator with most permissions", is_system_role=True
        )
        db.session.add(admin_role)

    # Create default role (basic permissions)
    default_role = Role.query.filter_by(name="default").first()
    if not default_role:
        default_role = Role(
            name="default", description="Default role for regular users", is_system_role=True
        )
        db.session.add(default_role)

    db.session.commit()

    # Assign permissions to owner role (all permissions)
    for permission in permissions.values():
        owner_role.add_permission(permission)

    # Assign permissions to admin role (all except user management)
    admin_permissions = [
        "character.view_all",
        "character.edit_all",
        "character.background_approve",
        "character.refund",
        "banking.view_all",
        "banking.manage",
        "event.create",
        "event.edit",
        "event.delete",
        "event.assign_tickets",
        "event.manage_attendees",
        "database.backup",
        "database.restore",
        "rules.conditions",
        "rules.skills",
        "rules.species",
        "rules.cybernetics",
        "rules.exotic_substances",
        "rules.items",
        "rules.medicaments",
        "rules.mods",
        "rules.item_types",
        "rules.item_blueprints",
        "rules.global_settings",
        "rules.group_types",
        "rules.factions",
        "research.create",
        "research.edit",
        "research.delete",
        "research.assign",
        "wiki.create",
        "wiki.edit",
        "wiki.delete",
        "wiki.publish",
        "wiki.manage_sections",
        "plot.reputation_briefings",
        "downtime.manage",
        "group.view_all",
        "group.edit",
        "group.background_approve",
        "template.create",
        "template.edit",
        "messages.view_all",
        "messages.respond",
        "messages.send_for_character",
        "messages.send_for_other",
        "user.view",
        "user.edit",
        "user.roles",
        "owner.promote",
    ]

    for perm_name in admin_permissions:
        if perm_name in permissions:
            admin_role.add_permission(permissions[perm_name])

    # Assign basic permissions to default role
    default_permissions = [
        # Default role starts with no permissions
    ]

    for perm_name in default_permissions:
        if perm_name in permissions:
            default_role.add_permission(permissions[perm_name])

    db.session.commit()

    return {"owner": owner_role, "admin": admin_role, "default": default_role}


def main():
    """Main function to set up the permissions system."""
    app = create_app()

    with app.app_context():
        print("Creating default permissions...")
        permissions = create_default_permissions()
        print(f"Created {len(permissions)} permissions")

        print("Creating default roles...")
        roles = create_default_roles(permissions)
        print(f"Created {len(roles)} roles")

        print("Permissions system setup complete!")


if __name__ == "__main__":
    main()
