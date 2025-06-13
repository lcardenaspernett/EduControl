# app/services/security.py
"""
Servicio de seguridad para EduControl
Maneja validación de contraseñas, bloqueo de cuentas y creación de tokens JWT
"""

import hashlib
import re
from datetime import datetime, timedelta
from flask import request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti
from app.models.user import User
from app.models.token import RefreshToken
from app.models.database import db


class SecurityService:
    """Servicio para operaciones de seguridad"""
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validar fortaleza de contraseña
        
        Args:
            password (str): Contraseña a validar
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe tener al menos una letra mayúscula"
        
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe tener al menos una letra minúscula"
        
        if not re.search(r'\d', password):
            return False, "La contraseña debe tener al menos un número"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "La contraseña debe tener al menos un carácter especial"
        
        return True, "Contraseña válida"
    
    @staticmethod
    def check_account_lockout(user):
        """
        Verificar si la cuenta está bloqueada
        
        Args:
            user (User): Usuario a verificar
            
        Returns:
            tuple: (is_locked: bool, message: str)
        """
        if hasattr(user, 'locked_until') and user.locked_until and user.locked_until > datetime.utcnow():
            return True, f"Cuenta bloqueada hasta {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
        return False, ""
    
    @staticmethod
    def handle_failed_login(user):
        """
        Manejar intento de login fallido
        
        Args:
            user (User): Usuario con login fallido
            
        Returns:
            tuple: (is_locked: bool, message: str)
        """
        # Inicializar campos si no existen
        if not hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
        if not hasattr(user, 'last_failed_login'):
            user.last_failed_login = None
        if not hasattr(user, 'locked_until'):
            user.locked_until = None
            
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        user.last_failed_login = datetime.utcnow()
        
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
        if user.failed_login_attempts >= max_attempts:
            lockout_duration = current_app.config.get('LOCKOUT_DURATION', timedelta(minutes=15))
            user.locked_until = datetime.utcnow() + lockout_duration
            user.failed_login_attempts = 0
            db.session.commit()
            return True, "Cuenta bloqueada por exceso de intentos fallidos"
        
        db.session.commit()
        return False, f"Intento fallido {user.failed_login_attempts}"
    
    @staticmethod
    def handle_successful_login(user):
        """
        Manejar login exitoso
        
        Args:
            user (User): Usuario con login exitoso
        """
        # Inicializar campos si no existen
        if not hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
        if not hasattr(user, 'locked_until'):
            user.locked_until = None
            
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_tokens(user):
        """
        Crear tokens JWT para un usuario
        
        Args:
            user (User): Usuario para crear tokens
            
        Returns:
            dict: Diccionario con tokens y metadata
        """
        try:
            # Crear access token
            access_token = create_access_token(identity=user)
            
            # Crear refresh token
            refresh_token = create_refresh_token(identity=user)
            refresh_jti = get_jti(refresh_token)
            
            # Hashear y guardar refresh token
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            
            # Obtener información del cliente
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')[:500]
            
            refresh_token_obj = RefreshToken(
                user_id=user.id,
                token_hash=token_hash,
                jti=refresh_jti,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(refresh_token_obj)
            db.session.commit()
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            }
            
        except Exception as e:
            current_app.logger.error(f"Error creating tokens: {str(e)}")
            raise e
    
    @staticmethod
    def revoke_token(jti):
        """
        Revocar un token específico
        
        Args:
            jti (str): JWT ID del token a revocar
            
        Returns:
            bool: True si se revocó exitosamente
        """
        try:
            token = RefreshToken.query.filter_by(jti=jti).first()
            if token:
                token.revoke()
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error revoking token: {str(e)}")
            return False
    
    @staticmethod
    def get_client_info():
        """
        Obtener información del cliente para auditoría
        
        Returns:
            dict: Información del cliente
        """
        return {
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', '')[:500],
            'timestamp': datetime.utcnow()
        }
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        Limpiar tokens expirados de la base de datos
        
        Returns:
            int: Número de tokens eliminados
        """
        try:
            return RefreshToken.cleanup_expired()
        except Exception as e:
            current_app.logger.error(f"Error cleaning up tokens: {str(e)}")
            return 0