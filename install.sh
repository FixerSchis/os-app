#!/bin/bash

# Orion Sphere LRP Installation Script
# This script installs all dependencies and sets up the Flask application as a systemd service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="orion-sphere-lrp"
SERVICE_USER="orion-sphere"
SERVICE_GROUP="orion-sphere"

print_status "Starting Orion Sphere LRP installation..."
print_status "Installation directory: $SCRIPT_DIR"

# Function to install packages with error handling
install_packages() {
    local packages=("$@")
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        print_status "Attempting to install packages (attempt $((retry_count + 1))/$max_retries)..."
        
        if sudo apt install -y "${packages[@]}" 2>&1 | tee /tmp/apt_install.log; then
            print_success "Package installation successful"
            return 0
        else
            retry_count=$((retry_count + 1))
            print_warning "Package installation failed (attempt $retry_count/$max_retries)"
            
            if [ $retry_count -lt $max_retries ]; then
                print_status "Waiting 30 seconds before retry..."
                sleep 30
                
                # Try to fix repository issues
                print_status "Attempting to fix repository issues..."
                sudo apt clean
                sudo apt update --fix-missing || true
            fi
        fi
    done
    
    print_error "Failed to install packages after $max_retries attempts"
    print_error "Last error log:"
    cat /tmp/apt_install.log
    return 1
}

# Update package lists with error handling
print_status "Updating package lists..."
if ! sudo apt update 2>&1 | tee /tmp/apt_update.log; then
    print_warning "Package list update had issues, but continuing..."
    print_warning "This might be due to repository timing issues (common on Debian)"
    cat /tmp/apt_update.log
fi

# Install system dependencies
print_status "Installing system dependencies..."
PACKAGES=(
    python3
    python3-pip
    python3-venv
    python3-dev
    build-essential
    libffi-dev
    libssl-dev
    libxml2-dev
    libxslt1-dev
    libjpeg-dev
    libpng-dev
    libfreetype6-dev
    liblcms2-dev
    libwebp-dev
    libharfbuzz-dev
    libfribidi-dev
    libxcb1-dev
    libpango1.0-dev
    libcairo2-dev
    libgdk-pixbuf2.0-dev
    libgtk-3-dev
    libgirepository1.0-dev
    nginx
    supervisor
    sqlite3
)

if ! install_packages "${PACKAGES[@]}"; then
    print_error "Failed to install system dependencies"
    print_error "Please check your internet connection and try again"
    print_error "You may also need to wait for repository timing issues to resolve"
    exit 1
fi

# Create service user and group
print_status "Creating service user and group..."
if ! getent group $SERVICE_GROUP > /dev/null 2>&1; then
    sudo groupadd $SERVICE_GROUP
    print_success "Created group: $SERVICE_GROUP"
else
    print_warning "Group $SERVICE_GROUP already exists"
fi

if ! getent passwd $SERVICE_USER > /dev/null 2>&1; then
    sudo useradd -r -g $SERVICE_GROUP -s /bin/bash -d $SCRIPT_DIR $SERVICE_USER
    print_success "Created user: $SERVICE_USER"
else
    print_warning "User $SERVICE_USER already exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
sudo mkdir -p /var/log/$APP_NAME
sudo mkdir -p /var/run/$APP_NAME
sudo mkdir -p /etc/$APP_NAME

# Set ownership
sudo chown -R $SERVICE_USER:$SERVICE_GROUP /var/log/$APP_NAME
sudo chown -R $SERVICE_USER:$SERVICE_GROUP /var/run/$APP_NAME
sudo chown -R $SERVICE_USER:$SERVICE_GROUP /etc/$APP_NAME

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    if python3 -m venv "$SCRIPT_DIR/venv"; then
        print_success "Created virtual environment"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
else
    print_warning "Virtual environment already exists"
fi

# Verify virtual environment was created
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    print_error "Virtual environment activation script not found"
    print_error "Virtual environment may not have been created properly"
    exit 1
fi

# Activate virtual environment and install Python dependencies
print_status "Installing Python dependencies..."
if source "$SCRIPT_DIR/venv/bin/activate"; then
    print_success "Virtual environment activated"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Verify pip is available
if ! command -v pip &> /dev/null; then
    print_error "pip not found in virtual environment"
    exit 1
fi

pip install --upgrade pip

# Install Python packages with retry logic
MAX_PIP_RETRIES=3
PIP_RETRY_COUNT=0

while [ $PIP_RETRY_COUNT -lt $MAX_PIP_RETRIES ]; do
    print_status "Installing Python packages (attempt $((PIP_RETRY_COUNT + 1))/$MAX_PIP_RETRIES)..."
    
    if pip install -r "$SCRIPT_DIR/requirements.txt" 2>&1 | tee /tmp/pip_install.log; then
        print_success "Python packages installed successfully"
        break
    else
        PIP_RETRY_COUNT=$((PIP_RETRY_COUNT + 1))
        print_warning "Python package installation failed (attempt $PIP_RETRY_COUNT/$MAX_PIP_RETRIES)"
        
        if [ $PIP_RETRY_COUNT -lt $MAX_PIP_RETRIES ]; then
            print_status "Waiting 30 seconds before retry..."
            sleep 30
        fi
    fi
done

if [ $PIP_RETRY_COUNT -eq $MAX_PIP_RETRIES ]; then
    print_error "Failed to install Python packages after $MAX_PIP_RETRIES attempts"
    print_error "Last error log:"
    cat /tmp/pip_install.log
    exit 1
fi

# Create database directory if it doesn't exist
print_status "Setting up database directory..."
mkdir -p "$SCRIPT_DIR/db"
sudo chown -R $SERVICE_USER:$SERVICE_GROUP "$SCRIPT_DIR/db"

# Create local configuration file
print_status "Creating local configuration file..."
if [ ! -f "$SCRIPT_DIR/config/local.py" ]; then
    cat > "$SCRIPT_DIR/config/local.py" << EOF
import os
from config import Config

class LocalConfig(Config):
    # Override default configuration for local environment
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATABASE_PATH = os.path.join(basedir, 'db')
    DATABASE_FILE_NAME = "oslrp.db"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(DATABASE_PATH, DATABASE_FILE_NAME)}'
    
    # Server configuration
    DEFAULT_PORT = 5000
    
    # Email configuration - update these with your actual email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.example.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@example.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'Orion Sphere LRP <no-reply@example.com>'
    
    # Application configuration
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
EOF
    print_success "Created local configuration file"
else
    print_warning "Local configuration file already exists"
fi

# Create WSGI entry point
print_status "Creating WSGI entry point..."
cat > "$SCRIPT_DIR/wsgi.py" << EOF
#!/usr/bin/env python3
"""
WSGI entry point for Orion Sphere LRP
"""
import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import create_app

# Create the Flask application
application = create_app()

if __name__ == "__main__":
    application.run()
EOF

# Make WSGI file executable
chmod +x "$SCRIPT_DIR/wsgi.py"

# Create systemd service file
print_status "Creating systemd service file..."
sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=Orion Sphere LRP Flask Application
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/venv/bin
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
ExecStart=$SCRIPT_DIR/venv/bin/python wsgi.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$SCRIPT_DIR /var/log/$APP_NAME /var/run/$APP_NAME

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
print_status "Creating nginx configuration..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Logs
    access_log /var/log/nginx/$APP_NAME_access.log;
    error_log /var/log/nginx/$APP_NAME_error.log;

    # Static files
    location /static/ {
        alias $SCRIPT_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable nginx site
print_status "Enabling nginx site..."
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Set proper permissions
print_status "Setting proper permissions..."
sudo chown -R $SERVICE_USER:$SERVICE_GROUP "$SCRIPT_DIR"
sudo chmod -R 755 "$SCRIPT_DIR"
sudo chmod 644 "$SCRIPT_DIR/config/local.py"

# Initialize database (if needed)
print_status "Initializing database..."
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/venv/bin/python" -c "
from app import create_app
from models.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"

# Reload systemd and enable services
print_status "Reloading systemd and enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl enable nginx

# Start services
print_status "Starting services..."
sudo systemctl start $APP_NAME
sudo systemctl start nginx

# Check service status
print_status "Checking service status..."
if sudo systemctl is-active --quiet $APP_NAME; then
    print_success "Orion Sphere LRP service is running"
else
    print_error "Failed to start Orion Sphere LRP service"
    sudo systemctl status $APP_NAME
    exit 1
fi

if sudo systemctl is-active --quiet nginx; then
    print_success "Nginx service is running"
else
    print_error "Failed to start nginx service"
    sudo systemctl status nginx
    exit 1
fi

# Display final information
print_success "Installation completed successfully!"
echo ""
echo "=== Orion Sphere LRP Installation Summary ==="
echo "Application URL: http://localhost"
echo "Service name: $APP_NAME"
echo "Service user: $SERVICE_USER"
echo "Installation directory: $SCRIPT_DIR"
echo ""
echo "=== Useful Commands ==="
echo "Check service status: sudo systemctl status $APP_NAME"
echo "View service logs: sudo journalctl -u $APP_NAME -f"
echo "Restart service: sudo systemctl restart $APP_NAME"
echo "Stop service: sudo systemctl stop $APP_NAME"
echo ""
echo "=== Next Steps ==="
echo "1. Update the email configuration in $SCRIPT_DIR/config/local.py"
echo "2. Change the SECRET_KEY in the configuration file"
echo "3. Set up SSL/TLS certificates for production use"
echo "4. Configure your firewall to allow HTTP/HTTPS traffic"
echo ""
print_warning "Remember to change the default secret key and email settings before going to production!" 