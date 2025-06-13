from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import User
from app.services.security import SecurityService

def jwt_or_session_required(f):
    """Decorador que permite autenticación por JWT o sesión"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Intentar verificar JWT
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(user_id)
                if user:
                    return f(*args, **kwargs)
        except:
            pass
            
        # Si no hay JWT válido, verificar sesión
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return f(*args, **kwargs)
            
        return jsonify({'error': 'No autorizado'}), 401
    return decorated

def role_required(*roles):
    """Decorador que requiere un rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = None
            
            # Verificar JWT
            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
                if user_id:
                    user = User.query.get(user_id)
            except:
                pass
            
            # Verificar sesión si no hay JWT
            if not user:
                user = getattr(request, 'user', None)
            
            if not user or not user.is_authenticated:
                return jsonify({'error': 'No autorizado'}), 401
                
            if not any(user.has_role(role) for role in roles):
                return jsonify({'error': 'No tienes permisos suficientes'}), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def rate_limit(limit, key='ip'):
    """Decorador para limitar el número de peticiones"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Implementar lógica de límite de peticiones
            if key == 'ip':
                ip = request.remote_addr
                # Aquí iría la lógica para verificar límite por IP
                pass
            elif key == 'user':
                user = getattr(request, 'user', None)
                if user and user.is_authenticated:
                    # Aquí iría la lógica para verificar límite por usuario
                    pass
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_token(f):
    """Decorador para validar tokens de refresco"""
    @wraps(f)
    def decorated(*args, **kwargs):
        refresh_token = request.headers.get('Authorization')
        if not refresh_token:
            return jsonify({'error': 'Token de refresco requerido'}), 401
            
        if not SecurityService.verify_reset_token(refresh_token, user):
            return jsonify({'error': 'Token de refresco inválido'}), 401
            
        return f(*args, **kwargs)
    return decorated
