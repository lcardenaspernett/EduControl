import os
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

    # ==================== CONFIGURACIÓN ====================
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-desarrollo'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///educontrol.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # ==================== IMPORTAR MODELOS ====================
    # Importar modelos ANTES del app_context y blueprints
    try:
        from app.models import User, Course, Grade, Attendance, Subject, Role, Configuration
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
            
        print("✅ Modelos importados correctamente")
            
    except ImportError as e:
        print(f"❌ Error importando modelos: {e}")
        
        @login_manager.user_loader
        def load_user(user_id):
            return None

    # ==================== REGISTRAR BLUEPRINTS ====================
    
    # 1. Blueprint principal (rutas de inicio)
    try:
        from app.blueprints.main import main_bp
        app.register_blueprint(main_bp)
        print("✅ Main blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando main blueprint: {e}")

    # 2. Blueprint de autenticación
    try:
        from app.blueprints.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ Auth blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando auth blueprint: {e}")

    # 3. Blueprint de administrador
    try:
        from app.blueprints.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        print("✅ Admin blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando admin blueprint: {e}")

    # 4. Blueprint de profesor
    try:
        from app.blueprints.teacher import teacher_bp
        app.register_blueprint(teacher_bp, url_prefix='/teacher')
        print("✅ Teacher blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando teacher blueprint: {e}")

    # 5. Blueprint de estudiante
    try:
        from app.blueprints.student import student_bp
        app.register_blueprint(student_bp, url_prefix='/student')
        print("✅ Student blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando student blueprint: {e}")

    # 6. Blueprint de API
    try:
        from app.blueprints.api.v1 import api_v1_bp
        app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
        print("✅ API v1 blueprint registrado")
    except ImportError as e:
        print(f"❌ Error importando API v1 blueprint: {e}")

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
        """Inicializar la base de datos"""
        try:
            with app.app_context():
                db.create_all()
                print("✅ Base de datos inicializada correctamente")
                
                # Crear roles básicos
                from app.models import Role
                
                roles_default = [
                    {'name': 'admin', 'description': 'Administrador del sistema', 
                     'can_manage_users': True, 'can_manage_courses': True, 'can_grade': True, 'can_view_reports': True},
                    {'name': 'teacher', 'description': 'Profesor', 
                     'can_manage_courses': False, 'can_grade': True, 'can_view_reports': True},
                    {'name': 'student', 'description': 'Estudiante', 
                     'can_manage_courses': False, 'can_grade': False, 'can_view_reports': False}
                ]
                
                for role_data in roles_default:
                    if not Role.query.filter_by(name=role_data['name']).first():
                        role = Role(**role_data)
                        db.session.add(role)
                
                db.session.commit()
                print("✅ Roles básicos creados")
                
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")

    @app.cli.command()
    def create_admin():
        """Crear usuario administrador"""
        try:
            with app.app_context():
                from app.models import User
                from werkzeug.security import generate_password_hash
                
                # Verificar si ya existe
                if User.query.filter_by(username='admin').first():
                    print("⚠️ El usuario admin ya existe")
                    return
                
                admin = User(
                    username='admin',
                    email='admin@educontrol.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    first_name='Administrador',
                    last_name='Sistema',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuario administrador creado: admin/admin123")
                
        except Exception as e:
            print(f"❌ Error creando usuario admin: {e}")

    @app.cli.command()
    def create_sample_data():
        """Crear datos de ejemplo"""
        try:
            with app.app_context():
                from app.models import User, Subject, Course
                
                # Crear profesores de ejemplo
                if not User.query.filter_by(username='prof1').first():
                    prof1 = User(
                        username='prof1',
                        email='profesor1@educontrol.com',
                        role='teacher',
                        first_name='María',
                        last_name='García'
                    )
                    prof1.set_password('prof123')
                    db.session.add(prof1)
                
                # Crear estudiantes de ejemplo
                if not User.query.filter_by(username='est1').first():
                    est1 = User(
                        username='est1',
                        email='estudiante1@educontrol.com',
                        role='student',
                        first_name='Juan',
                        last_name='Pérez'
                    )
                    est1.set_password('est123')
                    db.session.add(est1)
                
                # Crear materias de ejemplo
                if not Subject.query.filter_by(code='MAT001').first():
                    math = Subject(
                        name='Matemáticas I',
                        code='MAT001',
                        description='Curso básico de matemáticas',
                        credits=3
                    )
                    db.session.add(math)
                
                db.session.commit()
                print("✅ Datos de ejemplo creados")
                
        except Exception as e:
            print(f"❌ Error creando datos de ejemplo: {e}")

    # Mostrar rutas registradas en modo debug
    if app.debug:
        print("\n=== RUTAS REGISTRADAS ===")
        for rule in app.url_map.iter_rules():
            print(f"{rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
        print("========================\n")

    return app