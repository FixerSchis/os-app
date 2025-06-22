#!/usr/bin/env python3
"""
WSL App Startup Script
Starts the OS App Flask application in WSL environment without systemd.
"""

import os
import signal
import subprocess  # nosec
import sys
import time
from pathlib import Path


def run_command(command, check=True, capture_output=False):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,  # nosec
            check=check,
            capture_output=capture_output,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        if check:
            return None
        return e
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def check_app_directory():
    """Check if the app directory exists and has the required files."""
    app_dir = "/opt/os-app"

    if not os.path.exists(app_dir):
        print(f"❌ App directory not found: {app_dir}")
        print("Please run the setup script first: python3 scripts/setup_production_server.py")
        return False

    required_files = ["app.py", "requirements.txt", "venv"]
    missing_files = []

    for file in required_files:
        if not os.path.exists(os.path.join(app_dir, file)):
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False

    print(f"✅ App directory found: {app_dir}")
    return True


def install_requirements():
    """Install Python requirements if needed."""
    print("\nChecking Python requirements...")

    app_dir = "/opt/os-app"
    venv_path = os.path.join(app_dir, "venv")

    # Check if virtual environment exists
    if not os.path.exists(venv_path):
        print("Creating virtual environment...")
        result = run_command(f"cd {app_dir} && python3 -m venv venv")
        if not result:
            print("❌ Failed to create virtual environment")
            return False

    # Install/upgrade pip
    print("Upgrading pip...")
    run_command(
        f"cd {app_dir} && source venv/bin/activate && pip install --upgrade pip",
        check=False,
    )

    # Install requirements
    print("Installing requirements...")
    result = run_command(
        f"cd {app_dir} && source venv/bin/activate && pip install -r requirements.txt"
    )
    if not result:
        print("❌ Failed to install requirements")
        return False

    print("✅ Requirements installed successfully")
    return True


def start_app(port=5000):
    """Start the Flask application."""
    print(f"\nStarting Flask app on port {port}...")

    app_dir = "/opt/os-app"

    # Check if app is already running
    result = run_command(f"netstat -tlnp | grep :{port}", check=False, capture_output=True)
    if result and hasattr(result, "returncode") and result.returncode == 0:
        print(f"⚠️  Port {port} is already in use. Stopping existing process...")
        run_command(f"pkill -f 'gunicorn.*:{port}'", check=False)
        time.sleep(2)

    # Start the app
    print("Starting gunicorn...")
    cmd = (
        f"cd {app_dir} && source venv/bin/activate && "
        f"gunicorn --workers 2 --bind 0.0.0.0:{port} app:app"
    )

    try:
        # Start in background
        process = subprocess.Popen(
            cmd,
            shell=True,  # nosec
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,  # Create new process group
        )

        # Wait a moment for startup
        time.sleep(3)

        # Check if process is still running
        if process.poll() is None:
            print(f"✅ App started successfully on port {port}")
            print(f"Process ID: {process.pid}")
            print(f"\nAccess your app at: http://localhost:{port}")
            print("\nTo stop the app, run: pkill -f gunicorn")
            return process
        else:
            stdout, stderr = process.communicate()
            print("❌ Failed to start app")
            if stderr:
                print(f"Error: {stderr}")
            return None

    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return None


def main():
    """Main function."""
    print("WSL App Startup Script")
    print("=" * 30)

    # Check if we're in WSL
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            version_info = f.read()
            if "microsoft" in version_info.lower():
                print("✅ Running in WSL")
            else:
                print("⚠️  Not running in WSL (but continuing anyway)")

    # Check app directory
    if not check_app_directory():
        sys.exit(1)

    # Install requirements
    if not install_requirements():
        sys.exit(1)

    # Get port from user
    port = input("\nEnter port number (default: 5000): ").strip() or "5000"

    try:
        port = int(port)
    except ValueError:
        print("❌ Invalid port number")
        sys.exit(1)

    # Start the app
    process = start_app(port)

    if process:
        print("\nApp is running! Press Ctrl+C to stop...")
        try:
            # Keep the script running
            while True:
                time.sleep(1)
                if process.poll() is not None:
                    print("\n❌ App stopped unexpectedly")
                    break
        except KeyboardInterrupt:
            print("\n\nStopping app...")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            print("✅ App stopped")
    else:
        print("❌ Failed to start app")
        sys.exit(1)


if __name__ == "__main__":
    main()
