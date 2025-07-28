# Database Management Feature

## Overview

The Database Management feature provides administrators with the ability to monitor database status, create backups, and restore from previous backups. This feature is only available to users with the "admin" role.

## Features

### Database Status Display
- Shows current database version (Alembic migration version)
- Displays counts of all major database objects:
  - Users
  - Characters
  - Groups
  - Messages
  - Research Projects
  - Factions
  - Species
  - Skills
  - Group Types
  - Global Settings
  - Item Types
  - Item Blueprints
  - Items
  - Conditions
  - Cybernetics
  - Samples
  - Exotic Substances
  - Medicaments
  - Mods

### Backup Management
- **Create Backup**: Creates a timestamped backup of the current database
- **Restore Backup**: Restores the database from a selected backup file
- **Backup List**: Shows all available backups with creation date and file size

## Access

The Database Management page is accessible via:
- **URL**: `/tools/database`
- **Navigation**: Tools dropdown → Database (admin users only)

## Security

- All routes require the "admin" role
- Uses the `@admin_required` decorator for route protection
- Backup files are stored in a `backups/` subdirectory relative to the database location

## File Structure

```
routes/tools/database_management.py          # Route handlers
templates/tools/database_management.html     # Page template
static/css/pages/database-management.css     # Styling
static/js/pages/database-management.js       # JavaScript functionality
tests/routes/tools/test_database_management.py  # Tests
```

## Backup File Format

Backup files are named with the pattern: `oslrp_backup_YYYYMMDD_HHMMSS.db`

Example: `oslrp_backup_20241201_143022.db`

## Implementation Details

### Database Path Detection
The system automatically detects the database file location from the Flask configuration:
- Extracts path from `SQLALCHEMY_DATABASE_URI`
- Creates backups in a `backups/` subdirectory

### Backup Process
1. Validates database file exists
2. Creates backups directory if it doesn't exist
3. Generates timestamped filename
4. Copies database file to backup location
5. Returns success/error response

### Restore Process
1. Validates backup file exists
2. Creates a backup of current database before restore
3. Copies backup file to database location
4. Returns success/error response

### Error Handling
- Graceful handling of missing files/directories
- User-friendly error messages
- Logging of errors for debugging

## Testing

The feature includes comprehensive tests covering:
- Database statistics collection
- Database version detection
- Backup file listing
- Route access control
- Error handling

Run tests with:
```bash
python -m pytest tests/routes/tools/test_database_management.py -v
```

## Usage

1. **View Database Status**:
   - Navigate to Tools → Database
   - View current version and object counts

2. **Create Backup**:
   - Click "Create Backup" button
   - Wait for confirmation message
   - Backup will appear in the list

3. **Restore Backup**:
   - Select a backup from the dropdown
   - Click "Restore Backup" button
   - Confirm the action
   - Wait for completion message

## Notes

- Backups are stored in the same directory as the database file
- The system creates a backup of the current database before restoring
- All operations are logged for audit purposes
- The interface uses Select2 for enhanced dropdown functionality
- Responsive design works on mobile devices
