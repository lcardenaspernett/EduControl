from datetime import timedelta
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class SecurityConfig:
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL') or 'memory://'
    LOGIN_RATE_LIMIT = "5 per minute"
    API_RATE_LIMIT = "100 per minute"
    
    # Security Settings (nombres compatibles con el test)
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    MAX_FAILED_ATTEMPTS = MAX_LOGIN_ATTEMPTS
    LOCKOUT_DURATION_MINUTES = int(os.getenv('LOCKOUT_DURATION_MINUTES', 15))
    LOCKOUT_DURATION = timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    ACCOUNT_LOCK_DURATION = LOCKOUT_DURATION
    
    # Password Configuration
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_MAX_LENGTH = 128
    REQUIRE_PASSWORD_COMPLEXITY = True
    PASSWORD_REQUIREMENTS = {
        'uppercase': True,
        'lowercase': True,
        'numbers': True,
        'special_chars': True
    }
    
    # Password Reset
    PASSWORD_RESET_EXPIRES = timedelta(hours=24)
    RESET_TOKEN_LENGTH = 32
    
    # Two-Factor Authentication
    TOTP_SECRET_LENGTH = 16
    TOTP_INTERVAL = 30
    
    # Session Management
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')