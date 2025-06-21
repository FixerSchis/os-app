"""
Database initialization utilities for handling existing databases
that may not have been set up with migrations.
"""

import logging

from flask import current_app
from flask_migrate import current, stamp, upgrade
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


def initialize_database():
    """
    Initialize the database, handling cases where:
    1. Database is empty (normal migration)
    2. Database has tables but no alembic_version table (stamp then migrate)
    3. Database has tables and alembic_version table (normal migration)
    """
    try:
        # First, try to run migrations normally
        logger.info("Attempting to run database migrations...")
        upgrade()
        logger.info("Database migrations completed successfully.")

    except (OperationalError, ProgrammingError) as e:
        # Check if this is a "table already exists" error
        error_str = str(e).lower()
        if any(
            keyword in error_str for keyword in ["table", "already exists", "duplicate", "exists"]
        ):
            logger.warning(f"Migration failed with table existence error: {e}")

            # Check if this is because tables exist but alembic_version doesn't
            inspector = inspect(current_app.extensions["migrate"].db.engine)
            tables = inspector.get_table_names()

            if "alembic_version" not in tables:
                logger.info(
                    "This appears to be an existing database without migration " "tracking."
                )

                # Check if we have any application tables (indicating this is a real
                # database)
                app_tables = [
                    t for t in tables if t not in ["sqlite_sequence"]
                ]  # Exclude SQLite system tables

                if app_tables:
                    logger.info(f"Found existing tables: {app_tables}")
                    logger.info("Stamping database as current head to enable migrations...")

                    try:
                        # Stamp the database as being at the current head
                        stamp()
                        logger.info("Database stamped successfully.")

                        # Now try upgrade again to apply any pending migrations
                        logger.info("Checking for any pending migrations...")
                        upgrade()
                        logger.info("Database initialization completed successfully.")

                    except Exception as stamp_error:
                        logger.error(f"Failed to stamp database: {stamp_error}")
                        raise RuntimeError(f"Failed to initialize existing database: {stamp_error}")
                else:
                    # No application tables found, this might be a fresh database
                    logger.info(
                        "No application tables found. This appears to be a fresh " "database."
                    )
                    raise e
            else:
                # alembic_version table exists, so this is a different error
                logger.error(f"Migration failed with existing alembic_version table: {e}")
                raise e
        else:
            # Some other database error
            logger.error(f"Database error during migration: {e}")
            raise e

    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Unexpected error during database initialization: {e}")
        raise e


def check_database_status():
    """
    Check the current status of the database and migrations.
    Returns a dictionary with status information.
    """
    try:
        inspector = inspect(current_app.extensions["migrate"].db.engine)
        tables = inspector.get_table_names()

        status = {
            "has_alembic_version": "alembic_version" in tables,
            "app_tables": [t for t in tables if t not in ["sqlite_sequence", "alembic_version"]],
            "total_tables": len(tables),
        }

        if "alembic_version" in tables:
            try:
                current_revision = current()
                status["current_revision"] = current_revision
            except Exception as e:
                status["current_revision"] = None
                status["revision_error"] = str(e)

        return status

    except Exception as e:
        return {
            "error": str(e),
            "has_alembic_version": False,
            "app_tables": [],
            "total_tables": 0,
        }


def safe_stamp_database():
    """
    Safely stamp the database as current head, handling various error conditions.
    """
    try:
        logger.info("Stamping database as current head...")
        stamp()
        logger.info("Database stamped successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to stamp database: {e}")
        return False


def safe_upgrade_database():
    """
    Safely upgrade the database, handling various error conditions.
    """
    try:
        logger.info("Running database upgrades...")
        upgrade()
        logger.info("Database upgrades completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to upgrade database: {e}")
        return False
