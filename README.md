# Orion Sphere LRP

A comprehensive Flask web application for managing Live Role-Playing (LRP) game systems. Built with modern web technologies, it provides a robust platform for character management, wiki functionality, user authentication, and game administration.

## 🚀 Features

### Core Functionality
- **User Authentication & Authorization**: Secure login system with role-based access control
- **Character Management**: Complete character creation, editing, and tracking system
- **Wiki System**: Rich content management with image support and markdown formatting
- **Species & Skills Management**: Comprehensive database for game mechanics
- **Downtime Activities**: Track and manage character activities between sessions
- **Research System**: Manage character research projects and progress
- **Banking System**: In-game currency and transaction management
- **Event Management**: Organize and track game events and attendance

### Technical Features
- **Modern Web Framework**: Built with Flask 3.0+ and SQLAlchemy ORM
- **Database Management**: SQLite with Alembic migrations for schema evolution
- **Security**: CSRF protection, password hashing, secure session handling
- **Email Integration**: Automated email notifications and user verification
- **PDF Generation**: Character sheets and documents with WeasyPrint
- **QR Code Support**: Generate QR codes for various game elements
- **SSL/TLS Support**: Built-in HTTPS support for secure connections
- **Responsive Design**: Modern UI with Bootstrap and custom styling

### Administrative Tools
- **User Management Dashboard**: Comprehensive user administration
- **Audit Logging**: Track system changes and user actions
- **Template Management**: Customizable templates for various game elements
- **Database Administration**: Web-based management of game data
- **Message System**: Internal communication between players and GMs

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Web Browser**: Modern browser with JavaScript enabled
- **SSL Certificates**: For production HTTPS deployment (optional for development)

## 🛠️ Installation

### Development Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd os-app
```

2. **Create a virtual environment**:
```bash
python -m venv venv
```

3. **Activate the virtual environment**:
   - **Windows**:
   ```bash
   venv\Scripts\activate
   ```
   - **Unix/macOS**:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```

5. **Initialize the database**:
```bash
# The database will be automatically initialized on first run
```

6. **Run the application**:
```bash
python app.py
```

The application will be available at `https://localhost` (HTTPS) or `http://localhost:5000` (HTTP)

### Production Setup

For production deployment, see the [Linux Service Setup](#linux-service-setup) section below.

## 🐧 Linux Service Setup

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
sudo mkdir -p /opt/orion-sphere-lrp/instance
sudo mkdir -p /opt/orion-sphere-lrp/db
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp/logs
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp/instance
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp/db
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

### Troubleshooting

If the service fails to start, check the following:

1. **Check service status and logs**:
```bash
sudo systemctl status orion-sphere-lrp
sudo journalctl -u orion-sphere-lrp -n 50
```

2. **Verify file permissions**:
```bash
sudo ls -la /opt/orion-sphere-lrp/
sudo ls -la /opt/orion-sphere-lrp/venv/bin/python
```

3. **Test manual execution**:
```bash
sudo -u orion-sphere /opt/orion-sphere-lrp/venv/bin/python /opt/orion-sphere-lrp/wsgi.py
```

4. **Check directory ownership**:
```bash
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp
```

5. **Verify virtual environment**:
```bash
sudo -u orion-sphere /opt/orion-sphere-lrp/venv/bin/pip list
```

### Configuration

The service runs the application using the `wsgi.py` file. Make sure to:

1. Configure SSL certificates in `/opt/orion-sphere-lrp/data/ssl/`
2. Update the configuration in `config/__init__.py` for production settings
3. Ensure the database directory has proper permissions
4. Set appropriate file permissions for the application directory

## 🏗️ Project Structure

```
os-app/
├── app.py                          # Main application entry point
├── wsgi.py                         # WSGI entry point for production
├── requirements.txt                # Python dependencies
├── orion-sphere-lrp.service        # Systemd service file
├── config/                         # Configuration management
│   └── __init__.py                # Main configuration class
├── static/                         # Static assets
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript files
│   ├── images/                    # Images and icons
│   └── external/                  # Third-party libraries
├── templates/                      # HTML templates
│   ├── auth/                      # Authentication pages
│   ├── characters/                # Character management
│   ├── wiki/                      # Wiki pages
│   ├── errors/                    # Error pages
│   └── ...                        # Other template directories
├── models/                         # Database models and business logic
│   ├── database/                  # Core database models
│   ├── tools/                     # Game-specific models
│   ├── enums.py                   # Enumeration definitions
│   └── extensions.py              # Flask extensions
├── routes/                         # Application routes
│   ├── auth.py                    # Authentication routes
│   ├── database/                  # Database management routes
│   ├── tools/                     # Game tool routes
│   └── ...                        # Other route modules
├── migrations/                     # Database migrations
│   └── versions/                  # Migration files
├── tests/                          # Test suite
│   ├── models/                    # Model tests
│   ├── routes/                    # Route tests
│   └── utils/                     # Utility tests
├── utils/                          # Utility functions
├── data/                          # Application data
│   ├── ssl/                       # SSL certificates
│   └── templates/                 # Print templates
└── db/                           # Database files (created at runtime)
```

## 📦 Dependencies

### Core Framework
- **Flask 3.0.2**: Web framework
- **Flask-SQLAlchemy 3.1.1**: Database ORM
- **Flask-Login 0.6.3**: User session management
- **Flask-WTF 1.2.1**: Form handling and CSRF protection
- **Flask-Migrate 4.0.5**: Database migrations
- **Flask-Mail 0.9.1**: Email functionality

### Security & Validation
- **Werkzeug 3.0.1**: WSGI utilities and security
- **email-validator 2.1.0.post1**: Email validation
- **cryptography 42.0.8**: Cryptographic functions
- **pyOpenSSL 24.1.0**: SSL/TLS support

### Utilities
- **python-dotenv 1.0.1**: Environment variable management
- **qrcode[pil] 7.4.2**: QR code generation
- **WeasyPrint 62.1**: PDF generation
- **pytest**: Testing framework

## 🔧 Configuration

### Environment Variables

The application can be configured using environment variables or by creating a `config/local.py` file:

```python
# config/local.py
class LocalConfig(Config):
    SECRET_KEY = 'your-secure-secret-key'
    MAIL_USERNAME = 'your-email@gmail.com'
    MAIL_PASSWORD = 'your-app-password'
    BASE_URL = 'https://your-domain.com'
    SSL_ENABLED = True
    DEFAULT_PORT = 443
```

### SSL Configuration

For HTTPS support, place your SSL certificates in `data/ssl/`:
- `cert.pem`: SSL certificate
- `key.pem`: Private key

### Database Configuration

The application uses SQLite by default. The database file is created automatically in the `db/` directory.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py
```

## 🔒 Security Features

- **Password Security**: Passwords hashed using Werkzeug's security functions
- **CSRF Protection**: Enabled on all forms
- **Session Security**: Secure session handling with configurable lifetime
- **Input Validation**: Comprehensive client and server-side validation
- **Role-Based Access Control**: Granular permissions system
- **SQL Injection Protection**: SQLAlchemy ORM prevents injection attacks
- **XSS Protection**: Template escaping and input sanitization

## 🚀 Deployment

### Development
```bash
python app.py
```

### Production with WSGI
```bash
python wsgi.py
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application
```

### Docker (Future Enhancement)
```bash
# Dockerfile and docker-compose.yml will be added in future versions
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the wiki documentation

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added Linux service support and enhanced documentation
- **Future**: Planned features and improvements

---

**Orion Sphere LRP** - Empowering Live Role-Playing communities with modern web technology.