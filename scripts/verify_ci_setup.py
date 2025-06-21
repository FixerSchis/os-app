#!/usr/bin/env python3
"""
Script to verify CI/CD setup is working correctly.
This script checks various aspects of the CI/CD configuration.
"""

import os
import subprocess  # nosec
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and return the result. Accepts command as a list."""
    try:
        # If command is a string, split it for safety
        if isinstance(command, str):
            command = command.split()
        result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)  # nosec B603
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_file_exists(filepath):
    """Check if a file exists."""
    return Path(filepath).exists()


def main():
    """Main verification function."""
    print("🔍 Verifying CI/CD Setup...")
    print("=" * 50)

    # Get repository root
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)

    checks_passed = 0
    total_checks = 0

    # Check 1: Verify workflow files exist
    print("\n1. Checking workflow files...")
    workflow_files = [
        ".github/workflows/ci.yml",
        ".github/workflows/setup-branch-protection.yml",
        ".github/workflows/initial-setup.yml",
        ".github/workflows/release.yml",
    ]

    for workflow_file in workflow_files:
        total_checks += 1
        if check_file_exists(workflow_file):
            print(f"   ✅ {workflow_file} exists")
            checks_passed += 1
        else:
            print(f"   ❌ {workflow_file} missing")

    # Check 2: Verify pre-commit config
    print("\n2. Checking pre-commit configuration...")
    total_checks += 1
    if check_file_exists(".pre-commit-config.yaml"):
        print("   ✅ .pre-commit-config.yaml exists")
        checks_passed += 1
    else:
        print("   ❌ .pre-commit-config.yaml missing")

    # Check 3: Check current branch
    print("\n3. Checking current branch...")
    success, stdout, stderr = run_command(["git", "branch", "--show-current"])
    total_checks += 1
    if success:
        current_branch = stdout.strip()
        print(f"   ✅ Current branch: {current_branch}")
        if current_branch in ["master", "develop"]:
            checks_passed += 1
        else:
            print("   ⚠️  Not on master or develop branch")
    else:
        print(f"   ❌ Could not determine current branch: {stderr}")

    # Check 4: Check if develop branch exists
    print("\n4. Checking if develop branch exists...")
    success, stdout, stderr = run_command(["git", "ls-remote", "--heads", "origin", "develop"])
    total_checks += 1
    if success and stdout.strip():
        print("   ✅ Develop branch exists on remote")
        checks_passed += 1
    else:
        print("   ❌ Develop branch does not exist on remote")

    # Check 5: Check if workflows are properly configured for master
    print("\n5. Checking workflow branch configuration...")
    total_checks += 1
    ci_workflow = repo_root / ".github" / "workflows" / "ci.yml"
    if ci_workflow.exists():
        content = ci_workflow.read_text()
        if "branches: [ master, develop ]" in content:
            print("   ✅ CI workflow configured for master and develop")
            checks_passed += 1
        else:
            print("   ❌ CI workflow not properly configured for master/develop")
    else:
        print("   ❌ CI workflow file not found")

    # Check 6: Verify requirements files
    print("\n6. Checking requirements files...")
    req_files = ["requirements.txt", "requirements-dev.txt"]
    for req_file in req_files:
        total_checks += 1
        if check_file_exists(req_file):
            print(f"   ✅ {req_file} exists")
            checks_passed += 1
        else:
            print(f"   ❌ {req_file} missing")

    # Check 7: Check pytest configuration
    print("\n7. Checking pytest configuration...")
    total_checks += 1
    if check_file_exists("pytest.ini"):
        print("   ✅ pytest.ini exists")
        checks_passed += 1
    else:
        print("   ❌ pytest.ini missing")

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Summary: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("🎉 All checks passed! Your CI/CD setup should be working correctly.")
        print("\nNext steps:")
        print("1. Go to GitHub and check the Actions tab")
        print("2. Look for workflow runs on the master and develop branches")
        print("3. Create a test PR to verify branch protection is working")
        print("4. Check that all required status checks are enforced")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\nTo fix issues:")
        print("1. Ensure all workflow files are properly configured")
        print("2. Push to master/develop to trigger workflow runs")
        print("3. Check GitHub Actions tab for any workflow failures")

    return 0 if checks_passed == total_checks else 1


if __name__ == "__main__":
    sys.exit(main())
