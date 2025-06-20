import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from app.extensions import init_security_extensions
from app.config.security import SecurityConfig
from app.blueprints.auth.routes_jwt import auth_jwt_bp
from app.cli import init_app as init_cli

# Inicializar extensiones
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(__name__, template_folder='app/templates')

    # ==================== CONFIGURACIÓN ====================
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-desarrollo'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///educontrol.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración de seguridad
    if os.environ.get('FLASK_ENV') == 'testing':
        from app.config.testing import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(SecurityConfig)

    # ==================== INICIALIZAR EXTENSIONES ====================
    # IMPORTANTE: Usar la misma instancia de SQLAlchemy que está en app/__init__.py
    from app import db  # Importar la instancia de SQLAlchemy de app/__init__.py
    db.init_app(app)

    # Luego las otras extensiones
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Inicializar extensiones de seguridad
    init_security_extensions(app)

    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # ==================== USER LOADER ====================
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from app.models import User  # Importar desde el archivo unificado
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error cargando usuario: {e}")
            return None

    # ==================== REGISTRAR BLUEPRINTS ====================
    # Registrar blueprint de autenticación
    try:
        from app.blueprints.auth import auth_bp
        app.register_blueprint(auth_bp)
        print("✅ Auth blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando auth blueprint: {e}")

    # Registrar blueprint principal
    try:
        from app.blueprints.main import main_bp
        app.register_blueprint(main_bp, url_prefix='')
        print("✅ Main blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando main blueprint: {e}")

    # Registrar blueprint API v1
    try:
        from app.blueprints.api.v1 import api_v1_bp
        app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
        print("✅ API v1 blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando API v1 blueprint: {e}")

    # Registrar blueprint JWT
    try:
        app.register_blueprint(auth_jwt_bp, url_prefix='/api/auth')
        print("✅ JWT auth blueprint registrado")
    except Exception as e:
        print(f"❌ Error registrando JWT auth blueprint: {e}")
    
    # Inicializar comandos CLI
    try:
        init_cli(app)
        print("✅ Comandos CLI registrados")
    except Exception as e:
        print(f"❌ Error inicializando CLI: {e}")

    # ==================== MANEJADORES DE ERRORES ====================
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401

    # ==================== FILTROS Y CONTEXTO ====================
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.context_processor
    def utility_processor():
        return {
            'current_year': datetime.now().year,
            'app_name': 'EduControl',
            'current_date': datetime.now()
        }

    # ==================== COMANDOS CLI ====================
    @app.cli.command()
    def init_db():
        db.create_all()
        print("✅ Base de datos inicializada")

    @app.cli.command()
    def create_admin():
        from app.models import User, Role
        from werkzeug.security import generate_password_hash

        # Buscar rol de admin
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("❌ Rol 'admin' no encontrado. Crea los roles primero.")
            return

        existing_admin = User.query.filter_by(role_id=admin_role.id).first()
        if existing_admin:
            print(f"Ya existe un administrador: {existing_admin.username}")
            return

        admin = User(
            username='admin',
            email='admin@educontrol.com',
            password='admin123',  # Usar el setter de password
            role_id=admin_role.id,
            first_name='Administrador',
            last_name='Sistema',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario administrador creado: admin/admin123")

    if app.debug:
        print("\n=== RUTAS REGISTRADAS ===")
        for rule in app.url_map.iter_rules():
            print(f"{rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
        print("========================\n")

    return app

if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        try:
            from app import db
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")

    try:
        print("🚀 Iniciando servidor Flask...")
        print("📍 Aplicación disponible en: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Error iniciando el servidor: {e}")