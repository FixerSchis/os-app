#!/usr/bin/env python3
"""
Development Environment Setup Script

This script helps set up the local development environment with all necessary
tools, dependencies, and pre-commit hooks.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description, check=True):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")


def check_virtual_environment():
    """Check if we're in a virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  No virtual environment detected")
        print("   Consider creating one: python -m venv venv")
        return False


def install_dependencies():
    """Install project dependencies."""
    # Install base requirements
    run_command("pip install --upgrade pip", "Upgrading pip")
    run_command("pip install -r requirements.txt", "Installing base requirements")
    run_command("pip install -r requirements-dev.txt", "Installing development requirements")


def setup_pre_commit():
    """Set up pre-commit hooks."""
    run_command("pre-commit install", "Installing pre-commit hooks")
    run_command("pre-commit install --hook-type commit-msg", "Installing commit-msg hook")


def run_initial_checks():
    """Run initial checks to ensure everything is working."""
    print("\n🔍 Running initial checks...")
    
    # Check if tools are available
    tools = [
        ("black", "Black formatter"),
        ("isort", "isort import sorter"),
        ("flake8", "flake8 linter"),
        ("pytest", "pytest test runner"),
        ("bandit", "bandit security checker"),
        ("pre-commit", "pre-commit hooks"),
    ]
    
    for tool, description in tools:
        result = run_command(f"{tool} --version", f"Checking {description}", check=False)
        if result.returncode == 0:
            print(f"✅ {description} is available")
        else:
            print(f"❌ {description} is not available")


def run_formatting():
    """Run initial formatting on the codebase."""
    print("\n🎨 Running initial code formatting...")
    run_command("black .", "Formatting code with Black", check=False)
    run_command("isort .", "Sorting imports with isort", check=False)


def run_tests():
    """Run tests to ensure everything is working."""
    print("\n🧪 Running tests...")
    run_command("pytest --cov=. --cov-report=term-missing", "Running tests with coverage", check=False)


def main():
    """Main setup function."""
    print("🚀 Setting up development environment for OS App")
    print("=" * 50)
    
    # Check prerequisites
    check_python_version()
    check_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Set up pre-commit hooks
    setup_pre_commit()
    
    # Run initial checks
    run_initial_checks()
    
    # Run initial formatting
    run_formatting()
    
    # Run tests
    run_tests()
    
    print("\n" + "=" * 50)
    print("🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Create a feature branch: git checkout -b feature/your-feature")
    print("2. Make your changes")
    print("3. Commit with pre-commit hooks: git commit -m 'Your message'")
    print("4. Push and create a PR: git push origin feature/your-feature")
    print("\nUseful commands:")
    print("- Run tests: pytest")
    print("- Format code: black . && isort .")
    print("- Lint code: flake8 .")
    print("- Run pre-commit: pre-commit run --all-files")


if __name__ == "__main__":
    main() 