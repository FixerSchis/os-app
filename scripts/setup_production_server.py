#!/usr/bin/env python3
"""
Production Server Setup Script

This script helps set up a Debian server for automated deployment of the OS App.
Run this script on your production server to prepare it for CD deployment.
"""

import os
import secrets
import string
import subprocess  # nosec
import sys
from pathlib import Path


def check_wsl_environment():
    """Check if we're running in WSL and exit if so."""
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            version_info = f.read()
            if "microsoft" in version_info.lower():
                print("❌ This script is not compatible with WSL (Windows Subsystem for Linux)")
                print("\nWSL does not support:")
                print("- systemd services (required for production deployment)")
                print("- proper SSL certificate management")
                print("- production-grade service management")
                print("\nFor development/testing in WSL, use:")
                print("- python3 scripts/test_wsl_setup.py (for testing)")
                print("- python3 scripts/start_wsl_app.py (for running the app)")
                print("\nFor production deployment, use a real Linux server or VM.")
                sys.exit(1)


def run_command(command, check=True, capture_output=False):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=capture_output, text=True  # nosec
        )
        if capture_output:
            return result.stdout.strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        if check:
            sys.exit(1)
        return None


def check_system_requirements():
    """Check system requirements."""
    print("Checking system requirements...")

    # Check OS
    if os.path.exists("/etc/debian_version"):
        with open("/etc/debian_version", "r") as f:
            debian_version = f.read().strip()
        print(f"✅ Debian version: {debian_version}")
    else:
        print("Warning: This script is designed for Debian/Ubuntu systems")

    # Check Python - try multiple commands
    python_commands = ["python3", "python"]
    python_found = False

    for cmd in python_commands:
        python_version_result = run_command(f"{cmd} --version", capture_output=True, check=False)
        if (
            python_version_result
            and hasattr(python_version_result, "returncode")
            and python_version_result.returncode == 0
        ):
            print(f"✅ Python: {python_version_result.stdout.strip()}")
            python_found = True
            break

    if not python_found:
        print("❌ Python3 not found")
        print("Installing Python3...")
        run_command("sudo apt update")
        run_command("sudo apt install -y python3 python3-pip python3-venv")
        return True  # Continue anyway

    # Check required packages
    required_packages = ["python3-venv", "python3-pip", "nginx", "git"]
    missing_packages = []

    for package in required_packages:
        result = run_command(f"dpkg -l | grep -q {package}", check=False)
        if result and result.returncode != 0:
            missing_packages.append(package)

    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        run_command("sudo apt update")
        for package in missing_packages:
            run_command(f"sudo apt install -y {package}")
    else:
        print("✅ All required packages are installed")

    return True


def create_deployment_user():
    """Create a deployment user."""
    print("Setting up deployment user...")

    username = input("Enter deployment username (default: os-app): ").strip() or "os-app"

    # Check if user exists
    result = run_command(f"id {username}", check=False)
    if result and result.returncode == 0:
        print(f"✅ User {username} already exists")
        return username

    # Create user with proper group handling
    print(f"Creating user {username}...")

    # First try to create user normally
    result = run_command(f"sudo useradd -m -s /bin/bash {username}", check=False)

    if result and result.returncode != 0:
        # If that fails, try with existing group
        print("User creation failed, trying with existing group...")
        result = run_command(f"sudo useradd -m -s /bin/bash -g {username} {username}", check=False)

        if result and result.returncode != 0:
            # If still fails, try without group specification
            print("Trying without group specification...")
            result = run_command(f"sudo useradd -m -s /bin/bash {username}", check=False)

    if result and result.returncode == 0:
        # Add to sudo group
        run_command(f"sudo usermod -aG sudo {username}", check=False)
        print(f"✅ Created user: {username}")
        return username
    else:
        print(f"❌ Failed to create user {username}")
        print("You may need to create the user manually:")
        print(f"sudo useradd -m -s /bin/bash {username}")
        print(f"sudo usermod -aG sudo {username}")
        return None


def setup_directories():
    """Set up necessary directories."""
    print("Setting up directories...")

    directories = ["/opt/os-app", "/opt/backups/os-app", "/var/log/os-app"]

    for directory in directories:
        run_command(f"sudo mkdir -p {directory}")
        run_command(f"sudo chown {os.getenv('USER')}:{os.getenv('USER')} {directory}")
        print(f"Created directory: {directory}")


def get_env_variables():
    """Get environment variables from user input or existing .env file."""
    print("Setting up environment variables...")

    env_path = "/opt/os-app/.env"
    existing_env = {}

    # Read existing .env file if it exists
    if os.path.exists(env_path):
        print("Found existing .env file. Reading current values...")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_env[key] = value

    # Default values
    defaults = {
        "SECRET_KEY": "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        ),
        "MAIL_SERVER": "smtp.gmail.com",
        "MAIL_USERNAME": "",
        "MAIL_PASSWORD": "",
    }

    env_vars = {}

    # Prompt for each variable
    for var_name, default_value in defaults.items():
        current_value = existing_env.get(var_name, default_value)

        if var_name == "SECRET_KEY":
            if current_value and current_value != default_value:
                print(f"Current {var_name}: [HIDDEN] (press Enter to keep current)")
            else:
                print(f"Current {var_name}: [GENERATED] (press Enter to keep current)")
        else:
            if current_value:
                print(f"Current {var_name}: {current_value} (press Enter to keep current)")
            else:
                print(f"Current {var_name}: [NOT SET] (press Enter to skip)")

        user_input = input(f"Enter new {var_name}: ").strip()

        if user_input:
            env_vars[var_name] = user_input
        elif current_value:
            env_vars[var_name] = current_value
        elif var_name == "SECRET_KEY":
            env_vars[var_name] = current_value  # Use generated default

    return env_vars


def setup_nginx(port, use_ssl=False, domain=None):
    """Set up Nginx configuration."""
    print("Setting up Nginx...")

    # Ask for port
    if not port:
        port = input("Enter application port (default: 8000): ").strip() or "8000"

    # Ask about SSL
    if use_ssl is None:
        ssl_choice = input("Enable SSL/HTTPS? (y/N): ").strip().lower()
        use_ssl = ssl_choice in ["y", "yes"]

    # Ask for domain if SSL is enabled
    if use_ssl and not domain:
        domain = input("Enter your domain name: ").strip()
        if not domain:
            print("Domain required for SSL. Disabling SSL.")
            use_ssl = False
        elif domain.lower() in ["localhost", "127.0.0.1"]:
            print("SSL cannot be used with localhost. Disabling SSL.")
            use_ssl = False

    # Create non-SSL config first (we'll update it later if SSL is enabled)
    nginx_config = f"""
server {{
    listen 80;
    server_name _;  # Accept all domains

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

    location /data {{
        alias /opt/os-app/data;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}
"""

    # Create Nginx config
    config_path = "/etc/nginx/sites-available/os-app"
    with open("/tmp/os-app-nginx.conf", "w") as f:  # nosec
        f.write(nginx_config)

    run_command(f"sudo cp /tmp/os-app-nginx.conf {config_path}")
    run_command(f"sudo ln -sf {config_path} /etc/nginx/sites-enabled/")

    # Test Nginx config
    nginx_test = run_command("sudo nginx -t", check=False, capture_output=True)
    if nginx_test and hasattr(nginx_test, "returncode") and nginx_test.returncode == 0:
        print("✅ Nginx configuration test passed")
        # Only try to reload if systemd is available
        systemctl_check = run_command("which systemctl", check=False, capture_output=True)
        if (
            systemctl_check
            and hasattr(systemctl_check, "returncode")
            and systemctl_check.returncode == 0
        ):
            run_command("sudo systemctl reload nginx", check=False)
    else:
        print("❌ Nginx configuration test failed")
        if nginx_test and hasattr(nginx_test, "stderr"):
            print(f"Error: {nginx_test.stderr}")
        return port, False, domain

    print("Nginx configuration created.")
    return port, use_ssl, domain


def setup_ssl(domain):
    """Set up SSL with Let's Encrypt."""
    if not domain:
        print("No domain provided. Skipping SSL setup.")
        return False

    print(f"Setting up SSL for {domain}...")

    # Install certbot
    run_command("sudo apt update")
    run_command("sudo apt install -y certbot python3-certbot-nginx")

    # Get SSL certificate
    result = run_command(f"sudo certbot --nginx -d {domain}", check=False)

    if result.returncode == 0:
        print(f"SSL certificate obtained for {domain}")
        return True
    else:
        print(f"Failed to obtain SSL certificate for {domain}")
        return False


def generate_ssh_key():
    """Generate SSH key for GitHub Actions."""
    print("Generating SSH key for deployment...")

    key_path = os.path.expanduser("~/.ssh/os-app-deploy")

    if os.path.exists(key_path):
        print(f"SSH key already exists at {key_path}")
    else:
        run_command(f"ssh-keygen -t ed25519 -f {key_path} -N ''")
        print(f"SSH key generated at {key_path}")

    # Display public key
    public_key_result = run_command(f"cat {key_path}.pub", capture_output=True)
    if public_key_result and hasattr(public_key_result, "stdout"):
        print("\n" + "=" * 50)
        print("SSH PUBLIC KEY FOR GITHUB SECRETS")
        print("=" * 50)
        print(public_key_result.stdout.strip())
        print("=" * 50)
        print("\nAdd this public key to your GitHub repository secrets as DEPLOY_SSH_KEY")
    else:
        print("❌ Failed to read SSH public key")


def create_env_file(env_vars, port):
    """Create the .env file with user-provided values."""
    print("Creating .env file...")

    env_template = f"""# Database Configuration
DATABASE_URL=sqlite:///os_app.db
# For PostgreSQL: postgresql://username:password@localhost/os_app

# Flask Configuration
SECRET_KEY={env_vars.get('SECRET_KEY', 'your-secret-key-here')}
FLASK_ENV=production
FLASK_APP=app.py

# Email Configuration
MAIL_SERVER={env_vars.get('MAIL_SERVER', 'smtp.gmail.com')}
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME={env_vars.get('MAIL_USERNAME', 'your-email@gmail.com')}
MAIL_PASSWORD={env_vars.get('MAIL_PASSWORD', 'your-app-password')}

# Security
WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=False
REMEMBER_COOKIE_SECURE=False

# Application Settings
UPLOAD_FOLDER=/opt/os-app/uploads
MAX_CONTENT_LENGTH=16777216

# Server Configuration
HOST=0.0.0.0
PORT={port}
"""

    env_path = "/opt/os-app/.env"
    with open(env_path, "w") as f:
        f.write(env_template)

    print(f"Created .env file at {env_path}")


def create_systemd_service(port):
    """Create systemd service file."""
    print("Creating systemd service...")

    service_content = f"""[Unit]
Description=OS App Flask Application
After=network.target

[Service]
Type=simple
User=os-app
WorkingDirectory=/opt/os-app
Environment=PATH=/opt/os-app/venv/bin
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
ExecStart=/opt/os-app/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:{port} app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/os-app.service"
    with open("/tmp/os-app.service", "w") as f:  # nosec
        f.write(service_content)

    run_command(f"sudo cp /tmp/os-app.service {service_path}")

    # Only try systemctl commands if systemd is available
    systemctl_check = run_command("which systemctl", check=False, capture_output=True)
    if (
        systemctl_check
        and hasattr(systemctl_check, "returncode")
        and systemctl_check.returncode == 0
    ):
        run_command("sudo systemctl daemon-reload", check=False)
        run_command("sudo systemctl enable os-app", check=False)
        print("Systemd service created and enabled.")
    else:
        print("⚠️  Systemd service file created (systemd not available in WSL)")


def main():
    """Main setup function."""
    print("OS App Production Server Setup")
    print("=" * 40)

    # Check WSL environment first
    check_wsl_environment()

    # Check system requirements
    check_system_requirements()

    # Create deployment user
    username = create_deployment_user()

    # Setup directories
    setup_directories()

    # Get environment variables
    env_vars = get_env_variables()

    # Setup Nginx
    port, use_ssl, domain = setup_nginx(port=None, use_ssl=None, domain=None)

    # Setup SSL (optional)
    if use_ssl:
        setup_ssl(domain)

    # Generate SSH key
    generate_ssh_key()

    # Create env file
    create_env_file(env_vars, port)

    # Create systemd service
    create_systemd_service(port)

    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Add the SSH public key to your GitHub repository secrets")
    print("2. Add the following secrets to your GitHub repository:")
    print("   - DEPLOY_HOST: Your server's IP address or domain")
    print(f"   - DEPLOY_USER: {username}")
    print("   - DEPLOY_SSH_KEY: The private SSH key content")
    print("   - DEPLOY_PORT: SSH port (default: 22)")
    print(f"3. The application will run on port {port}")
    if use_ssl:
        print(f"4. SSL is enabled for domain: {domain}")
    else:
        print("4. SSL is disabled (development mode)")
    print("5. Push to master to trigger your first deployment!")


if __name__ == "__main__":
    main()
