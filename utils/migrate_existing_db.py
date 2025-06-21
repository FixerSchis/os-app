#!/usr/bin/env python3
"""
Command-line utility to handle existing databases that don't have migration tracking.

This script helps migrate existing databases that were created without Alembic
migration tracking by stamping them as being at the current head revision.

Usage:
    python utils/migrate_existing_db.py [--check] [--stamp] [--upgrade]
"""

import argparse
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app import create_app
from utils.database_init import initialize_database, check_database_status
from flask_migrate import stamp, upgrade, current
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Handle existing databases without migration tracking"
    )
    parser.add_argument(
        '--check', 
        action='store_true', 
        help='Check database status without making changes'
    )
    parser.add_argument(
        '--stamp', 
        action='store_true', 
        help='Stamp database as current head (for existing databases without alembic_version)'
    )
    parser.add_argument(
        '--upgrade', 
        action='store_true', 
        help='Run database upgrades after stamping'
    )
    parser.add_argument(
        '--auto', 
        action='store_true', 
        help='Automatically handle database initialization (recommended)'
    )
    
    args = parser.parse_args()
    
    if not any([args.check, args.stamp, args.upgrade, args.auto]):
        parser.print_help()
        return
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        if args.check:
            logger.info("Checking database status...")
            status = check_database_status()
            
            print("\nDatabase Status:")
            print(f"  Has alembic_version table: {status['has_alembic_version']}")
            print(f"  Total tables: {status['total_tables']}")
            print(f"  Application tables: {status['app_tables']}")
            
            if 'current_revision' in status:
                if status['current_revision']:
                    print(f"  Current revision: {status['current_revision']}")
                else:
                    print(f"  Current revision: None (Error: {status.get('revision_error', 'Unknown')})")
            
            if 'error' in status:
                print(f"  Error: {status['error']}")
        
        elif args.stamp:
            logger.info("Stamping database as current head...")
            try:
                stamp()
                logger.info("Database stamped successfully!")
            except Exception as e:
                logger.error(f"Failed to stamp database: {e}")
                sys.exit(1)
        
        elif args.upgrade:
            logger.info("Running database upgrades...")
            try:
                upgrade()
                logger.info("Database upgrades completed successfully!")
            except Exception as e:
                logger.error(f"Failed to upgrade database: {e}")
                sys.exit(1)
        
        elif args.auto:
            logger.info("Automatically handling database initialization...")
            try:
                initialize_database()
                logger.info("Database initialization completed successfully!")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                sys.exit(1)

if __name__ == '__main__':
    main() 