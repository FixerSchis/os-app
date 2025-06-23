# CI/CD Setup Guide

This document explains the complete Continuous Integration and Continuous Deployment (CI/CD) setup for the OS App project.

## Overview

The CI/CD pipeline ensures that all code changes meet quality standards before being merged into protected branches, and automatically deploys to production when code is pushed to master. It includes automated testing, code quality checks, security analysis, branch protection, and automated deployment.

## What's Included

### 1. GitHub Actions Workflows

#### `ci.yml` - Main CI Pipeline
- **Triggers**: Every commit and pull request to master
- **Jobs**:
  - **Tests and Linting**: Runs tests across Python 3.10-3.12, linting, formatting checks
  - **Security Checks**: Bandit security analysis and Safety vulnerability checks
  - **Pre-commit Checks**: Runs all pre-commit hooks on all files

#### `deploy.yml` - Production Deployment Pipeline
- **Triggers**: After successful CI completion on master branch
- **Jobs**:
  - **Deploy to Production**: Automatically deploys to production server
  - **Backup Management**: Creates backups before deployment
  - **Health Checks**: Verifies deployment success
  - **Rollback Support**: Automatic rollback on failure

#### `setup-branch-protection.yml` - Branch Protection Setup
- **Triggers**: Manual dispatch or push to master
- **Purpose**: Automatically configures branch protection rules

#### `initial-setup.yml` - Repository Initialization
- **Triggers**: Manual dispatch or first push to master
- **Purpose**: Sets up repository settings and configures protection for the master branch.

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

## Deployment Architecture

```
GitHub Repository
       ↓
   CI Pipeline (tests, linting, security)
       ↓
   CD Pipeline (deployment)
       ↓
   Production Server (Debian)
       ↓
   Nginx (reverse proxy)
       ↓
   Gunicorn (WSGI server)
       ↓
   Flask Application
```

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

3. **Production Server Setup**:
   - Follow the detailed instructions in `DEPLOYMENT.md`
   - Run the automated setup script: `python3 scripts/setup_production_server.py`
   - Configure GitHub repository secrets

4. **Verify Setup**:
   - Check Settings → Branches for protection rules
   - Verify Actions tab shows workflows running
   - Test deployment by pushing to master

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

6. **Automatic Deployment**:
   - When merged to master, CI runs
   - If CI passes, CD automatically deploys to production
   - Monitor deployment in GitHub Actions

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
   - Automatic deployment to production

## Deployment Process

### Automatic Deployment

The deployment pipeline automatically:

1. **Creates Deployment Package**: Excludes development files and creates optimized archive
2. **Backs Up Current Version**: Creates timestamped backup before deployment
3. **Deploys New Code**: Extracts and sets up new version
4. **Preserves Database**: Maintains database in persistent location (`/var/lib/os-app/`)
5. **Runs Migrations**: Executes database migrations automatically
6. **Restarts Service**: Restarts the application with new code
7. **Health Check**: Verifies the service is running correctly
8. **Cleanup**: Removes old backups (keeps last 5)

### Manual Deployment

If needed, you can deploy manually:

```bash
# On the production server
cd /opt/os-app
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_PATH=/var/lib/os-app
flask db upgrade
sudo systemctl restart os-app
```

### Rollback

If deployment fails:

1. **Automatic**: Pipeline stops and keeps previous version
2. **Manual**: Use backup files in `/opt/backups/os-app/`

```bash
sudo systemctl stop os-app
cd /opt/backups/os-app
sudo tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz -C /opt/
sudo systemctl start os-app
```

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
- **Parallel**: Tests run across Python 3.10-3.12

## Monitoring and Maintenance

### Production Monitoring

- **Service Status**: `sudo systemctl status os-app`
- **Logs**: `sudo journalctl -u os-app -f`
- **Nginx Logs**: `/var/log/nginx/`
- **Application Logs**: `/var/log/os-app/`

### Backup Management

- **Automatic**: Before each deployment
- **Location**: `/opt/backups/os-app/`
- **Retention**: Last 5 backups
- **Manual**: Database backups with `sqlite3 os_app.db ".backup backup.db"`

### Performance Optimization

- **Gunicorn Workers**: 2-4 workers based on server resources
- **Nginx**: Gzip compression, static file caching
- **Database**: Regular maintenance and optimization

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
   pytest --tb=short  # Get detailed error info
   pytest -x  # Stop on first failure
   ```

#### Deployment Failures

1. **Check GitHub Actions Logs**: Look for specific error messages
2. **Verify SSH Connectivity**: Test connection to production server
3. **Check Server Logs**: Review system and application logs
4. **Verify Configuration**: Check environment variables and permissions

### Getting Help

1. **Check Documentation**: Review `DEPLOYMENT.md` for detailed setup instructions
2. **Review Logs**: GitHub Actions logs and server logs
3. **Test Locally**: Ensure code works in development environment
4. **Rollback**: Use backup if deployment fails

## Security Considerations

### Repository Security

- **Branch Protection**: Prevents direct pushes to protected branches
- **Code Reviews**: Required for all changes to master
- **Security Scanning**: Automated vulnerability checks
- **Secret Management**: Secure handling of deployment credentials

### Production Security

- **Firewall**: Configure UFW to allow only necessary ports
- **SSL/TLS**: Automatic certificate management with Let's Encrypt
- **User Permissions**: Limited deployment user with sudo access
- **Regular Updates**: Automated system and package updates

## Support

For issues with CI/CD:

1. **Check GitHub Actions**: Review workflow logs for specific errors
2. **Verify Configuration**: Ensure all secrets and settings are correct
3. **Test Locally**: Run pre-commit hooks and tests locally
4. **Review Documentation**: Check `DEPLOYMENT.md` for deployment-specific issues

The CI/CD pipeline is designed to be robust and self-healing, with comprehensive logging and rollback capabilities.
