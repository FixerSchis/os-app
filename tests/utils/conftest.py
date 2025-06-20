import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

@pytest.fixture
def mock_flask_app():
    """Create a mock Flask app for testing."""
    from unittest.mock import MagicMock
    app = MagicMock()
    app.config = {
        'BASE_URL': 'https://example.com',
        'static_folder': '/static'
    }
    return app 