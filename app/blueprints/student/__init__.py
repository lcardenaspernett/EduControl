# app/blueprints/student/__init__.py
from flask import Blueprint

# Crear el blueprint
student_bp = Blueprint('student', __name__, template_folder='templates')

# Importar las rutas después de crear el blueprint
from . import routes