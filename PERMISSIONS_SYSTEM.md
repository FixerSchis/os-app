# Granular Permissions System

This document describes the granular permissions system that replaces the old role-based system.

## Overview

The system uses a three-tier architecture:
1. **Permissions**: Granular actions (e.g., `user.view`, `character.edit_all`)
2. **Roles**: Collections of permissions that can be assigned to users
3. **Users**: Have a single role that grants them specific permissions

## Core Components

### Permission Model
```python
class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    roles = db.relationship('Role', secondary='role_permissions', back_populates='permissions')
```

### Role Model
```python
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_system_role = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    permissions = db.relationship('Permission', secondary='role_permissions', back_populates='roles')
```

### User Model
```python
class User(db.Model):
    # ... other fields ...
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)
    role = db.relationship('Role', backref='users')

    def has_permission(self, permission_name):
        """Check if the user has a specific permission."""
        if self.role:
            return self.role.has_permission(permission_name)
        return False
```

## System Roles

Three system roles are created by default and cannot be modified or deleted:

1. **owner**: Has all permissions, automatically assigned to the first user
2. **admin**: Has all permissions except user management
3. **default**: Has a basic set of permissions for regular users

## Available Permissions

### User Management
- `user.view` - View user list and details
- `user.edit` - Edit user information
- `user.roles` - Manage user roles and permissions
- `user.delete` - Delete users

### Character Management
- `character.view_all` - View all characters
- `character.edit_all` - Edit any character
- `character.delete` - Delete characters
- `character.background_approve` - Approve character backgrounds
- `character.refund_points` - Refund character points

### Banking
- `banking.view_all` - View all bank accounts
- `banking.manage` - Manage bank accounts
- `banking.transfer` - Perform transfers

### Events
- `event.create` - Create events
- `event.edit` - Edit events
- `event.delete` - Delete events
- `event.manage` - Manage event assignments and attendees
- `event.view_attendees` - View event attendees
- `event.view_packs` - View event packs
- `event.assign_tickets` - Assign tickets to users

### Database Management
- `database.backup` - Create database backups
- `database.restore` - Restore database from backup
- `database.export` - Export database data

### Rules Management
- `rules.conditions` - Manage conditions
- `rules.skills` - Manage skills
- `rules.species` - Manage species
- `rules.cybernetics` - Manage cybernetics
- `rules.exotic_substances` - Manage exotic substances
- `rules.items` - Manage items
- `rules.medicaments` - Manage medicaments
- `rules.mods` - Manage mods
- `rules.item_types` - Manage item types
- `rules.item_blueprints` - Manage item blueprints
- `rules.global_settings` - Manage global settings
- `rules.group_types` - Manage group types

### Research
- `research.create` - Create research projects
- `research.edit` - Edit research projects
- `research.delete` - Delete research projects

### Wiki
- `wiki.create` - Create wiki pages
- `wiki.edit` - Edit wiki pages
- `wiki.delete` - Delete wiki pages
- `wiki.publish` - Publish wiki changes
- `wiki.manage_sections` - Manage wiki sections

### Plot
- `plot.reputation_briefings` - Manage reputation briefings
- `plot.messages` - Manage plot messages

### Downtime
- `downtime.manage` - Manage downtime periods
- `downtime.approve` - Approve downtime submissions

### Groups
- `group.view_all` - View all groups
- `group.edit` - Edit groups
- `group.delete` - Delete groups
- `group.manage_members` - Manage group members
- `group.background_approve` - Approve group backgrounds

### Templates
- `template.create` - Create templates
- `template.edit` - Edit templates
- `template.delete` - Delete templates

## Usage Examples

### In Python Routes
```python
from utils.permission_decorators import permission_required

@app.route("/admin/users")
@login_required
@permission_required(permissions=["user.view"])
def user_list():
    # Route logic here
    pass

@app.route("/admin/users/<int:user_id>/edit")
@login_required
@permission_required(permissions=["user.edit", "user.roles"])
def edit_user(user_id):
    # Route logic here
    pass
```

### In Templates
```html
{% if has_permission('user.view') %}
    <a href="{{ url_for('user_management.list') }}">Manage Users</a>
{% endif %}

{% if can_manage_characters() %}
    <a href="{{ url_for('characters.create') }}">Create Character</a>
{% endif %}
```

### In Python Code
```python
if current_user.has_permission("character.edit_all"):
    # Allow editing any character
    pass

if current_user.has_any_permission(["user.view", "user.edit"]):
    # Allow user management operations
    pass
```

## Template Helpers

The following helper functions are available in templates:

### Permission Checks
- `has_permission(permission_name)` - Check for specific permission
- `has_any_permission(permission_names)` - Check for any of multiple permissions
- `has_all_permissions(permission_names)` - Check for all of multiple permissions

### Management Checks
- `can_manage_users()` - Check if user can manage users
- `can_manage_characters()` - Check if user can manage characters
- `can_manage_banking()` - Check if user can manage banking
- `can_manage_events()` - Check if user can manage events
- `can_manage_database()` - Check if user can manage database
- `can_manage_rules()` - Check if user can manage rules
- `can_manage_research()` - Check if user can manage research
- `can_manage_wiki()` - Check if user can manage wiki
- `can_manage_plot()` - Check if user can manage plot
- `can_manage_downtime()` - Check if user can manage downtime
- `can_manage_groups()` - Check if user can manage groups
- `can_manage_templates()` - Check if user can manage templates
- `can_approve_character_backgrounds()` - Check if user can approve character backgrounds
- `can_approve_group_backgrounds()` - Check if user can approve group backgrounds

## Migration from Old System

The old role-based system has been completely removed. All routes and templates now use the new granular permission system.

### Key Changes
1. **No Backward Compatibility**: The old `has_role()` method and role-based decorators have been removed
2. **Granular Permissions**: All access control is now based on specific permissions
3. **Single Role per User**: Users now have one role instead of multiple roles
4. **Runtime Role Management**: Roles and permissions can be managed through the web interface

## Role Management Interface

Access the role management interface at `/tools/roles` to:
- View all roles and their permissions
- Create new custom roles
- Edit existing roles (except system roles)
- Delete custom roles
- View all available permissions

## Security Considerations

1. **System Roles**: The "owner", "admin", and "default" roles cannot be modified or deleted
2. **Permission Granularity**: Each action requires specific permission checks
3. **Role Assignment**: Only users with `user.roles` permission can assign roles
4. **Audit Trail**: All role and permission changes are logged
