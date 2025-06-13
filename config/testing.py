# testing.py
from app.config.security import SecurityConfig

class TestingConfig(SecurityConfig):
    """Configuración de prueba"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-secret-key'
    MAX_LOGIN_ATTEMPTS = 3  # Reducir para pruebas
    LOCKOUT_DURATION_MINUTES = 1  # Reducir para pruebas
    RATELIMIT_STORAGE_URL = 'memory://'  # Usar memoria en pruebas