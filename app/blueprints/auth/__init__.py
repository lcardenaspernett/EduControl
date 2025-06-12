# app/blueprints/auth/__init__.py
"""
Blueprint de autenticación para EduControl
Maneja login, logout, registro y validación de usuarios
"""

from flask import Blueprint

# Crear el blueprint de autenticación
auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

# Importar las rutas después de crear el blueprint
from .auth import auth_bp

# Hacer disponible para importación
__all__ = ['auth_bp']