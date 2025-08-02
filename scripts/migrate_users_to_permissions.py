#!/usr/bin/env python3
"""
Script to migrate existing users from the old role system to the new granular permissions system.
"""

from app import create_app
from models.database.permissions import Role
from models.extensions import db
from models.tools.user import User


def migrate_users_to_new_system():
    """Migrate existing users to the new role system."""
    app = create_app()

    with app.app_context():
        # Get the default roles
        owner_role = Role.query.filter_by(name="owner").first()
        admin_role = Role.query.filter_by(name="admin").first()
        default_role = Role.query.filter_by(name="default").first()

        if not owner_role or not admin_role or not default_role:
            print("Error: Default roles not found. Please run setup_permissions.py first.")
            return

        # Get all users
        users = User.query.all()

        if not users:
            print("No users found to migrate.")
            return

        # Find the first user (will become owner)
        first_user = users[0]
        print(f"Setting {first_user.email} as owner...")
        first_user.role = owner_role

        # Migrate other users
        migrated_count = 0
        for user in users[1:]:  # Skip the first user (already set as owner)
            old_roles = (user.roles or "").split(",")
            old_roles = [r.strip() for r in old_roles if r.strip()]

            # Determine new role based on old roles
            if "admin" in old_roles:
                new_role = admin_role
                print(f"Migrating {user.email} to admin role (had: {old_roles})")
            else:
                new_role = default_role
                print(f"Migrating {user.email} to default role (had: {old_roles})")

            user.role = new_role
            migrated_count += 1

        # Commit changes
        db.session.commit()

        print(f"Migration complete! Migrated {migrated_count} users.")
        print(f"Owner: {first_user.email}")
        print("Note: The old 'roles' field is preserved for rollback purposes.")


def main():
    """Main function to run the migration."""
    print("Starting user migration to new permissions system...")
    migrate_users_to_new_system()
    print("Migration script completed!")


if __name__ == "__main__":
    main()
