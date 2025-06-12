from flask import Blueprint
from .views import login, register, logout, profile, change_password

# Crear el blueprint de autenticación
auth_bp = Blueprint('auth', __name__)

# Registrar las rutas usando el blueprint
auth_bp.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
auth_bp.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
auth_bp.add_url_rule('/logout', 'logout', logout, methods=['GET'])
auth_bp.add_url_rule('/profile', 'profile', profile, methods=['GET'])
auth_bp.add_url_rule('/change_password', 'change_password', change_password, methods=['GET', 'POST'])

# Exportar el blueprint
__all__ = ['auth_bp']
