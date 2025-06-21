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
- Python 3.8 or higher
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
   cp .env.example .env
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

The application will be available at `http://localhost:5000`

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
- Python 3.8 or higher
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
sudo chown orion-sphere:orion-sphere /opt/orion-sphere-lrp
# Copy your application files to /opt/orion-sphere-lrp/
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
DATABASE_URL=your-database-url
MAIL_SERVER=your-smtp-server
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
