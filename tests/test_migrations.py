"""
Test all migrations step-by-step to ensure they are idempotent and reversible.

This test suite:
1. Tests each migration in order from base to head
2. Tests each migration can be run multiple times (idempotency)
3. Tests each migration can be downgraded and re-upgraded
4. Tests the entire migration chain from base to head and back
"""

import os
import tempfile
from pathlib import Path

import pytest
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


class TestMigrations:
    """Test all migrations step-by-step."""

    @pytest.fixture(scope="class")
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        import time

        time.sleep(0.1)  # Give time for connections to close
        try:
            os.unlink(db_path)
        except PermissionError:
            pass  # Ignore if file is still locked

    @pytest.fixture(scope="class")
    def app(self, temp_db_path):
        """Create a Flask app for testing migrations."""
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{temp_db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # Initialize SQLAlchemy and Migrate
        db = SQLAlchemy(app)
        Migrate(app, db)

        return app

    @pytest.fixture(scope="class")
    def engine(self, temp_db_path):
        """Create a SQLAlchemy engine for the test database."""
        from sqlalchemy import create_engine

        engine = create_engine(f"sqlite:///{temp_db_path}")
        yield engine
        engine.dispose()

    def get_migration_revisions(self, app):
        """Get all migration revisions in order."""
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        # Get the migrations directory
        migrations_dir = Path(__file__).parent.parent / "migrations"

        # Create Alembic config
        config = Config()
        config.set_main_option("script_location", str(migrations_dir))
        config.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])

        # Get script directory
        script_dir = ScriptDirectory.from_config(config)

        # Get all revisions
        revisions = []
        current = script_dir.get_current_head()

        # Walk backwards from head to base
        while current:
            revisions.insert(0, current)
            try:
                current = script_dir.get_revision(current).down_revision
            except Exception:
                break

        return revisions

    def test_all_migrations_step_by_step(self, app, engine):
        """Test each migration step-by-step."""
        from flask_migrate import downgrade, upgrade

        with app.app_context():
            revisions = self.get_migration_revisions(app)

            print(f"\nTesting {len(revisions)} migrations:")
            for i, rev in enumerate(revisions):
                print(f"  {i + 1:2d}. {rev}")

            # Test each migration individually
            for i, revision in enumerate(revisions):
                print(f"\n--- Testing migration {i + 1}/{len(revisions)}: {revision} ---")

                # Skip the base migration (no upgrade needed)
                if revision == revisions[0]:
                    print("  Skipping base migration (no upgrade needed)")
                    continue

                # Test upgrade
                print(f"  Testing upgrade to {revision}")
                try:
                    upgrade(revision=revision)
                    print(f"  ✓ Upgrade to {revision} successful")
                except Exception as e:
                    pytest.fail(f"Upgrade to {revision} failed: {e}")

                # Test idempotency (run upgrade again)
                print(f"  Testing idempotency for {revision}")
                try:
                    upgrade(revision=revision)
                    print(f"  ✓ Idempotency test for {revision} successful")
                except Exception as e:
                    pytest.fail(f"Idempotency test for {revision} failed: {e}")

                # Test downgrade to previous revision
                if i > 0:
                    prev_revision = revisions[i - 1]
                    if isinstance(prev_revision, tuple):
                        prev_revision = prev_revision[0]
                    print(f"  Testing downgrade from {revision} to {prev_revision}")
                    try:
                        downgrade(revision=prev_revision)
                        print(f"  ✓ Downgrade from {revision} to {prev_revision} successful")
                    except Exception as e:
                        pytest.fail(f"Downgrade from {revision} to {prev_revision} failed: {e}")

                    # Test re-upgrade
                    print(f"  Testing re-upgrade from {prev_revision} to {revision}")
                    try:
                        upgrade(revision=revision)
                        print(f"  ✓ Re-upgrade from {prev_revision} to {revision} successful")
                    except Exception as e:
                        pytest.fail(f"Re-upgrade from {prev_revision} to {revision} failed: {e}")

    def test_full_migration_chain(self, app, engine):
        """Test the complete migration chain from base to head and back."""
        from flask_migrate import downgrade, upgrade

        with app.app_context():
            revisions = self.get_migration_revisions(app)
            head_revision = revisions[-1]
            base_revision = revisions[0]
            if isinstance(base_revision, tuple):
                base_revision = base_revision[0]

            print("\n--- Testing full migration chain ---")

            # Test upgrade to head
            print(f"Testing upgrade from {base_revision} to {head_revision}")
            try:
                upgrade()
                print(f"✓ Full upgrade to {head_revision} successful")
            except Exception as e:
                pytest.fail(f"Full upgrade to {head_revision} failed: {e}")

            # Test downgrade to base
            print(f"Testing downgrade from {head_revision} to {base_revision}")
            try:
                downgrade(revision=base_revision)
                print(f"✓ Full downgrade to {base_revision} successful")
            except Exception as e:
                pytest.fail(f"Full downgrade to {base_revision} failed: {e}")

            # Test re-upgrade to head
            print(f"Testing re-upgrade from {base_revision} to {head_revision}")
            try:
                upgrade()
                print(f"✓ Full re-upgrade to {head_revision} successful")
            except Exception as e:
                pytest.fail(f"Full re-upgrade to {head_revision} failed: {e}")

    def test_migration_idempotency(self, app, engine):
        """Test that running the same migration multiple times doesn't cause issues."""
        from flask_migrate import upgrade

        with app.app_context():
            revisions = self.get_migration_revisions(app)
            head_revision = revisions[-1]

            print("\n--- Testing migration idempotency ---")

            # Upgrade to head
            print(f"Upgrading to {head_revision}")
            upgrade()

            # Run upgrade to head multiple times
            for i in range(3):
                print(f"Running upgrade to {head_revision} again (attempt {i + 1})")
                try:
                    upgrade()
                    print(f"✓ Idempotency test {i + 1} successful")
                except Exception as e:
                    pytest.fail(f"Idempotency test {i + 1} failed: {e}")

    def test_database_schema_consistency(self, app, engine):
        """Test that the final database schema is consistent."""
        with app.app_context():
            print("\n--- Testing database schema consistency ---")

            # Check that key tables exist
            with engine.connect() as conn:
                # Get all tables
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result]

                # Check for essential tables
                essential_tables = [
                    "user",
                    "character",
                    "events",
                    "group",
                    "faction",
                    "skill",
                    "conditions",
                    "cybernetics",
                    "exotic_substances",
                ]

                missing_tables = [table for table in essential_tables if table not in tables]
                if missing_tables:
                    pytest.fail(f"Missing essential tables: {missing_tables}")

                print(f"✓ All essential tables present: {essential_tables}")

                # Check that user table doesn't have player_id column
                result = conn.execute(text("PRAGMA table_info(user)"))
                columns = [row[1] for row in result]

                if "player_id" in columns:
                    pytest.fail("user table still has player_id column after migration")

                print("✓ user table correctly has no player_id column")

                # Check that character table has user_id column
                result = conn.execute(text("PRAGMA table_info(character)"))
                columns = [row[1] for row in result]

                if "user_id" not in columns:
                    pytest.fail("character table missing user_id column")

                print("✓ character table correctly has user_id column")
