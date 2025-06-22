#!/usr/bin/env python3
"""
WSL Debian Setup Test Script

This script tests the production server setup on WSL Debian.
It runs the setup with predefined test values and verifies the configuration.
"""

import os
import subprocess  # nosec
import sys
import time
from pathlib import Path


def run_command(command, check=True, capture_output=False, timeout=30):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,  # nosec
            check=check,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {command}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        if check:
            return None
        return e
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def check_wsl_environment():
    """Check if we're running in WSL."""
    print("Checking WSL environment...")

    # Check if we're in WSL
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            version_info = f.read()
            if "microsoft" in version_info.lower():
                print("✅ Running in WSL")
                return True
            else:
                print("⚠️  Not running in WSL (but that's okay)")
                return False

    return False


def check_system_requirements():
    """Check system requirements."""
    print("\nChecking system requirements...")

    # Check OS
    if os.path.exists("/etc/debian_version"):
        with open("/etc/debian_version", "r") as f:
            debian_version = f.read().strip()
        print(f"✅ Debian version: {debian_version}")
    else:
        print("❌ Not running Debian/Ubuntu")
        return False

    # Check Python
    python_version_result = run_command("python3 --version", capture_output=True)
    if python_version_result and hasattr(python_version_result, "stdout"):
        print(f"✅ Python: {python_version_result.stdout.strip()}")
    else:
        print("❌ Python3 not found")
        return False

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


def create_test_user():
    """Create a test user for deployment."""
    print("\nSetting up test user...")

    username = "os-app-test"

    # Check if user exists
    result = run_command(f"id {username}", check=False)
    if result and result.returncode == 0:
        print(f"✅ User {username} already exists")
        return username

    # Create user
    result = run_command(f"sudo useradd -m -s /bin/bash {username}")
    if result:
        run_command(f"sudo usermod -aG sudo {username}")
        print(f"✅ Created user: {username}")
        return username
    else:
        print(f"❌ Failed to create user {username}")
        return None


def setup_test_directories():
    """Set up test directories."""
    print("\nSetting up test directories...")

    directories = ["/opt/os-app-test", "/opt/backups/os-app-test", "/var/log/os-app-test"]

    for directory in directories:
        run_command(f"sudo mkdir -p {directory}")
        run_command(f"sudo chown {os.getenv('USER')}:{os.getenv('USER')} {directory}")
        print(f"✅ Created directory: {directory}")


def test_nginx_configuration():
    """Test Nginx configuration."""
    print("\nTesting Nginx configuration...")

    # Create a simple test config
    test_config = """
server {
    listen 8080;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

    config_path = "/etc/nginx/sites-available/os-app-test"

    # Create the config file in /tmp first
    with open("/tmp/os-app-test-nginx.conf", "w") as f:  # nosec
        f.write(test_config)

    result = run_command(f"sudo cp /tmp/os-app-test-nginx.conf {config_path}")
    if result:
        run_command(f"sudo ln -sf {config_path} /etc/nginx/sites-enabled/")
        nginx_test = run_command("sudo nginx -t", capture_output=True)
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
            return True
        else:
            print("❌ Nginx configuration test failed")
            if nginx_test and hasattr(nginx_test, "stdout"):
                print(f"Error: {nginx_test.stdout}")
            return False
    else:
        print("❌ Failed to create Nginx configuration")
        return False


def test_systemd_service():
    """Test systemd service creation."""
    print("\nTesting systemd service...")

    service_content = """[Unit]
Description=OS App Test Flask Application
After=network.target

[Service]
Type=simple
User=os-app-test
WorkingDirectory=/opt/os-app-test
Environment=PATH=/opt/os-app-test/venv/bin
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
ExecStart=/opt/os-app-test/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/os-app-test.service"
    with open("/tmp/os-app-test.service", "w") as f:  # nosec
        f.write(service_content)

    result = run_command(f"sudo cp /tmp/os-app-test.service {service_path}")
    if result:
        # Only try systemctl commands if systemd is available
        systemctl_check = run_command("which systemctl", check=False, capture_output=True)
        if (
            systemctl_check
            and hasattr(systemctl_check, "returncode")
            and systemctl_check.returncode == 0
        ):
            run_command("sudo systemctl daemon-reload", check=False)
            run_command("sudo systemctl enable os-app-test", check=False)
            print("✅ Systemd service created and enabled")
        else:
            print("⚠️  Systemd service file created (systemd not available in WSL)")
        return True
    else:
        print("❌ Failed to create systemd service")
        return False


def test_ssh_key_generation():
    """Test SSH key generation."""
    print("\nTesting SSH key generation...")

    key_path = os.path.expanduser("~/.ssh/os-app-test-deploy")

    if os.path.exists(key_path):
        print(f"✅ SSH key already exists at {key_path}")
        return True

    result = run_command(f"ssh-keygen -t ed25519 -f {key_path} -N ''")
    if result:
        public_key_result = run_command(f"cat {key_path}.pub", capture_output=True)
        if public_key_result and hasattr(public_key_result, "stdout"):
            print("✅ SSH key generated successfully")
            print(f"Public key: {public_key_result.stdout.strip()[:50]}...")
            return True

    print("❌ Failed to generate SSH key")
    return False


def create_test_env_file():
    """Create a test .env file."""
    print("\nCreating test .env file...")

    env_content = """# Test Environment Configuration
DATABASE_URL=sqlite:///os_app_test.db

# Flask Configuration
SECRET_KEY=test-secret-key-for-wsl-testing-only
FLASK_ENV=production
FLASK_APP=app.py

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=test@example.com
MAIL_PASSWORD=test-password

# Security
WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=False
REMEMBER_COOKIE_SECURE=False

# Application Settings
UPLOAD_FOLDER=/opt/os-app-test/uploads
MAX_CONTENT_LENGTH=16777216

# Server Configuration
HOST=0.0.0.0
PORT=8000
"""

    env_path = "/opt/os-app-test/.env"
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"✅ Created test .env file at {env_path}")
    return True


def test_python_environment():
    """Test Python virtual environment setup."""
    print("\nTesting Python environment...")

    test_dir = "/opt/os-app-test"

    # Create virtual environment
    result = run_command(f"cd {test_dir} && python3 -m venv venv")
    if not result:
        print("❌ Failed to create virtual environment")
        return False

    # Test pip install (use . instead of source for WSL compatibility)
    result = run_command(f"cd {test_dir} && . venv/bin/activate && pip install --upgrade pip")
    if not result:
        print("❌ Failed to upgrade pip")
        return False

    print("✅ Python virtual environment created successfully")
    return True


def run_integration_tests():
    """Run integration tests."""
    print("\nRunning integration tests...")

    tests = [
        ("Check test directories exist", "ls -la /opt/os-app-test"),
        ("Check test user exists", "id os-app-test"),
        ("Check SSH key exists", "ls -la ~/.ssh/os-app-test-deploy*"),
        ("Check .env file exists", "ls -la /opt/os-app-test/.env"),
        ("Check systemd service exists", "ls -la /etc/systemd/system/os-app-test.service"),
    ]

    # Only test Nginx if it's available
    nginx_check = run_command("which nginx", check=False, capture_output=True)
    if nginx_check and hasattr(nginx_check, "returncode") and nginx_check.returncode == 0:
        tests.insert(0, ("Check Nginx status", "sudo systemctl is-active nginx"))

    passed = 0
    total = len(tests)

    for test_name, command in tests:
        try:
            result = run_command(command, check=False, capture_output=True)
            if result and hasattr(result, "returncode") and result.returncode == 0:
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}")
                if result and hasattr(result, "stderr") and result.stderr:
                    print(f"  Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ {test_name}: {e}")

    print(f"\nIntegration tests: {passed}/{total} passed")
    return passed == total


def cleanup_test_environment():
    """Clean up test environment."""
    print("\nCleaning up test environment...")

    # Only try systemctl commands if systemd is available
    if run_command("which systemctl", check=False, capture_output=True):
        run_command("sudo systemctl stop os-app-test", check=False)
        run_command("sudo systemctl disable os-app-test", check=False)
        run_command("sudo systemctl daemon-reload", check=False)

    # Remove service file
    run_command("sudo rm -f /etc/systemd/system/os-app-test.service", check=False)

    # Remove Nginx config
    run_command("sudo rm -f /etc/nginx/sites-enabled/os-app-test", check=False)
    run_command("sudo rm -f /etc/nginx/sites-available/os-app-test", check=False)

    # Test Nginx config and reload if systemd is available
    nginx_test = run_command("sudo nginx -t", check=False, capture_output=True)
    if nginx_test and hasattr(nginx_test, "returncode") and nginx_test.returncode == 0:
        if run_command("which systemctl", check=False, capture_output=True):
            run_command("sudo systemctl reload nginx", check=False)

    # Remove directories
    run_command("sudo rm -rf /opt/os-app-test", check=False)
    run_command("sudo rm -rf /opt/backups/os-app-test", check=False)
    run_command("sudo rm -rf /var/log/os-app-test", check=False)

    # Remove test user
    run_command("sudo userdel -r os-app-test", check=False)

    # Remove SSH key
    run_command("rm -f ~/.ssh/os-app-test-deploy*", check=False)

    print("✅ Test environment cleaned up")


def main():
    """Main test function."""
    print("WSL Debian Setup Test")
    print("=" * 50)

    # Check if we're in WSL
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            version_info = f.read()
            if "microsoft" in version_info.lower():
                print("✅ Running in WSL - this test is designed for WSL environments")
            else:
                print("⚠️  Not running in WSL - this test is designed for WSL environments")
                print("For production testing, use the production setup script instead.")
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response not in ["y", "yes"]:
                    print("Test cancelled.")
                    return
    else:
        print("⚠️  Could not detect WSL environment")

    # Check if user wants to run tests
    response = (
        input("This will test the production server setup. Continue? (y/N): ").strip().lower()
    )
    if response not in ["y", "yes"]:
        print("Test cancelled.")
        return

    try:
        # Run tests
        wsl_check = check_wsl_environment()
        system_check = check_system_requirements()

        if not system_check:
            print("❌ System requirements not met. Exiting.")
            return

        user_created = create_test_user()
        if not user_created:
            print("❌ Failed to create test user. Exiting.")
            return

        setup_test_directories()
        nginx_ok = test_nginx_configuration()
        service_ok = test_systemd_service()
        ssh_ok = test_ssh_key_generation()
        env_ok = create_test_env_file()
        python_ok = test_python_environment()

        # Run integration tests
        integration_ok = run_integration_tests()

        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"WSL Environment: {'✅' if wsl_check else '⚠️'}")
        print(f"System Requirements: {'✅' if system_check else '❌'}")
        print(f"Test User: {'✅' if user_created else '❌'}")
        print(f"Nginx Configuration: {'✅' if nginx_ok else '❌'}")
        print(f"Systemd Service: {'✅' if service_ok else '❌'}")
        print(f"SSH Key Generation: {'✅' if ssh_ok else '❌'}")
        print(f"Environment File: {'✅' if env_ok else '❌'}")
        print(f"Python Environment: {'✅' if python_ok else '❌'}")
        print(f"Integration Tests: {'✅' if integration_ok else '❌'}")

        if integration_ok:
            print("\n🎉 All tests passed! The setup script should work correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")

        # Ask about cleanup
        cleanup = input("\nClean up test environment? (y/N): ").strip().lower()
        if cleanup in ["y", "yes"]:
            cleanup_test_environment()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        cleanup_test_environment()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup_test_environment()


if __name__ == "__main__":
    main()
