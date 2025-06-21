# CI/CD Setup Guide

This document explains the complete Continuous Integration and Continuous Deployment (CI/CD) setup for the OS App project.

## Overview

The CI/CD pipeline ensures that all code changes meet quality standards before being merged into protected branches. It includes automated testing, code quality checks, security analysis, and branch protection.

## What's Included

### 1. GitHub Actions Workflows

#### `ci.yml` - Main CI Pipeline
- **Triggers**: Every commit and pull request to master/develop
- **Jobs**:
  - **Tests and Linting**: Runs tests across Python 3.8-3.11, linting, formatting checks
  - **Security Checks**: Bandit security analysis and Safety vulnerability checks
  - **Pre-commit Checks**: Runs all pre-commit hooks on all files

#### `setup-branch-protection.yml` - Branch Protection Setup
- **Triggers**: Manual dispatch or push to master/develop
- **Purpose**: Automatically configures branch protection rules

#### `initial-setup.yml` - Repository Initialization
- **Triggers**: Manual dispatch or first push to master
- **Purpose**: Sets up repository settings, creates develop branch, configures protection

#### `release.yml` - Release Management
- **Triggers**: Manual dispatch
- **Purpose**: Handles releases and versioning

### 2. Branch Protection Rules

#### Master Branch
- ✅ Required status checks: All CI jobs must pass
- ✅ Pull request reviews: At least 1 approval required
- ✅ Code owner reviews: Required
- ✅ Stale review dismissal: Enabled
- ❌ Force pushes: Disabled
- ❌ Branch deletions: Disabled

#### Develop Branch
- ✅ Required status checks: All CI jobs must pass
- ✅ Pull request reviews: At least 1 approval required
- ❌ Code owner reviews: Not required
- ✅ Stale review dismissal: Enabled
- ❌ Force pushes: Disabled
- ❌ Branch deletions: Disabled

### 3. Pre-commit Hooks

Local development hooks that run before each commit:
- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with newline
- **check-yaml**: Validates YAML files
- **check-added-large-files**: Prevents large file commits
- **check-merge-conflict**: Detects merge conflict markers
- **debug-statements**: Removes debug statements
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **bandit**: Security analysis

## Setup Instructions

### For Repository Administrators

1. **Initial Setup** (run once):
   ```bash
   # Push to main branch to trigger initial setup
   git push origin main
   ```

2. **Manual Setup** (if needed):
   - Go to Actions tab
   - Select "Initial Repository Setup"
   - Click "Run workflow"

3. **Verify Setup**:
   - Check Settings → Branches for protection rules
   - Verify Actions tab shows workflows running

### For Developers

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd os-app
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Run Setup Script**:
   ```bash
   python scripts/setup_dev_environment.py
   ```

3. **Manual Setup** (alternative):
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

## Development Workflow

### Standard Workflow

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Commit Changes**:
   ```bash
   git add .
   git commit -m "Add your feature"
   # Pre-commit hooks run automatically
   ```

4. **Push and Create PR**:
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

5. **Wait for CI**:
   - All checks must pass
   - Get code review approval
   - Merge when ready

### Hotfix Workflow

1. **Create Hotfix Branch**:
   ```bash
   git checkout -b hotfix/critical-fix
   ```

2. **Make Changes and Test**:
   ```bash
   # Make minimal changes
   pytest  # Ensure tests pass
   ```

3. **Commit and Push**:
   ```bash
   git commit -m "Fix critical issue"
   git push origin hotfix/critical-fix
   ```

4. **Create PR to main**:
   - Requires code owner approval
   - All CI checks must pass

## Quality Standards

### Code Coverage
- **Minimum**: 70% coverage required
- **Goal**: 80%+ coverage
- **Exclusions**: Configuration files, migrations, templates

### Code Quality
- **Formatting**: Black with 100 character line length
- **Imports**: isort with Black profile
- **Linting**: flake8 with custom rules
- **Security**: Bandit analysis on all Python files

### Testing
- **Framework**: pytest
- **Coverage**: pytest-cov
- **Mocking**: pytest-mock
- **Parallel**: Tests run across Python 3.8-3.11

## Troubleshooting

### Common Issues

#### CI Failures

1. **Formatting Issues**:
   ```bash
   black .
   isort .
   git add .
   git commit -m "Fix formatting"
   ```

2. **Linting Issues**:
   ```bash
   flake8 . --select=E9,F63,F7,F82  # Check syntax errors
   flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100
   ```

3. **Test Failures**:
   ```bash
   pytest  # Run locally first
   pytest --cov=. --cov-report=term-missing
   ```