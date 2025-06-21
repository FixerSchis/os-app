#!/usr/bin/env python3
"""
Development environment setup script for OS App.
This script helps new collaborators set up their development environment quickly.
"""

import os
import shlex  # Add this import for safe splitting if needed
import subprocess  # nosec B404
import sys
import venv
from pathlib import Path


def run_command(command, check=True, capture_output=False):
    """Run a shell command and return the result."""
    try:
        # WARNING: Using shell=True can be dangerous if command comes from untrusted
        # input.
        # Consider using shlex.split(command) and shell=False for untrusted input.
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True,  # nosec B602
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        return None


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True

    print("Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
        print("✅ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def get_activate_command():
    """Get the appropriate activation command for the current OS."""
    if os.name == "nt":  # Windows
        return "venv\\Scripts\\activate"
    else:  # Unix-like
        return "source venv/bin/activate"


def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")

    # Install main dependencies
    result = run_command("pip install -r requirements.txt")
    if result is None or result.returncode != 0:
        print("❌ Failed to install main dependencies")
        return False

    # Install development dependencies
    result = run_command("pip install -r requirements-dev.txt")
    if result is None or result.returncode != 0:
        print("❌ Failed to install development dependencies")
        return False

    print("✅ Dependencies installed successfully")
    return True


def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("Setting up pre-commit hooks...")
    result = run_command("pre-commit install")
    if result is None or result.returncode != 0:
        print("❌ Failed to set up pre-commit hooks")
        return False

    print("✅ Pre-commit hooks installed successfully")
    return True


def create_env_file():
    """Create a .env file from template if it doesn't exist."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file already exists")
        return True

    # Create a basic .env file
    env_content = """# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///db/os_app.db

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Application Configuration
BASE_URL=http://localhost:5000
"""

    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created (please update with your actual values)")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def run_tests():
    """Run the test suite to verify setup."""
    print("Running tests to verify setup...")
    result = run_command("pytest --version")
    if result is None or result.returncode != 0:
        print("❌ pytest not available")
        return False

    result = run_command("pytest -v")
    if result is None or result.returncode != 0:
        print("❌ Some tests failed")
        return False

    print("✅ All tests passed")
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up OS App development environment...")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Set up pre-commit hooks
    if not setup_pre_commit():
        sys.exit(1)

    # Create .env file
    if not create_env_file():
        sys.exit(1)

    # Run tests
    if not run_tests():
        print("⚠️  Tests failed, but setup completed")

    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    print(f"   {get_activate_command()}")
    print("2. Update the .env file with your actual configuration")
    print("3. Run the application:")
    print("   python app.py")
    print("4. Visit http://localhost:5000 in your browser")
    print("\nFor more information, see CONTRIBUTING.md")


if __name__ == "__main__":
    main()
