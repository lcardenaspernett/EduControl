"""
Rutas JWT mejoradas para EduControl
Integra con modelos de seguridad y manejo de tokens
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash
from email_validator import validate_email, EmailNotValidError

from app import db
from app.extensions import limiter
from app.models.user import User
from app.models.token import RefreshToken
from app.config.security import SecurityConfig

# Crear blueprint JWT
auth_jwt_bp = Blueprint('auth_jwt', __name__, url_prefix='/api/auth')

@auth_jwt_bp.route('/login', methods=['POST'])
@limiter.limit(SecurityConfig.LOGIN_RATE_LIMIT)
def login():
    """
    Login con JWT - Versión completa con seguridad
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Obtener credenciales (soporta username o email)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if not username and not email:
            return jsonify({'error': 'Username or email is required'}), 400
        
        # Buscar usuario por username o email
        user = None
        if email:
            try:
                validate_email(email)
                user = User.query.filter_by(email=email).first()
            except EmailNotValidError:
                return jsonify({'error': 'Invalid email format'}), 400
        elif username:
            user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verificar si la cuenta está bloqueada
        now = datetime.utcnow()
        if user.locked_until and user.locked_until > now:
            time_left = user.locked_until - now
            minutes_left = int(time_left.total_seconds() / 60)
            return jsonify({
                'error': 'Account temporarily locked',
                'locked_until': user.locked_until.isoformat(),
                'minutes_remaining': minutes_left
            }), 423
        
        # Verificar contraseña
        if not check_password_hash(user.password_hash, password):
            # Incrementar intentos fallidos
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            user.last_failed_login = now
            user.last_login_attempt = now
            
            # Bloquear cuenta si excede máximo de intentos
            if user.failed_login_attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                user.locked_until = now + SecurityConfig.LOCKOUT_DURATION
                db.session.commit()
                
                return jsonify({
                    'error': 'Account locked due to too many failed attempts',
                    'locked_until': user.locked_until.isoformat(),
                    'attempts_made': user.failed_login_attempts
                }), 423
            
            db.session.commit()
            attempts_remaining = SecurityConfig.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
            return jsonify({
                'error': 'Invalid credentials',
                'attempts_remaining': attempts_remaining
            }), 401
        
        # Verificar si el usuario está activo
        if not user.is_active:
            return jsonify({'error': 'Account deactivated'}), 403
        
        # Login exitoso - resetear campos de seguridad
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.locked_until = None
        user.last_login = now
        user.last_login_attempt = now
        
        # Crear tokens JWT
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role_name,
                'email': user.email,
                'username': user.username
            }
        )
        
        refresh_token_str = create_refresh_token(identity=user.id)
        
        # Guardar refresh token en BD
        refresh_token = RefreshToken(user_id=user.id)
        refresh_token.token = refresh_token_str
        db.session.add(refresh_token)
        db.session.commit()
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token_str,
            'token_type': 'Bearer',
            'expires_in': int(SecurityConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role_name,
                'last_login': user.last_login.isoformat()
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_jwt_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refrescar access token usando refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 404
        
        # Crear nuevo access token
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role_name,
                'email': user.email,
                'username': user.username
            }
        )
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': int(SecurityConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_jwt_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Cerrar sesión y revocar refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Buscar y revocar refresh tokens del usuario
        refresh_tokens = RefreshToken.query.filter_by(
            user_id=current_user_id,
            revoked=False
        ).all()
        
        for token in refresh_tokens:
            token.revoked = True
        
        db.session.commit()
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_jwt_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtener información del usuario actual
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role_name,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_jwt_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_token():
    """
    Validar si el token JWT es válido
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'valid': False, 'error': 'User not found or inactive'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': current_user_id,
            'role': user.role_name,
            'username': user.username
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token validation error: {str(e)}")
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401

@auth_jwt_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Endpoint protegido para testing
    """
    try:
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        
        return jsonify({
            'message': 'Access granted to protected resource',
            'user_id': current_user_id,
            'claims': jwt_claims
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Protected endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Manejadores de errores específicos para JWT
@auth_jwt_bp.errorhandler(422)
def handle_unprocessable_entity(e):
    """Manejar errores de JWT malformados"""
    return jsonify({'error': 'Invalid token format'}), 422

@auth_jwt_bp.errorhandler(401)
def handle_unauthorized(e):
    """Manejar errores de autorización"""
    return jsonify({'error': 'Invalid or expired token'}), 401