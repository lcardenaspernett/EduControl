from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models import User
from app.services.security import SecurityService
from app.utils.decorators import rate_limit

auth_jwt_bp = Blueprint('auth_jwt', __name__)

@auth_jwt_bp.route('/login', methods=['POST'])
@rate_limit(limit="5 per minute", key='ip')
def login():
    """Autenticar usuario y generar tokens JWT"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not SecurityService.check_password(user, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generar tokens
    tokens = SecurityService.create_tokens(user)
    return jsonify({
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'expires_at': tokens['expires_at'],
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role_name
        }
    })

@auth_jwt_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refrescar token de acceso"""
    current_user = get_jwt_identity()
    new_token = SecurityService.refresh_access_token(current_user)
    return jsonify({'access_token': new_token})

@auth_jwt_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Endpoint protegido para verificar tokens"""
    current_user = get_jwt_identity()
    return jsonify({'user_id': current_user})

@auth_jwt_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión y revocar tokens"""
    current_user = get_jwt_identity()
    refresh_token = request.headers.get('Authorization')
    if refresh_token:
        SecurityService.revoke_refresh_token(refresh_token)
    return jsonify({'message': 'Logged out successfully'})

@auth_jwt_bp.route('/password/reset/request', methods=['POST'])
def request_password_reset():
    """Solicitar reseteo de contraseña"""
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    if user:
        reset_token = SecurityService.generate_reset_token()
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        
        # Aquí iría el código para enviar el email
        # send_reset_password_email(user, reset_token)
    
    return jsonify({'message': 'Si existe una cuenta con ese email, se ha enviado un email de recuperación'})

@auth_jwt_bp.route('/password/reset/<token>', methods=['POST'])
def reset_password(token):
    """Resetear contraseña"""
    data = request.get_json()
    new_password = data.get('new_password')
    
    user = User.query.filter_by(password_reset_token=token).first()
    if not user or not SecurityService.verify_reset_token(token, user):
        return jsonify({'error': 'Token inválido o expirado'}), 400
        
    valid, error = SecurityService.validate_password(new_password)
    if not valid:
        return jsonify({'error': error}), 400
        
    user.set_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.session.commit()
    
    return jsonify({'message': 'Contraseña actualizada exitosamente'})
