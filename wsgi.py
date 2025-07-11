#!/usr/bin/env python3
"""
WSGI entry point for OS App
"""
import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import the Flask app factory
from app import create_app  # noqa: E402

# Create the Flask application
application = create_app()

if __name__ == "__main__":
    config = application.config

    ssl_context = None
    if config.get("SSL_ENABLED"):
        ssl_context = (config.get("SSL_CERT_FILE"), config.get("SSL_KEY_FILE"))

    application.run(
        debug=config.get("FLASK_DEBUG", "0") == "1",
        host=config.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=config.get("DEFAULT_PORT", 5000),
        ssl_context=ssl_context,
    )
