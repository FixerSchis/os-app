#!/usr/bin/env python3
"""Run database migration with Flask app context."""

from flask_migrate import upgrade

from app import create_app

app = create_app()

with app.app_context():
    upgrade()
    print("Migration completed successfully!")
