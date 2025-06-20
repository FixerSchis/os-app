import os

class Config:
    # Use a consistent secret key
    SECRET_KEY = 'your-secret-key-here'  # In production, use a secure random key
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60  # 30 days in seconds
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Project root
    DATABASE_PATH = os.path.join(basedir, 'db')
    DATABASE_FILE_NAME = "oslrp.db"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(DATABASE_PATH, DATABASE_FILE_NAME)}'
    
    # Server configuration
    DEFAULT_PORT = 5000
    SSL_ENABLED = True
    SSL_CERT_FILE = os.path.join(basedir, 'data', 'ssl', 'cert.pem')
    SSL_KEY_FILE = os.path.join(basedir, 'data', 'ssl', 'key.pem')
    
    # Email configuration
    MAIL_SERVER = 'smtp.example.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@example.com'
    MAIL_PASSWORD = 'your-password'
    MAIL_DEFAULT_SENDER = 'Orion Sphere LRP <no-reply@example.com>'
    
    # Application configuration
    BASE_URL = 'https://fixer-mc.ddns.net'  # Used for generating verification links 