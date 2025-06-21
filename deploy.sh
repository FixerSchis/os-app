#!/bin/bash

# Orion Sphere LRP Linux Deployment Script
# This script automates the deployment of the Orion Sphere LRP application on Linux servers
# Supports both fresh installations and updates

set -e  # Exit on any error

# Configuration
APP_NAME="orion-sphere-lrp"
APP_USER="orion-sphere"
APP_GROUP="orion-sphere"
APP_DIR="/opt/$APP_NAME"
SERVICE_FILE="$APP_NAME.service"
BACKUP_DIR="/opt/backups/$APP_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.10 or higher."
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MINOR -lt 10 ]]; then
        error "Python 3.10 or higher is required. Found: $PYTHON_VERSION"
    fi

    log "Python version: $PYTHON_VERSION ✓"

    # Check for required packages
    local required_packages=("git" "curl" "wget")
    for package in "${required_packages[@]}"; do
        if ! command -v $package &> /dev/null; then
            warn "$package is not installed. Installing..."
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y $package
            elif command -v yum &> /dev/null; then
                yum install -y $package
            elif command -v dnf &> /dev/null; then
                dnf install -y $package
            else
                error "Could not install $package. Please install it manually."
            fi
        fi
    done

    log "System requirements check completed ✓"
}

# Create application user and group
create_user() {
    log "Creating application user and group..."

    if ! getent group $APP_GROUP > /dev/null 2>&1; then
        groupadd $APP_GROUP
        log "Created group: $APP_GROUP"
    else
        log "Group $APP_GROUP already exists"
    fi

    if ! getent passwd $APP_USER > /dev/null 2>&1; then
        useradd -r -s /bin/false -g $APP_GROUP $APP_USER
        log "Created user: $APP_USER"
    else
        log "User $APP_USER already exists"
    fi
}

# Create application directory
create_app_directory() {
    log "Creating application directory..."

    if [[ ! -d "$APP_DIR" ]]; then
        mkdir -p "$APP_DIR"
        log "Created directory: $APP_DIR"
    else
        log "Directory $APP_DIR already exists"
    fi

    chown $APP_USER:$APP_GROUP "$APP_DIR"
    chmod 755 "$APP_DIR"
}

# Backup existing installation
backup_existing() {
    if [[ -d "$APP_DIR" ]] && [[ "$(ls -A $APP_DIR)" ]]; then
        log "Backing up existing installation..."

        mkdir -p "$BACKUP_DIR"
        local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
        local backup_path="$BACKUP_DIR/$backup_name"

        cp -r "$APP_DIR" "$backup_path"
        log "Backup created: $backup_path"

        # Keep only last 5 backups
        cd "$BACKUP_DIR"
        ls -t | tail -n +6 | xargs -r rm -rf
        log "Cleaned up old backups (kept last 5)"
    fi
}

# Deploy application files
deploy_files() {
    log "Deploying application files..."

    # Copy all files except .git directory
    rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' . "$APP_DIR/"

    # Set proper ownership
    chown -R $APP_USER:$APP_GROUP "$APP_DIR"

    # Set proper permissions
    find "$APP_DIR" -type f -exec chmod 644 {} \;
    find "$APP_DIR" -type d -exec chmod 755 {} \;
    chmod +x "$APP_DIR/wsgi.py"

    log "Application files deployed ✓"
}

# Set up virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."

    cd "$APP_DIR"

    # Remove existing venv if it exists
    if [[ -d "venv" ]]; then
        rm -rf venv
        log "Removed existing virtual environment"
    fi

    # Create new virtual environment
    sudo -u $APP_USER python3 -m venv venv
    log "Created virtual environment"

    # Upgrade pip
    sudo -u $APP_USER venv/bin/pip install --upgrade pip

    # Install dependencies
    log "Installing Python dependencies..."
    sudo -u $APP_USER venv/bin/pip install -r requirements.txt

    log "Virtual environment setup completed ✓"
}

# Install systemd service
install_service() {
    log "Installing systemd service..."

    # Copy service file
    cp "$SERVICE_FILE" /etc/systemd/system/
    chmod 644 /etc/systemd/system/"$SERVICE_FILE"

    # Reload systemd
    systemctl daemon-reload

    log "Systemd service installed ✓"
}

# Initialize database
init_database() {
    log "Initializing database..."

    cd "$APP_DIR"

    # Check if database exists
    if [[ ! -f "app.db" ]]; then
        log "Creating new database..."
        sudo -u $APP_USER venv/bin/flask db upgrade
        log "Database initialized ✓"
    else
        log "Database already exists, running migrations..."
        sudo -u $APP_USER venv/bin/flask db upgrade
        log "Database migrations completed ✓"
    fi
}

# Start and enable service
start_service() {
    log "Starting application service..."

    # Enable service
    systemctl enable "$APP_NAME"

    # Start service
    systemctl start "$APP_NAME"

    # Wait a moment for service to start
    sleep 3

    # Check service status
    if systemctl is-active --quiet "$APP_NAME"; then
        log "Service started successfully ✓"
    else
        error "Service failed to start. Check logs with: journalctl -u $APP_NAME -n 50"
    fi
}

# Display status information
show_status() {
    log "Deployment completed successfully!"
    echo
    echo "=== Deployment Summary ==="
    echo "Application Directory: $APP_DIR"
    echo "Service Name: $APP_NAME"
    echo "User: $APP_USER"
    echo "Group: $APP_GROUP"
    echo
    echo "=== Service Management ==="
    echo "Check status:     systemctl status $APP_NAME"
    echo "Start service:    systemctl start $APP_NAME"
    echo "Stop service:     systemctl stop $APP_NAME"
    echo "Restart service:  systemctl restart $APP_NAME"
    echo "View logs:        journalctl -u $APP_NAME -f"
    echo
    echo "=== Next Steps ==="
    echo "1. Create and configure $APP_DIR/.env with your production settings"
    echo "2. Restart the service: systemctl restart $APP_NAME"
    echo "3. Configure your web server (nginx/apache) to proxy to 127.0.0.1:5000"
    echo "4. Set up SSL certificates if needed"
    echo
    echo "=== Backup Location ==="
    echo "Backups are stored in: $BACKUP_DIR"
    echo
}

# Main deployment function
deploy() {
    log "Starting Orion Sphere LRP deployment..."

    check_root
    check_requirements
    create_user
    create_app_directory
    backup_existing
    deploy_files
    setup_venv
    install_service
    init_database
    start_service
    show_status
}

# Update function
update() {
    log "Starting Orion Sphere LRP update..."

    check_root

    # Stop service before update
    if systemctl is-active --quiet "$APP_NAME"; then
        log "Stopping service for update..."
        systemctl stop "$APP_NAME"
    fi

    backup_existing
    deploy_files
    setup_venv
    init_database

    # Start service after update
    log "Starting service after update..."
    systemctl start "$APP_NAME"

    if systemctl is-active --quiet "$APP_NAME"; then
        log "Update completed successfully! ✓"
    else
        error "Service failed to start after update. Check logs with: journalctl -u $APP_NAME -n 50"
    fi
}

# Show usage information
show_usage() {
    echo "Orion Sphere LRP Linux Deployment Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy    - Deploy a fresh installation"
    echo "  update    - Update an existing installation"
    echo "  status    - Show service status"
    echo "  logs      - Show service logs"
    echo "  backup    - Create a backup of current installation"
    echo "  help      - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy    # Fresh installation"
    echo "  $0 update    # Update existing installation"
    echo "  $0 status    # Check service status"
    echo
}

# Main script logic
case "${1:-}" in
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    status)
        systemctl status "$APP_NAME"
        ;;
    logs)
        journalctl -u "$APP_NAME" -f
        ;;
    backup)
        backup_existing
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
