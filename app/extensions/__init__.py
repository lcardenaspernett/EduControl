from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# Inicializar extensiones
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

# Función para inicializar todas las extensiones de seguridad
def init_security_extensions(app):
    """Inicializar todas las extensiones de seguridad"""
    jwt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
