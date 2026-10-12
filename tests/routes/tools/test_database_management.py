import sqlite3
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from routes.tools.database_management import (
    get_available_backups,
    get_backups_directory,
    get_current_database_version,
    get_database_stats,
    resolve_backup_path,
)


class TestDatabaseManagement:
    """Test database management functionality."""

    def test_get_database_stats(self, app, db_session):
        """Test getting database statistics."""
        with app.app_context():
            stats = get_database_stats()

            # Check that stats is a dictionary
            assert isinstance(stats, dict)

            # Check that expected keys are present
            expected_keys = [
                "Users",
                "Characters",
                "Groups",
                "Messages",
                "Research Projects",
                "Factions",
                "Species",
                "Skills",
                "Group Types",
                "Item Types",
                "Item Blueprints",
                "Items",
                "Conditions",
                "Cybernetics",
                "Samples",
                "Exotic Substances",
                "Medicaments",
                "Mods",
            ]

            for key in expected_keys:
                assert key in stats
                assert isinstance(stats[key], int)

    @patch("routes.tools.database_management.db")
    def test_get_current_database_version_success(self, mock_db, app):
        """Test getting current database version successfully."""
        with app.app_context():
            # Mock the database query result
            mock_result = MagicMock()
            mock_result.scalar.return_value = "test_version"
            mock_db.session.execute.return_value = mock_result

            version = get_current_database_version()
            assert version == "test_version"

    @patch("routes.tools.database_management.db")
    def test_get_current_database_version_error(self, mock_db, app):
        """Test getting current database version with error."""
        with app.app_context():
            # Mock the database query to raise an exception
            mock_db.session.execute.side_effect = Exception("Database error")

            version = get_current_database_version()
            assert version == "Unknown"

    @patch("routes.tools.database_management.Path")
    def test_get_available_backups_no_directory(self, mock_path, app):
        """Test getting available backups when directory doesn't exist."""
        with app.app_context():
            # Mock Path.exists to return False
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            backups = get_available_backups()
            assert backups == []

    @patch("routes.tools.database_management.get_database_path")
    def test_get_backups_directory(self, mock_get_db_path, app):
        """Test getting backups directory path."""
        with app.app_context():
            # Mock database path
            mock_db_path = MagicMock()
            mock_parent = MagicMock()
            # Mock the __truediv__ method to return a string
            mock_parent.__truediv__.return_value = "backups_path/backups"
            mock_db_path.parent = mock_parent
            mock_get_db_path.return_value = mock_db_path

            backups_dir = get_backups_directory()
            assert backups_dir == "backups_path/backups"

    @patch("routes.tools.database_management.get_database_path")
    def test_get_backups_directory_error(self, mock_get_db_path, app):
        """Test getting backups directory when database path is None."""
        with app.app_context():
            mock_get_db_path.return_value = None

            backups_dir = get_backups_directory()
            assert backups_dir is None


class TestDatabaseManagementRoutes:
    """Test database management routes."""

    def test_database_management_route_requires_admin(self, test_client, authenticated_user):
        """Test that database management route requires admin role."""
        # User without admin role should get 302 (redirect)
        response = test_client.get("/tools/database")
        assert response.status_code == 302

    def test_database_management_route_with_admin(self, test_client, admin_user):
        """Test that database management route works with admin role."""
        response = test_client.get("/tools/database")
        assert response.status_code == 200
        assert b"Database Management" in response.data

    def test_create_backup_requires_admin(self, test_client, authenticated_user):
        """Test that create backup route requires admin role."""
        response = test_client.post("/tools/database/create-backup")
        assert response.status_code == 302

    def test_restore_backup_requires_admin(self, test_client, authenticated_user):
        """Test that restore backup route requires admin role."""
        response = test_client.post("/tools/database/restore-backup")
        assert response.status_code == 302

    def test_create_backup_snapshots_open_database(self, test_client, admin_user, app, tmp_path):
        """A backup taken while the database is open is a consistent SQLite file."""
        db_file = tmp_path / "live.db"
        connection = sqlite3.connect(db_file)
        try:
            connection.execute("CREATE TABLE marker (label TEXT)")
            connection.execute("INSERT INTO marker (label) VALUES ('open-db')")
            connection.commit()

            with sqlite_database_config(app, db_file):
                response = test_client.post("/tools/database/create-backup")
        finally:
            connection.close()

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        backup_path = tmp_path / "backups" / payload["filename"]
        assert backup_path.is_file()

        backup = sqlite3.connect(backup_path)
        try:
            integrity = backup.execute("PRAGMA integrity_check").fetchone()[0]
            label = backup.execute("SELECT label FROM marker").fetchone()[0]
        finally:
            backup.close()
        assert integrity == "ok"
        assert label == "open-db"

    def test_restore_backup_replaces_live_database(self, test_client, admin_user, app, tmp_path):
        """Restore copies a named backup from the backups directory over the live file."""
        db_dir = tmp_path / "data"
        db_file = db_dir / "live.db"
        backup_name = "oslrp_backup_20200101_120000.db"
        write_marker_db(db_file, "live")
        write_marker_db(db_dir / "backups" / backup_name, "restored")

        with sqlite_database_config(app, db_file):
            response = test_client.post(
                "/tools/database/restore-backup",
                data={"backup_filename": f"../backups/{backup_name}"},
            )

        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert read_marker(db_file) == "restored"
        pre_restore = list(db_dir.glob("oslrp_pre_restore_*.db"))
        assert len(pre_restore) == 1
        assert read_marker(pre_restore[0]) == "live"

    def test_restore_backup_rejects_files_outside_backups(
        self, test_client, admin_user, app, tmp_path
    ):
        """Restore refuses filenames that are not a backup inside the backups directory."""
        db_dir = tmp_path / "data"
        db_file = db_dir / "live.db"
        outside = tmp_path / "secret.db"
        write_marker_db(db_file, "live")
        write_marker_db(outside, "secret")

        with sqlite_database_config(app, db_file):
            response = test_client.post(
                "/tools/database/restore-backup",
                data={"backup_filename": "../secret.db"},
            )

        assert response.status_code == 400
        assert response.get_json()["error"] == "Invalid backup file"
        assert read_marker(db_file) == "live"
        assert read_marker(outside) == "secret"


class TestBackupPathResolution:
    """Backup restore only accepts names inside the backups directory."""

    def test_resolve_backup_path_uses_basename_inside_backups(self, tmp_path):
        backups = tmp_path / "backups"
        backups.mkdir()
        name = "oslrp_backup_20200101_120000.db"
        resolved = resolve_backup_path(backups, str(tmp_path / name))
        assert resolved == (backups / name).resolve()

    @pytest.mark.parametrize(
        "filename",
        [
            "secret.db",
            "../secret.db",
            "..\\secret.db",
            "oslrp_pre_restore_20200101_120000.db",
            "oslrp_backup_20200101_120000.txt",
            "oslrp_backup_20200101_120000.db/../../secret.db",
        ],
    )
    def test_resolve_backup_path_rejects_unexpected_names(self, tmp_path, filename):
        backups = tmp_path / "backups"
        backups.mkdir()
        assert resolve_backup_path(backups, filename) is None

    def test_resolve_backup_path_rejects_symlink_outside_backups(self, tmp_path):
        backups = tmp_path / "backups"
        backups.mkdir()
        outside = tmp_path / "oslrp_backup_20200101_120000.db"
        write_marker_db(outside, "outside")
        link = backups / outside.name
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not available")

        assert resolve_backup_path(backups, link.name) is None


def write_marker_db(path, label):
    """Create a small SQLite file containing one marker row."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE marker (label TEXT)")
        connection.execute("INSERT INTO marker (label) VALUES (?)", (label,))
        connection.commit()
    finally:
        connection.close()


def read_marker(path):
    """Return the marker label stored by write_marker_db."""
    connection = sqlite3.connect(path)
    try:
        return connection.execute("SELECT label FROM marker").fetchone()[0]
    finally:
        connection.close()


@contextmanager
def sqlite_database_config(app, db_file):
    """Point database management at a file without changing the test engine."""
    original_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + Path(db_file).resolve().as_posix()
    try:
        yield
    finally:
        app.config["SQLALCHEMY_DATABASE_URI"] = original_uri
