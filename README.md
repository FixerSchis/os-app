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

The application will be available at `https://localhost`

## Linux Service Setup

To run the application as a systemd service on Linux:

### 1. Create Service User

Create a dedicated user for the application:
```bash
sudo useradd -r -s /bin/false orion-sphere
sudo groupadd orion-sphere
sudo usermod -a -G orion-sphere orion-sphere
```

### 2. Install Application

Copy the application to `/opt/orion-sphere-lrp`:
```bash
sudo mkdir -p /opt/orion-sphere-lrp
sudo cp -r . /opt/orion-sphere-lrp/
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp
```

### 3. Set Up Virtual Environment

```bash
cd /opt/orion-sphere-lrp
sudo -u orion-sphere python3 -m venv venv
sudo -u orion-sphere /opt/orion-sphere-lrp/venv/bin/pip install -r requirements.txt
```

### 4. Create Required Directories

```bash
sudo mkdir -p /opt/orion-sphere-lrp/logs
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp/logs
```

### 5. Install Service File

Copy the service file to systemd:
```bash
sudo cp orion-sphere-lrp.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 6. Enable and Start Service

```bash
sudo systemctl enable orion-sphere-lrp
sudo systemctl start orion-sphere-lrp
```

### 7. Check Service Status

```bash
sudo systemctl status orion-sphere-lrp
```

### 8. View Logs

```bash
sudo journalctl -u orion-sphere-lrp -f
```

### Service Management Commands

- **Start service**: `sudo systemctl start orion-sphere-lrp`
- **Stop service**: `sudo systemctl stop orion-sphere-lrp`
- **Restart service**: `sudo systemctl restart orion-sphere-lrp`
- **Reload configuration**: `sudo systemctl reload orion-sphere-lrp`
- **Disable service**: `sudo systemctl disable orion-sphere-lrp`

### Configuration

The service runs the application using the `wsgi.py` file. Make sure to:

1. Configure SSL certificates in `/opt/orion-sphere-lrp/data/ssl/`
2. Update the configuration in `config/__init__.py` for production settings
3. Ensure the database directory has proper permissions

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