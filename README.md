# OS App

A Flask-based web application for managing LARP (Live Action Role-Playing) game data, including characters, events, and game mechanics.

## Features

- Character management and creation
- Event organization and tracking
- Database management for game rules and items
- User authentication and authorization
- Email notifications
- QR code generation
- PDF generation for game materials

## Quick Start

### Prerequisites
- Python 3.10 or higher
- pip
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/os-app.git
   cd os-app
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python app.py
   ```

The application will be available at the URL and port specified in your environment variables (default: `http://localhost:5000`)

## Configuration

This application uses environment variables for all configuration. Copy `env.example` to `.env` and modify the values as needed:

### Required Environment Variables

- `SECRET_KEY`: Secret key for Flask sessions (generate a secure random string)
- `MAIL_USERNAME`: Gmail username for sending emails
- `MAIL_PASSWORD`: Gmail app password (not your regular password)

### Optional Environment Variables

- `FLASK_RUN_PORT`: Port to run the server on (default: 5000)
- `SSL_ENABLED`: Enable SSL/HTTPS (default: false)
- `SSL_CERT_FILE`: Path to SSL certificate file
- `SSL_KEY_FILE`: Path to SSL private key file
- `BASE_URL`: Base URL for the application (default: http://localhost)
- `MAIL_SERVER`: SMTP server (default: smtp.gmail.com)
- `MAIL_PORT`: SMTP port (default: 587)
- `MAIL_USE_TLS`: Use TLS for email (default: true)
- `MAIL_DEFAULT_SENDER`: Default sender email address

### Development Configuration

For development, you can use these settings in your `.env` file:

```bash
FLASK_DEBUG=1
FLASK_RUN_PORT=5000
SSL_ENABLED=false
BASE_URL=http://localhost
```

### Production Configuration

For production, use these settings:

```bash
FLASK_DEBUG=0
FLASK_RUN_PORT=443
SSL_ENABLED=true
BASE_URL=https://yourdomain.com
```

## Development

### Setting up the development environment

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   black .
   isort .
   ```

5. Lint code:
   ```bash
   flake8 .
   ```

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to:

- Set up your development environment
- Follow our coding standards
- Submit pull requests
- Report issues

### Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pytest**: Testing
- **bandit**: Security analysis
- **pre-commit**: Git hooks for automated checks

### Continuous Integration and Deployment (CI/CD)

This project uses GitHub Actions for automated testing, code quality checks, and branch protection. The CI/CD pipeline ensures that all code changes meet quality standards before being merged.

#### Automated Checks

Every commit and pull request triggers the following checks:

1. **Tests and Linting** (`Tests and Linting` job):
   - Runs tests across Python 3.10, 3.11, and 3.12
   - Executes linting with flake8
   - Checks code formatting with Black
   - Verifies import sorting with isort
   - Runs pytest with coverage (minimum 70% required)
   - Uploads coverage reports to Codecov

2. **Security Checks** (`Security Checks` job):
   - Runs Bandit security analysis
   - Checks for known security vulnerabilities with Safety
   - Generates security reports

3. **Pre-commit Checks** (`Pre-commit Checks` job):
   - Runs all pre-commit hooks on all files
   - Ensures consistent code formatting and quality

#### Branch Protection

The main and develop branches are protected with the following rules:

- **Required Status Checks**: All CI jobs must pass before merging
- **Pull Request Reviews**: At least 1 approval required
- **Code Owner Reviews**: Required for main branch
- **Stale Review Dismissal**: Outdated reviews are automatically dismissed
- **No Force Pushes**: Force pushes are disabled
- **No Deletions**: Branch deletions are disabled

#### Setting Up Branch Protection

Branch protection is automatically configured when you push to main or develop branches. You can also manually trigger the setup:

1. Go to the **Actions** tab in your GitHub repository
2. Select the **Setup Branch Protection** workflow
3. Click **Run workflow**
4. Choose the branch to protect (main or develop)

#### Local Development Workflow

1. **Install pre-commit hooks** (recommended):
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Add your feature"
   ```
   (Pre-commit hooks will run automatically)

4. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Wait for CI checks** to complete on your PR

6. **Request review** from code owners (for main branch)

7. **Merge** once all checks pass and reviews are approved

#### CI/CD Workflows

- **`ci.yml`**: Main CI workflow that runs on all commits and PRs
- **`setup-branch-protection.yml`**: Automatically configures branch protection
- **`release.yml`**: Handles releases and versioning

#### Troubleshooting CI Issues

**Common Issues and Solutions:**

1. **Formatting Issues**:
   ```bash
   # Fix Black formatting
   black .

   # Fix import sorting
   isort .
   ```

2. **Linting Issues**:
   ```bash
   # Check specific issues
   flake8 . --select=E9,F63,F7,F82

   # Check all issues
   flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100
   ```

3. **Test Failures**:
   ```bash
   # Run tests locally
   pytest

   # Run with coverage
   pytest --cov=. --cov-report=term-missing
   ```

4. **Pre-commit Hook Failures**:
   ```bash
   # Run pre-commit manually
   pre-commit run --all-files

   # Run specific hook
   pre-commit run black --all-files
   ```

5. **Coverage Issues**:
   - Ensure new code has adequate test coverage
   - Minimum coverage requirement is 70%
   - Add tests for new functionality

#### CI/CD Configuration Files

- `.github/workflows/ci.yml`: Main CI workflow
- `.github/workflows/setup-branch-protection.yml`: Branch protection setup
- `.pre-commit-config.yaml`: Pre-commit hooks configuration
- `pyproject.toml`: Tool configurations (Black, isort, pytest)
- `pytest.ini`: Pytest configuration
- `.bandit`: Bandit security configuration

#### Performance Optimization

- **Caching**: Dependencies are cached between runs
- **Parallel Jobs**: Tests run in parallel across Python versions
- **Conditional Execution**: Some jobs only run when needed
- **Matrix Strategy**: Tests multiple Python versions efficiently

### Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
os-app/
├── app.py                 # Main application entry point
├── models/               # Database models
├── routes/               # Flask routes and views
├── templates/            # Jinja2 templates
├── static/               # Static files (CSS, JS, images)
├── tests/                # Test suite
├── migrations/           # Database migrations
├── config/               # Configuration files
└── utils/                # Utility functions
```

## Deployment

### Production Setup

1. Set up a production server
2. Install dependencies
3. Configure environment variables
4. Set up a production database
5. Run database migrations
6. Configure a WSGI server (e.g., Gunicorn)
7. Set up a reverse proxy (e.g., Nginx)

### Installing as a System Service

The application can be installed as a systemd service for automatic startup and management. This is the recommended approach for production deployments.

#### Prerequisites

- Linux system with systemd
- Python 3.10 or higher
- Application deployed to `/opt/orion-sphere-lrp` (or modify the service file accordingly)

#### Step 1: Create Service User

Create a dedicated user for running the application:

```bash
sudo useradd -r -s /bin/false orion-sphere
sudo groupadd orion-sphere
sudo usermod -a -G orion-sphere orion-sphere
```

#### Step 2: Deploy Application

Deploy your application to the target directory:

```bash
sudo mkdir -p /opt/orion-sphere-lrp
sudo cp -r . /opt/orion-sphere-lrp/
sudo rm -rf /opt/orion-sphere-lrp/.git
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp/
```

#### Step 3: Install Service File

Copy the service file to the systemd directory:

```bash
sudo cp orion-sphere-lrp.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/orion-sphere-lrp.service
```

#### Step 4: Configure Environment

Create a production environment file:

```bash
sudo -u orion-sphere nano /opt/orion-sphere-lrp/.env
```

Add your production environment variables:
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
MAIL_SERVER=your-mail-server
MAIL_USERNAME=your-email-username
MAIL_PASSWORD=your-email-password
```

#### Step 5: Set Up Virtual Environment

```bash
cd /opt/orion-sphere-lrp
sudo -u orion-sphere python3 -m venv venv
sudo -u orion-sphere venv/bin/pip install -r requirements.txt
```

#### Step 6: Initialize Database

```bash
sudo -u orion-sphere venv/bin/flask db upgrade
```

#### Step 7: Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable orion-sphere-lrp
sudo systemctl start orion-sphere-lrp
```

#### Step 8: Verify Installation

Check the service status:

```bash
sudo systemctl status orion-sphere-lrp
```

View logs:

```bash
sudo journalctl -u orion-sphere-lrp -f
```

#### Service Management Commands

```bash
# Start the service
sudo systemctl start orion-sphere-lrp

# Stop the service
sudo systemctl stop orion-sphere-lrp

# Restart the service
sudo systemctl restart orion-sphere-lrp

# Reload configuration (without stopping)
sudo systemctl reload orion-sphere-lrp

# Check status
sudo systemctl status orion-sphere-lrp

# View logs
sudo journalctl -u orion-sphere-lrp

# Follow logs in real-time
sudo journalctl -u orion-sphere-lrp -f

# Disable auto-start
sudo systemctl disable orion-sphere-lrp
```

#### Troubleshooting

1. **Service fails to start**: Check logs with `sudo journalctl -u orion-sphere-lrp -n 50`
2. **Permission issues**: Ensure the `orion-sphere` user owns the application directory
3. **Environment variables**: Verify `.env` file exists and has correct permissions
4. **Database connection**: Test database connectivity manually
5. **Port conflicts**: Ensure port 5000 (or your configured port) is available

#### Customization

You can modify the service file to:
- Change the working directory
- Use a different user/group
- Add additional environment variables
- Configure different restart policies
- Set resource limits

Example modifications:
```ini
# Add environment variables
Environment=FLASK_ENV=production
Environment=PORT=8080

# Change working directory
WorkingDirectory=/path/to/your/app

# Use different user
User=www-data
Group=www-data
```

### Environment Variables

Required environment variables:
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: Database connection string
- `MAIL_SERVER`: SMTP server for email
- `MAIL_USERNAME`: Email username
- `MAIL_PASSWORD`: Email password

## License

[Add your license information here]

## Support

- Create an issue for bugs or feature requests
- Check the documentation in the `/docs` folder
- Join our community discussions

## Acknowledgments

- Flask framework and ecosystem
- Contributors and maintainers
- LARP community feedback
