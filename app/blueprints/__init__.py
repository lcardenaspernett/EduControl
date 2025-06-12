# app/blueprints/__init__.py
"""
Módulo de blueprints para EduControl
Organiza todas las rutas por funcionalidad
"""

# Importaciones que estarán disponibles cuando se creen los blueprints
__all__ = [
    'auth',      # Disponible
    'admin_bp',     # Se creará después
    'teacher_bp',   # Se creará después
    'student_bp',   # Se creará después
    'api_v1_bp'     # Se creará después
]

# Función para registrar todos los blueprints
def register_blueprints(app):
    """
    Registra todos los blueprints disponibles en la aplicación
    """
    blueprints_to_register = []
    
    # Auth blueprint (ya disponible)
    try:
        from .auth import auth
        blueprints_to_register.append(('auth', auth, '/auth'))
    except ImportError:
        print("Warning: Auth blueprint no disponible")
    
    # Admin blueprint (futuro)
    try:
        from .admin import admin_bp
        blueprints_to_register.append(('admin_bp', admin_bp, '/admin'))
    except ImportError:
        pass
    
    # Teacher blueprint (futuro)
    try:
        from .teacher import teacher_bp
        blueprints_to_register.append(('teacher_bp', teacher_bp, '/teacher'))
    except ImportError:
        pass
    
    # Student blueprint (futuro)
    try:
        from .student import student_bp
        blueprints_to_register.append(('student_bp', student_bp, '/student'))
    except ImportError:
        pass
    
    # API v1 blueprint (futuro)
    try:
        from .api.v1 import api_v1_bp
        blueprints_to_register.append(('api_v1_bp', api_v1_bp, '/api/v1'))
    except ImportError:
        pass
    
    # Registrar todos los blueprints encontrados
    for name, blueprint, url_prefix in blueprints_to_register:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        print(f"✅ Registrado: {name} en {url_prefix}")
    
    return len(blueprints_to_register)