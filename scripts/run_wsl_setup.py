#!/usr/bin/env python3
"""
WSL Setup Runner

This script runs the production server setup with predefined test values
for testing in WSL environment.
"""

import os
import subprocess  # nosec
import sys
from pathlib import Path


def run_setup_with_test_values():
    """Run the setup script with test values."""
    print("WSL Production Setup Test")
    print("=" * 40)

    # Test values for WSL environment
    test_values = {
        "username": "os-app",
        "port": "8000",
        "use_ssl": False,
        "domain": None,
        "secret_key": "test-secret-key-for-wsl-testing-only",
        "mail_server": "smtp.gmail.com",
        "mail_username": "test@example.com",
        "mail_password": "test-password",
    }

    print("Using test values:")
    for key, value in test_values.items():
        if key == "mail_password":
            print(f"  {key}: [HIDDEN]")
        else:
            print(f"  {key}: {value}")

    print("\nStarting setup...")

    # Check if setup script exists
    setup_script = Path(__file__).parent / "setup_production_server.py"
    if not setup_script.exists():
        print(f"❌ Setup script not found: {setup_script}")
        return False

    # Make script executable
    os.chmod(setup_script, 0o755)  # nosec

    # Run the setup script
    try:
        result = subprocess.run(
            [sys.executable, str(setup_script)],  # nosec
            input=f"{test_values['username']}\n"
            f"{test_values['secret_key']}\n"
            f"{test_values['mail_server']}\n"
            f"{test_values['mail_username']}\n"
            f"{test_values['mail_password']}\n"
            f"{test_values['port']}\n"
            f"n\n",  # No SSL
            text=True,
            capture_output=False,
        )

        if result.returncode == 0:
            print("\n✅ Setup completed successfully!")
            return True
        else:
            print(f"\n❌ Setup failed with return code: {result.returncode}")
            return False

    except Exception as e:
        print(f"\n❌ Error running setup: {e}")
        return False


def verify_setup():
    """Verify the setup was successful."""
    print("\nVerifying setup...")

    checks = [
        ("Check if user exists", "id os-app"),
        ("Check if directories exist", "ls -la /opt/os-app"),
        ("Check if .env file exists", "ls -la /opt/os-app/.env"),
        ("Check if SSH key exists", "ls -la ~/.ssh/os-app-deploy*"),
        ("Check if Nginx config exists", "ls -la /etc/nginx/sites-enabled/os-app"),
        ("Check if systemd service exists", "ls -la /etc/systemd/system/os-app.service"),
    ]

    passed = 0
    total = len(checks)

    for check_name, command in checks:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)  # nosec
            if result.returncode == 0:
                print(f"✅ {check_name}")
                passed += 1
            else:
                print(f"❌ {check_name}")
        except Exception as e:
            print(f"❌ {check_name}: {e}")

    print(f"\nVerification: {passed}/{total} checks passed")
    return passed == total


def main():
    """Main function."""
    print("This will run the production server setup with test values.")
    print("Make sure you have sudo privileges.")

    response = input("Continue? (y/N): ").strip().lower()
    if response not in ["y", "yes"]:
        print("Setup cancelled.")
        return

    # Run setup
    success = run_setup_with_test_values()

    if success:
        # Verify setup
        verify_setup()

        print("\n" + "=" * 50)
        print("SETUP COMPLETE!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Check the SSH public key that was generated")
        print("2. Add it to your GitHub repository secrets")
        print("3. Test the deployment by pushing to master")
        print("\nTo clean up later, run:")
        print("  sudo userdel -r os-app")
        print("  sudo rm -rf /opt/os-app /opt/backups/os-app /var/log/os-app")
        print("  sudo rm -f /etc/nginx/sites-enabled/os-app /etc/nginx/sites-available/os-app")
        print("  sudo rm -f /etc/systemd/system/os-app.service")
    else:
        print("\n❌ Setup failed. Check the output above for errors.")


if __name__ == "__main__":
    main()
