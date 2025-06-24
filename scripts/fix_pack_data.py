#!/usr/bin/env python3
"""
Script to fix corrupted pack data in the database.
"""

import json
import os
import sys

from app import create_app
from models.extensions import db
from models.tools.character import Character
from models.tools.group import Group
from models.tools.pack import Pack

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def fix_pack_data():
    """Fix corrupted pack data in the database."""
    app = create_app()

    with app.app_context():
        print("Checking for corrupted pack data...")

        # Fix character pack data
        characters = Character.query.all()
        fixed_characters = 0

        for character in characters:
            try:
                # Try to load the pack
                pack = character.pack
                # If successful, save it back to ensure it's in the correct format
                character.pack = pack
                fixed_characters += 1
            except Exception as e:
                print(
                    f"Fixing corrupted pack data for character {character.id} "
                    f"({character.name}): {e}"
                )
                # Create a new empty pack
                character.pack = Pack()
                fixed_characters += 1

        # Fix group pack data
        groups = Group.query.all()
        fixed_groups = 0

        for group in groups:
            try:
                # Try to load the pack
                pack = group.pack
                # If successful, save it back to ensure it's in the correct format
                group.pack = pack
                fixed_groups += 1
            except Exception as e:
                print(f"Fixing corrupted pack data for group {group.id} ({group.name}): {e}")
                # Create a new empty pack
                group.pack = Pack()
                fixed_groups += 1

        # Commit all changes
        db.session.commit()

        print(f"Fixed pack data for {fixed_characters} characters and {fixed_groups} groups.")


if __name__ == "__main__":
    fix_pack_data()
