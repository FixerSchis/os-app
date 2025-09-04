#!/usr/bin/env python3
"""
Script to update downtime packs character_id from 3 to 1.
This script will:
1. Show current state of downtime packs with character_id 3
2. Update them to character_id 1
3. Show the updated state
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from models.extensions import db  # noqa: E402
from models.tools.character import Character  # noqa: E402
from models.tools.downtime import DowntimePack  # noqa: E402


def main():
    app = create_app()

    with app.app_context():
        print("=== Downtime Pack Character ID Update ===")
        print()

        # Check if character_id 1 exists
        character_1 = Character.query.get(1)
        if not character_1:
            print("ERROR: Character with ID 1 does not exist!")
            return

        print(f"Target character (ID 1): {character_1.name}")
        print()

        # Find all downtime packs with character_id 3
        packs_to_update = DowntimePack.query.filter_by(character_id=3).all()

        if not packs_to_update:
            print("No downtime packs found with character_id 3.")
            return

        print(f"Found {len(packs_to_update)} downtime pack(s) with character_id 3:")
        for pack in packs_to_update:
            print(
                f"  - Pack ID: {pack.id}, Period ID: {pack.period_id}, "
                f"Status: {pack.status.value}"
            )

        print()

        # Show current character 3 info if it exists
        character_3 = Character.query.get(3)
        if character_3:
            print(f"Source character (ID 3): {character_3.name}")
        else:
            print("Source character (ID 3): Does not exist")

        print()

        # Confirm the update
        response = input(
            f"Do you want to update {len(packs_to_update)} downtime pack(s) "
            f"from character_id 3 to character_id 1? (y/N): "
        )

        if response.lower() != "y":
            print("Update cancelled.")
            return

        # Perform the update
        try:
            updated_count = DowntimePack.query.filter_by(character_id=3).update({"character_id": 1})
            db.session.commit()

            print(f"Successfully updated {updated_count} downtime pack(s).")
            print()

            # Verify the update
            remaining_packs_3 = DowntimePack.query.filter_by(character_id=3).count()
            new_packs_1 = DowntimePack.query.filter_by(character_id=1).count()

            print("Verification:")
            print(f"  - Downtime packs with character_id 3: {remaining_packs_3}")
            print(f"  - Downtime packs with character_id 1: {new_packs_1}")

        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Failed to update downtime packs: {e}")
            return

        print()
        print("Update completed successfully!")


if __name__ == "__main__":
    main()
