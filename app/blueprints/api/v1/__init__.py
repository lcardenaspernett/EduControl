# app/blueprints/api/v1/__init__.py
from flask import Blueprint

# Crear el blueprint para API v1
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Importar las rutas después de crear el blueprint
from . import routes