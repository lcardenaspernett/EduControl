from flask import Flask
from flask_migrate import Migrate
from app.models.database import db
from app.models.user import User
from app.models.token import RefreshToken

migrate = Migrate()

def init_app(app: Flask):
    """Inicializar comandos CLI"""
    migrate.init_app(app, db)
    
    @app.cli.command()
    def init_db():
        """Inicializar la base de datos con los nuevos campos de seguridad"""
        print("🔍 Verificando campos de seguridad en la base de datos...")
        users = User.query.all()
        
        for user in users:
            # Inicializar campos de seguridad si no existen
            if user.failed_login_attempts is None:
                user.failed_login_attempts = 0
            if user.locked_until is None:
                user.locked_until = None
            if user.last_failed_login is None:
                user.last_failed_login = None
            if user.password_reset_token is None:
                user.password_reset_token = None
            if user.password_reset_expires is None:
                user.password_reset_expires = None
                
        db.session.commit()
        print("✅ Campos de seguridad inicializados para todos los usuarios")
        
    @app.cli.command()
    def cleanup_tokens():
        """Limpiar tokens expirados de la base de datos"""
        count = RefreshToken.cleanup_expired()
        print(f"✅ {count} tokens expirados eliminados")
        
    @app.cli.command()
    def check_security():
        """Verificar la seguridad de las cuentas"""
        users = User.query.all()
        locked_users = [u for u in users if u.locked_until and u.locked_until > datetime.utcnow()]
        
        print(f"🔍 Verificando {len(users)} cuentas...")
        print(f"⚠️ {len(locked_users)} cuentas bloqueadas:")
        for user in locked_users:
            print(f"  - {user.username} bloqueada hasta {user.locked_until}")
        
        print("✅ Verificación de seguridad completada")
