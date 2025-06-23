import os


class Config:
    # Use a consistent secret key
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60  # 30 days in seconds

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Project root

    # Use environment variable for database path, with sensible defaults
    # In production: /var/lib/os-app/
    # In development: ./db/ (relative to project root)
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        (
            "/var/lib/os-app"
            if os.environ.get("FLASK_ENV") == "production"
            else os.path.join(basedir, "db")
        ),
    )
    DATABASE_FILE_NAME = "oslrp.db"

    # Ensure the database path is absolute for SQLAlchemy
    db_file_path = os.path.join(DATABASE_PATH, DATABASE_FILE_NAME)
    if not os.path.isabs(db_file_path):
        db_file_path = os.path.abspath(db_file_path)

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file_path}"

    # Server configuration
    DEFAULT_PORT = int(os.environ.get("FLASK_RUN_PORT", 5000))
    SSL_ENABLED = os.environ.get("SSL_ENABLED", "false").lower() == "true"
    SSL_CERT_FILE = os.environ.get(
        "SSL_CERT_FILE", os.path.join(basedir, "data", "ssl", "cert.pem")
    )
    SSL_KEY_FILE = os.environ.get("SSL_KEY_FILE", os.path.join(basedir, "data", "ssl", "key.pem"))

    # Application configuration
    BASE_URL = os.environ.get("BASE_URL", "http://localhost")

    # Gmail configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "replace-this-in-production")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "replace-this-in-production")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "Orion Sphere LRP <replace-this-in-production>"
    )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    SSL_ENABLED = False


# Try to import LocalConfig, but don't fail if local.py doesn't exist
try:
    from .local import LocalConfig
except ImportError:
    # If local.py doesn't exist, create a dummy LocalConfig that's the same as Config
    LocalConfig = Config
