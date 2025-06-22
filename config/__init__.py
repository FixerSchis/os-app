import os


class Config:
    # Use a consistent secret key
    SECRET_KEY = "your-secret-key-here"  # nosec B105
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60  # 30 days in seconds

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Project root
    DATABASE_PATH = os.path.join(basedir, "db")
    DATABASE_FILE_NAME = "oslrp.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DATABASE_PATH, DATABASE_FILE_NAME)}"

    # Server configuration
    DEFAULT_PORT = 443
    SSL_ENABLED = True
    SSL_CERT_FILE = os.path.join(basedir, "data", "ssl", "cert.pem")
    SSL_KEY_FILE = os.path.join(basedir, "data", "ssl", "key.pem")

    # Gmail configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "schisveck@gmail.com"
    MAIL_PASSWORD = "replace-this-in-production"  # nosec B105
    MAIL_DEFAULT_SENDER = "Orion Sphere LRP <schisveck-gmail@gmail.com>"

    # Application configuration
    BASE_URL = "https://fixer-mc.ddns.net"  # Used for generating verification links


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
