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
