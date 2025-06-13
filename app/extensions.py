from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicializar extensiones
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def init_security_extensions(app):
    """Inicializar extensiones de seguridad"""
    jwt.init_app(app)
    limiter.init_app(app)
    setup_jwt_callbacks(app)

def setup_jwt_callbacks(app):
    """Configurar callbacks de JWT"""
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Obtener identidad del usuario para JWT"""
        return user.id
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Cargar usuario desde JWT payload"""
        from app.models.user import User
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity).one_or_none()
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Manejar tokens expirados"""
        return {
            'message': 'Token has expired',
            'error': 'token_expired'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Manejar tokens inválidos"""
        return {
            'message': 'Invalid token',
            'error': 'invalid_token'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Manejar tokens faltantes"""
        return {
            'message': 'Authorization token is required',
            'error': 'authorization_required'
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Manejar tokens revocados"""
        return {
            'message': 'Token has been revoked',
            'error': 'token_revoked'
        }, 401
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Verificar si un token está en la lista negra"""
        from app.models.token import RefreshToken
        jti = jwt_payload['jti']
        token = RefreshToken.query.filter_by(jti=jti).first()
        return token is None or token.revoked
