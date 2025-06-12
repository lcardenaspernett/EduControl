import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # Configuración básica de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-muy-segura-aqui'
    
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///educontrol.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Cambiar a True para ver las consultas SQL en desarrollo
    
    # Configuración de Flask-Login
    REMEMBER_COOKIE_DURATION = 86400  # 24 horas en segundos
    
    # Configuración de paginación
    POSTS_PER_PAGE = 10
    USERS_PER_PAGE = 15
    COURSES_PER_PAGE = 12
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo para uploads
    UPLOAD_FOLDER = 'app/static/uploads'
    
    # Configuración de email (para futuras funcionalidades)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configuración específica del sistema educativo
    SISTEMA_NOMBRE = "EduControl"
    SISTEMA_VERSION = "1.0.0"
    NOTA_MAXIMA_DEFECTO = 5.0
    NOTA_MINIMA_APROBACION = 3.0
    SEMESTRE_ACTUAL = "2025-1"

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Mostrar consultas SQL en desarrollo

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}