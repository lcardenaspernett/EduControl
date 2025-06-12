# app/blueprints/teacher/__init__.py
from flask import Blueprint

# Crear el blueprint
teacher_bp = Blueprint('teacher', __name__, template_folder='templates')

# Importar las rutas después de crear el blueprint
from . import routes