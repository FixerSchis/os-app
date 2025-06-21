# CI/CD Setup Guide

This document explains the complete Continuous Integration and Continuous Deployment (CI/CD) setup for the OS App project.

## Overview

The CI/CD pipeline ensures that all code changes meet quality standards before being merged into protected branches. It includes automated testing, code quality checks, security analysis, and branch protection.

## What's Included

### 1. GitHub Actions Workflows

#### `ci.yml` - Main CI Pipeline
- **Triggers**: Every commit and pull request to main/develop
- **Jobs**:
  - **Tests and Linting**: Runs tests across Python 3.8-3.11, linting, formatting checks
  - **Security Checks**: Bandit security analysis and Safety vulnerability checks
  - **Pre-commit Checks**: Runs all pre-commit hooks on all files

#### `setup-branch-protection.yml` - Branch Protection Setup
- **Triggers**: Manual dispatch or push to main/develop
- **Purpose**: Automatically configures branch protection rules

#### `initial-setup.yml` - Repository Initialization
- **Triggers**: Manual dispatch or first push to main
- **Purpose**: Sets up repository settings, creates develop branch, configures protection

#### `release.yml` - Release Management
- **Triggers**: Manual dispatch
- **Purpose**: Handles releases and versioning

### 2. Branch Protection Rules

#### Main Branch
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

4. **Coverage Issues**:
   - Add tests for new code
   - Check coverage report: `pytest --cov=. --cov-report=html`
   - Open `htmlcov/index.html` in browser

#### Pre-commit Hook Failures

1. **Manual Run**:
   ```bash
   pre-commit run --all-files
   ```

2. **Skip Hooks** (emergency only):
   ```bash
   git commit -m "Emergency fix" --no-verify
   ```

3. **Update Hooks**:
   ```bash
   pre-commit autoupdate
   ```

### Performance Issues

1. **Slow CI**:
   - Check cache configuration
   - Review parallel job settings
   - Consider splitting large test suites

2. **Local Development**:
   - Use pre-commit hooks for faster feedback
   - Run specific test files during development
   - Use pytest-xdist for parallel testing

## Configuration Files

### GitHub Actions
- `.github/workflows/ci.yml`: Main CI pipeline
- `.github/workflows/setup-branch-protection.yml`: Branch protection
- `.github/workflows/initial-setup.yml`: Repository setup
- `.github/workflows/release.yml`: Release management

### Code Quality Tools
- `pyproject.toml`: Black, isort, pytest configuration
- `pytest.ini`: Pytest settings
- `.pre-commit-config.yaml`: Pre-commit hooks
- `.bandit`: Security analysis configuration

### Dependencies
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies

## Best Practices

### For Developers

1. **Always run tests locally** before pushing
2. **Use meaningful commit messages**
3. **Keep PRs small and focused**
4. **Add tests for new functionality**
5. **Update documentation when needed**

### For Reviewers

1. **Check CI status** before approving
2. **Review test coverage**
3. **Verify security implications**
4. **Ensure documentation is updated**
5. **Test locally if needed**

### For Maintainers

1. **Monitor CI performance**
2. **Update dependencies regularly**
3. **Review and update quality standards**
4. **Maintain branch protection rules**
5. **Keep workflows up to date**

## Monitoring and Maintenance

### Regular Tasks

1. **Weekly**:
   - Review CI performance
   - Check for failed builds
   - Update dependencies if needed

2. **Monthly**:
   - Review and update quality standards
   - Check coverage trends
   - Update GitHub Actions versions

3. **Quarterly**:
   - Review and update branch protection rules
   - Assess CI/CD pipeline effectiveness
   - Plan improvements

### Metrics to Track

- **Build Success Rate**: Should be >95%
- **Average Build Time**: Monitor for increases
- **Test Coverage**: Maintain >70%, aim for >80%
- **Security Issues**: Address promptly
- **PR Review Time**: Keep under 48 hours

## Support

- **CI/CD Issues**: Check Actions tab for detailed logs
- **Local Setup**: Run `python scripts/setup_dev_environment.py`
- **Documentation**: See README.md for detailed setup instructions
- **Questions**: Create an issue or contact maintainers

## Future Improvements

- [ ] Add deployment automation
- [ ] Implement staging environment
- [ ] Add performance testing
- [ ] Integrate with external security scanning
- [ ] Add automated dependency updates
- [ ] Implement feature flags
- [ ] Add monitoring and alerting 