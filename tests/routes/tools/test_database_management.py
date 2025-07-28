from unittest.mock import MagicMock, patch

from routes.tools.database_management import (
    get_available_backups,
    get_backups_directory,
    get_current_database_version,
    get_database_stats,
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
        # User without admin role should get 403
        response = test_client.get("/tools/database")
        assert response.status_code == 403

    def test_database_management_route_with_admin(self, test_client, admin_user):
        """Test that database management route works with admin role."""
        response = test_client.get("/tools/database")
        assert response.status_code == 200
        assert b"Database Management" in response.data

    def test_create_backup_requires_admin(self, test_client, authenticated_user):
        """Test that create backup route requires admin role."""
        response = test_client.post("/tools/database/create-backup")
        assert response.status_code == 403

    def test_restore_backup_requires_admin(self, test_client, authenticated_user):
        """Test that restore backup route requires admin role."""
        response = test_client.post("/tools/database/restore-backup")
        assert response.status_code == 403
