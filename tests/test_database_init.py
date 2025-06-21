"""
Tests for database initialization utilities.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import OperationalError
from utils.database_init import initialize_database, check_database_status, safe_stamp_database, safe_upgrade_database
from flask import Flask

class TestDatabaseInit:
    def setup_method(self):
        self.mock_migrate = Mock()
        self.mock_db = Mock()
        self.mock_engine = Mock()

    @patch('utils.database_init.upgrade')
    def test_initialize_database_success(self, mock_upgrade):
        app = Flask(__name__)
        with app.app_context():
            app.extensions = {'migrate': self.mock_migrate}
            self.mock_migrate.db = self.mock_db
            self.mock_db.engine = self.mock_engine
            mock_upgrade.return_value = None
            initialize_database()
            mock_upgrade.assert_called_once()

    @patch('utils.database_init.upgrade')
    @patch('utils.database_init.stamp')
    @patch('utils.database_init.inspect')
    def test_initialize_database_with_existing_tables(self, mock_inspect, mock_stamp, mock_upgrade):
        app = Flask(__name__)
        with app.app_context():
            app.extensions = {'migrate': self.mock_migrate}
            self.mock_migrate.db = self.mock_db
            self.mock_db.engine = self.mock_engine
            mock_upgrade.side_effect = [
                OperationalError("table 'user' already exists", None, None),
                None
            ]
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ['user', 'character', 'sqlite_sequence']
            mock_inspect.return_value = mock_inspector
            mock_stamp.return_value = None
            initialize_database()
            mock_stamp.assert_called_once()
            assert mock_upgrade.call_count == 2

    @patch('utils.database_init.upgrade')
    @patch('utils.database_init.inspect')
    def test_initialize_database_with_alembic_version(self, mock_inspect, mock_upgrade):
        app = Flask(__name__)
        with app.app_context():
            app.extensions = {'migrate': self.mock_migrate}
            self.mock_migrate.db = self.mock_db
            self.mock_db.engine = self.mock_engine
            mock_upgrade.side_effect = OperationalError("table 'user' already exists", None, None)
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ['user', 'character', 'alembic_version']
            mock_inspect.return_value = mock_inspector
            with pytest.raises(OperationalError):
                initialize_database()

    @patch('utils.database_init.upgrade')
    @patch('utils.database_init.inspect')
    def test_initialize_database_fresh_database(self, mock_inspect, mock_upgrade):
        app = Flask(__name__)
        with app.app_context():
            app.extensions = {'migrate': self.mock_migrate}
            self.mock_migrate.db = self.mock_db
            self.mock_db.engine = self.mock_engine
            mock_upgrade.side_effect = OperationalError("table 'user' already exists", None, None)
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = []
            mock_inspect.return_value = mock_inspector
            with pytest.raises(OperationalError):
                initialize_database()

    @patch('utils.database_init.inspect')
    def test_check_database_status(self, mock_inspect):
        app = Flask(__name__)
        with app.app_context():
            app.extensions = {'migrate': self.mock_migrate}
            self.mock_migrate.db = self.mock_db
            self.mock_db.engine = self.mock_engine
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ['user', 'character', 'alembic_version', 'sqlite_sequence']
            mock_inspect.return_value = mock_inspector
            with patch('utils.database_init.current') as mock_current:
                mock_current.return_value = 'abc123'
                status = check_database_status()
                assert status['has_alembic_version'] is True
                assert status['app_tables'] == ['user', 'character']
                assert status['total_tables'] == 4
                assert status['current_revision'] == 'abc123'

    @patch('utils.database_init.stamp')
    def test_safe_stamp_database_success(self, mock_stamp):
        mock_stamp.return_value = None
        result = safe_stamp_database()
        assert result is True
        mock_stamp.assert_called_once()

    @patch('utils.database_init.stamp')
    def test_safe_stamp_database_failure(self, mock_stamp):
        mock_stamp.side_effect = Exception("Stamp failed")
        result = safe_stamp_database()
        assert result is False

    @patch('utils.database_init.upgrade')
    def test_safe_upgrade_database_success(self, mock_upgrade):
        mock_upgrade.return_value = None
        result = safe_upgrade_database()
        assert result is True
        mock_upgrade.assert_called_once()

    @patch('utils.database_init.upgrade')
    def test_safe_upgrade_database_failure(self, mock_upgrade):
        mock_upgrade.side_effect = Exception("Upgrade failed")
        result = safe_upgrade_database()
        assert result is False 