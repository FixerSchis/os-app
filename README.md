# Orion Sphere LRP

A Flask web application for managing a Live Role-Playing (LRP) game system, featuring character management, wiki functionality, and user authentication.

## Features

- User authentication and role-based access control
- Character management system
- Wiki system with image support
- Species and skills management
- User management dashboard
- Settings configuration
- SQLite database with SQLAlchemy ORM
- Flash messages for user feedback
- Form validation (both client and server-side)
- Error handling for common HTTP errors

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
.
├── app.py              # Main application file
├── config.py           # Application configuration
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS, images)
├── templates/         # HTML templates
│   ├── errors/        # Error pages
│   └── ...           # Other template files
├── models/            # Database models
│   └── enums.py      # Enumeration definitions
├── routes/            # Route blueprints
│   ├── auth.py       # Authentication routes
│   ├── characters.py # Character management
│   ├── species.py    # Species management
│   ├── skills.py     # Skills management
│   ├── wiki.py       # Wiki functionality
│   └── ...          # Other route modules
├── helper/           # Helper functions
└── db/              # Database files
```

## Dependencies

- Flask 3.0.2
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Flask-WTF 1.2.1
- email-validator 2.1.0
- python-dotenv 1.0.1
- Werkzeug 3.0.1

## Security Features

- Passwords are hashed using Werkzeug's security functions
- CSRF protection enabled
- Secure session handling
- Input validation and sanitization
- Role-based access control