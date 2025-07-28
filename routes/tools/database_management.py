import os
import shutil
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, flash, jsonify, render_template, request
from flask_login import login_required
from sqlalchemy import text

from models.database.conditions import Condition
from models.database.cybernetic import Cybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.group_type import GroupType
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.medicaments import Medicament
from models.database.mods import Mod
from models.database.sample import Sample
from models.database.skills import Skill
from models.database.species import Species
from models.extensions import db
from models.tools.character import Character
from models.tools.group import Group
from models.tools.message import Message
from models.tools.research import CharacterResearch
from models.tools.user import User
from utils.decorators import admin_required

database_management_bp = Blueprint("database_management", __name__)


@database_management_bp.route("/database")
@login_required
@admin_required
def database_management():
    """Database management page showing status and backup options."""

    # Get database statistics
    stats = get_database_stats()

    # Get current database version
    current_version = get_current_database_version()

    # Get available backups
    backups = get_available_backups()

    return render_template(
        "tools/database_management.html",
        stats=stats,
        current_version=current_version,
        backups=backups,
    )


@database_management_bp.route("/database/create-backup", methods=["POST"])
@login_required
@admin_required
def create_backup():
    """Create a new database backup."""
    try:
        # Get database file path
        db_path = get_database_path()
        if not db_path or not os.path.exists(db_path):
            return jsonify({"success": False, "error": "Database file not found"}), 400

        # Create backups directory if it doesn't exist
        backups_dir = get_backups_directory()
        backups_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"oslrp_backup_{timestamp}.db"
        backup_path = backups_dir / backup_filename

        # Copy database file
        shutil.copy2(db_path, backup_path)

        flash(f"Database backup created successfully: {backup_filename}", "success")
        return jsonify({"success": True, "filename": backup_filename})

    except Exception as e:
        current_app.logger.error(f"Error creating backup: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@database_management_bp.route("/database/restore-backup", methods=["POST"])
@login_required
@admin_required
def restore_backup():
    """Restore database from a backup."""
    try:
        backup_filename = request.form.get("backup_filename")
        if not backup_filename:
            return jsonify({"success": False, "error": "No backup file selected"}), 400

        # Validate backup file exists
        backups_dir = get_backups_directory()
        backup_path = backups_dir / backup_filename

        if not backup_path.exists():
            return jsonify({"success": False, "error": "Backup file not found"}), 400

        # Get current database path
        db_path = get_database_path()
        if not db_path:
            return jsonify({"success": False, "error": "Database file not found"}), 400

        # Create a backup of current database before restoring
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = db_path.parent / f"oslrp_pre_restore_{timestamp}.db"
        shutil.copy2(db_path, current_backup)

        # Restore the selected backup
        shutil.copy2(backup_path, db_path)

        flash(f"Database restored successfully from {backup_filename}", "success")
        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Error restoring backup: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def get_database_stats():
    """Get statistics about the database contents."""
    stats = {}

    # Database models to count
    models = {
        "Users": User,
        "Characters": Character,
        "Groups": Group,
        "Messages": Message,
        "Research Projects": CharacterResearch,
        "Factions": Faction,
        "Species": Species,
        "Skills": Skill,
        "Group Types": GroupType,
        "Item Types": ItemType,
        "Item Blueprints": ItemBlueprint,
        "Items": Item,
        "Conditions": Condition,
        "Cybernetics": Cybernetic,
        "Samples": Sample,
        "Exotic Substances": ExoticSubstance,
        "Medicaments": Medicament,
        "Mods": Mod,
    }

    for name, model in models.items():
        try:
            count = model.query.count()
            stats[name] = count
        except Exception as e:
            current_app.logger.error(f"Error counting {name}: {str(e)}")
            stats[name] = 0

    return stats


def get_current_database_version():
    """Get the current database version from Alembic."""
    try:
        # Get the current revision from the alembic_version table
        result = db.session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        version = result.scalar()
        return version if version else "Unknown"
    except Exception as e:
        current_app.logger.error(f"Error getting database version: {str(e)}")
        return "Unknown"


def get_available_backups():
    """Get list of available backup files."""
    backups = []
    backups_dir = get_backups_directory()

    if not backups_dir.exists():
        return backups

    for backup_file in backups_dir.glob("oslrp_backup_*.db"):
        try:
            # Extract timestamp from filename
            filename = backup_file.name
            if filename.startswith("oslrp_backup_") and filename.endswith(".db"):
                timestamp_str = filename[13:-3]  # Remove prefix and suffix
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                backups.append(
                    {
                        "filename": filename,
                        "timestamp": timestamp,
                        "size": backup_file.stat().st_size,
                        "formatted_date": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
        except Exception as e:
            current_app.logger.error(f"Error processing backup file {backup_file}: {str(e)}")

    # Sort by timestamp (newest first)
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    return backups


def get_database_path():
    """Get the path to the database file."""
    try:
        # Get database URI from config
        db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            # Extract file path from SQLite URI
            db_path = db_uri.replace("sqlite:///", "")
            return Path(db_path)
        return None
    except Exception as e:
        current_app.logger.error(f"Error getting database path: {str(e)}")
        return None


def get_backups_directory():
    """Get the backups directory path."""
    try:
        # Use the same base directory as the database
        db_path = get_database_path()
        if db_path:
            return db_path.parent / "backups"
        return None
    except Exception as e:
        current_app.logger.error(f"Error getting backups directory: {str(e)}")
        return None
