#!/usr/bin/env python3
"""
Production server setup script for OS App.
This script sets up a production environment for the Flask application.
"""

import argparse
import os
import subprocess  # nosec
import sys
from pathlib import Path


def run_command(command, check=True, capture_output=False):
    """Run a shell command and return the result."""
    print(f"Running: {command}")

    if capture_output:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=True, text=True  # nosec
        )
        return result
    else:
        result = subprocess.run(command, shell=True, check=check)  # nosec
        return result


def check_requirements():
    """Check if system meets requirements."""
    print("Checking system requirements...")

    # Check if running as root
    if os.geteuid() == 0:
        print("❌ This script should not be run as root.")
        print("Please run as a regular user with sudo privileges.")
        sys.exit(1)

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required.")
        sys.exit(1)

    print(
        f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected"
    )

    # Check if sudo is available
    try:
        run_command("sudo -n true", check=False, capture_output=True)
        print("✅ Sudo privileges available")
    except subprocess.CalledProcessError:
        print("❌ Sudo privileges required but not available.")
        sys.exit(1)


def create_user():
    """Create the os-app user and group."""
    print("Creating os-app user and group...")

    # Create group if it doesn't exist
    try:
        run_command("sudo groupadd os-app", check=False)
        print("✅ Group 'os-app' created or already exists")
    except subprocess.CalledProcessError:
        print("⚠️  Group creation failed (may already exist)")

    # Create user if it doesn't exist
    try:
        run_command("sudo useradd -r -s /bin/false -g os-app os-app", check=False)
        print("✅ User 'os-app' created or already exists")
    except subprocess.CalledProcessError:
        print("⚠️  User creation failed (may already exist)")


def install_system_packages():
    """Install required system packages."""
    print("Installing system packages...")

    packages = [
        "python3",
        "python3-pip",
        "python3-venv",
        "nginx",
        "git",
        "curl",
        "wget",
        "unzip",
        "build-essential",
        "python3-dev",
        "libffi-dev",
        "libssl-dev",
        "libjpeg-dev",
        "libpng-dev",
        "libfreetype6-dev",
        "liblcms2-dev",
        "libwebp-dev",
        "libharfbuzz-dev",
        "libfribidi-dev",
        "libxcb1-dev",
        "pkg-config",
    ]

    # Update package list
    run_command("sudo apt update")

    # Install packages
    for package in packages:
        try:
            run_command(f"sudo apt install -y {package}")
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"⚠️  Failed to install {package}")


def setup_application_directory():
    """Set up the application directory."""
    print("Setting up application directory...")

    app_dir = "/opt/os-app"

    # Create directory
    run_command(f"sudo mkdir -p {app_dir}")

    # Set ownership
    run_command(f"sudo chown os-app:os-app {app_dir}")

    print("✅ Application directory created: {}".format(app_dir))


def setup_python_environment():
    """Set up Python virtual environment."""
    print("Setting up Python virtual environment...")

    app_dir = "/opt/os-app"

    # Create virtual environment
    run_command(f"sudo -u os-app python3 -m venv {app_dir}/venv")

    # Upgrade pip
    run_command(f"sudo -u os-app {app_dir}/venv/bin/pip install --upgrade pip")

    print("✅ Python virtual environment created")


def install_python_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")

    app_dir = "/opt/os-app"
    venv_pip = f"{app_dir}/venv/bin/pip"

    # Install dependencies
    run_command(f"sudo -u os-app {venv_pip} install gunicorn")
    run_command(f"sudo -u os-app {venv_pip} install -r requirements.txt")

    print("✅ Python dependencies installed")


def create_nginx_config(port):
    """Create Nginx configuration."""
    print("Creating Nginx configuration...")

    nginx_config = f"""server {{
    listen 80;
    server_name _;

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /static {{
        alias /opt/os-app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}

    location /favicon.ico {{
        alias /opt/os-app/static/images/favicon.ico;
        expires 30d;
    }}
}}
"""

    config_path = "/etc/nginx/sites-available/os-app"
    with open("/tmp/os-app-nginx", "w") as f:  # nosec
        f.write(nginx_config)

    run_command(f"sudo cp /tmp/os-app-nginx {config_path}")

    # Enable site
    run_command("sudo ln -sf /etc/nginx/sites-available/os-app /etc/nginx/sites-enabled/")

    # Remove default site if it exists
    run_command("sudo rm -f /etc/nginx/sites-enabled/default", check=False)

    # Test configuration
    try:
        run_command("sudo nginx -t")
        print("✅ Nginx configuration is valid")
    except subprocess.CalledProcessError:
        print("❌ Nginx configuration is invalid")
        sys.exit(1)


def create_systemd_service(port):
    """Create systemd service file."""
    print("Creating systemd service...")

    service_content = """[Unit]
Description=OS App Flask Application
After=network.target

[Service]
Type=simple
User=os-app
WorkingDirectory=/opt/os-app
Environment=PATH=/opt/os-app/venv/bin
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
ExecStart=/opt/os-app/venv/bin/gunicorn -c gunicorn.conf.py wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/os-app.service"
    with open("/tmp/os-app.service", "w") as f:  # nosec
        f.write(service_content)

    run_command(f"sudo cp /tmp/os-app.service {service_path}")
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl enable os-app")
    print("✅ Systemd service created and enabled")


def setup_ssl():
    """Set up SSL with Let's Encrypt (optional)."""
    print("Setting up SSL...")

    # Install certbot
    try:
        run_command("sudo apt install -y certbot python3-certbot-nginx")
        print("✅ Certbot installed")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install certbot")
        return

    print("ℹ️  To set up SSL, run: sudo certbot --nginx -d yourdomain.com")


def start_services():
    """Start the services."""
    print("Starting services...")

    # Start Nginx
    run_command("sudo systemctl start nginx")
    run_command("sudo systemctl enable nginx")
    print("✅ Nginx started and enabled")

    # Start the application
    run_command("sudo systemctl start os-app")
    print("✅ OS App service started")

    # Check status
    run_command("sudo systemctl status os-app", check=False)


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup OS App production server")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for the Flask application (default: 5000)"
    )
    parser.add_argument("--skip-ssl", action="store_true", help="Skip SSL setup")

    args = parser.parse_args()

    print("🚀 OS App Production Server Setup")
    print("=" * 50)

    try:
        check_requirements()
        create_user()
        install_system_packages()
        setup_application_directory()
        setup_python_environment()
        install_python_dependencies()
        create_nginx_config(args.port)
        create_systemd_service(args.port)

        if not args.skip_ssl:
            setup_ssl()

        start_services()

        print("\n🎉 Setup completed successfully!")
        print(f"📱 Application is running on port {args.port}")
        print("🌐 Access via: http://your-server-ip")
        print("📋 To check status: sudo systemctl status os-app")
        print("📋 To view logs: sudo journalctl -u os-app -f")

    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
