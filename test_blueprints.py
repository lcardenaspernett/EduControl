#!/usr/bin/env python3
"""
Test completo del sistema de blueprints de EduControl
Versión actualizada con mejor manejo de errores y verificaciones
"""
import sys
import os
from flask import Flask

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Prueba que todos los módulos se importen correctamente"""
    print("🔍 Iniciando pruebas de importación...")
    
    try:
        print("   ✓ Importando Flask...")
        from flask import Flask
        
        print("   ✓ Importando Flask-Login...")
        from flask_login import LoginManager
        
        print("   ✓ Importando SQLAlchemy...")
        from flask_sqlalchemy import SQLAlchemy
        
        print("   ✓ Importando models...")
        from app.models.models import User as Usuario
        
        print("   ✓ Importando blueprint auth...")
        from app.blueprints.auth import auth_bp as auth_bp
        
        print("   ✓ Importando blueprint main...")
        from app.blueprints.main import main_bp as main_bp
        
        print("   ✓ Importando función de registro de blueprints...")
        from app.blueprints import register_blueprints
        
        print("✅ Todas las importaciones exitosas!\n")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Asegúrate de que todos los archivos existan y estén correctamente configurados\n")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}\n")
        return False

def test_app_creation():
    """Prueba la creación de la aplicación Flask"""
    print("🔍 Probando creación de aplicación...")
    
    try:
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True
        
        print("   ✓ Aplicación Flask creada correctamente")
        return app
        
    except Exception as e:
        print(f"❌ Error creando aplicación: {e}")
        return None

def test_database_setup(app):
    """Prueba la configuración de la base de datos"""
    print("🔍 Probando configuración de base de datos...")
    
    try:
        from app.models import db
        
        # Inicializar la base de datos con la app
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            print("   ✓ Base de datos inicializada correctamente")
            
        return True
        
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        return False

def test_login_manager_setup(app):
    """Prueba la configuración de Flask-Login"""
    print("🔍 Probando configuración de Flask-Login...")
    
    try:
        from flask_login import LoginManager
        from app.models.models import User as Usuario
        
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        print("   ✓ Flask-Login configurado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando Flask-Login: {e}")
        return False

def test_blueprints_registration(app):
    """Prueba el registro de blueprints"""
    print("🔍 Probando registro de blueprints...")
    
    try:
        from app.blueprints import register_blueprints
        
        # Registrar blueprints
        register_blueprints(app)
        
        # Verificar que los blueprints están registrados
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        
        expected_blueprints = ['auth', 'main']
        for bp_name in expected_blueprints:
            if bp_name in blueprint_names:
                print(f"   ✓ Blueprint '{bp_name}' registrado correctamente")
            else:
                print(f"   ❌ Blueprint '{bp_name}' NO encontrado")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error registrando blueprints: {e}")
        return False

def test_routes(app):
    """Prueba que las rutas principales funcionen"""
    print("🔍 Probando rutas principales...")
    
    try:
        with app.test_client() as client:
            # Probar ruta principal
            print("   ✓ Probando ruta principal (/)...")
            response = client.get('/')
            if response.status_code == 200:
                print("   ✓ Ruta principal funciona correctamente")
            else:
                print(f"   ❌ Ruta principal falló: {response.status_code}")
                return False
            
            # Probar que el contenido incluye elementos esperados
            content = response.get_data(as_text=True)
            if 'EduControl' in content:
                print("   ✓ Contenido de la página principal correcto")
            else:
                print("   ❌ Contenido de la página principal incorrecto")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando rutas: {e}")
        return False

def test_user_model():
    """Prueba el modelo User"""
    print("🔍 Probando modelo User...")
    
    try:
        from app.models.models import User as Usuario
        
        # Verificar que el modelo tiene los métodos necesarios
        user = User()
        
        # Verificar métodos básicos de Flask-Login
        methods_to_check = ['is_authenticated', 'is_active', 'is_anonymous', 'get_id']
        for method in methods_to_check:
            if hasattr(user, method):
                print(f"   ✓ Método '{method}' presente")
            else:
                print(f"   ❌ Método '{method}' faltante")
                return False
        
        # Verificar métodos de rol personalizados
        role_methods = ['is_admin', 'is_teacher', 'is_student']
        for method in role_methods:
            if hasattr(user, method):
                print(f"   ✓ Método de rol '{method}' presente")
            else:
                print(f"   ❌ Método de rol '{method}' faltante")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando modelo User: {e}")
        return False

def test_template_rendering(app):
    """Prueba que los templates se rendericen correctamente"""
    print("🔍 Probando renderizado de templates...")
    
    try:
        with app.test_client() as client:
            with app.app_context():
                response = client.get('/')
                content = response.get_data(as_text=True)
                
                # Verificar elementos clave del template
                expected_elements = [
                    'EduControl',
                    'Gestión de Cursos',
                    'Control de Estudiantes',
                    'Sistema integral de gestión educativa'
                ]
                
                for element in expected_elements:
                    if element in content:
                        print(f"   ✓ Elemento '{element}' encontrado en template")
                    else:
                        print(f"   ❌ Elemento '{element}' NO encontrado en template")
                        return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando templates: {e}")
        return False

def run_full_test():
    """Ejecuta todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS COMPLETAS DE EDUCONTROL")
    print("=" * 50)
    
    # Lista de pruebas
    tests = [
        ("Importaciones", test_imports),
        ("Creación de aplicación", lambda: test_app_creation()),
        ("Modelo User", test_user_model),
    ]
    
    results = []
    app = None
    
    # Ejecutar pruebas básicas
    for test_name, test_func in tests:
        if test_name == "Creación de aplicación":
            app = test_func()
            success = app is not None
        else:
            success = test_func()
        
        results.append((test_name, success))
        
        if not success and test_name in ["Importaciones", "Creación de aplicación"]:
            print(f"❌ Prueba crítica '{test_name}' falló. Deteniendo pruebas.")
            break
    
    # Si tenemos una app válida, ejecutar pruebas que la requieren
    if app is not None:
        app_tests = [
            ("Configuración de base de datos", lambda: test_database_setup(app)),
            ("Configuración de Flask-Login", lambda: test_login_manager_setup(app)),
            ("Registro de blueprints", lambda: test_blueprints_registration(app)),
            ("Rutas principales", lambda: test_routes(app)),
            ("Renderizado de templates", lambda: test_template_rendering(app)),
        ]
        
        for test_name, test_func in app_tests:
            success = test_func()
            results.append((test_name, success))
    
    # Mostrar resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status:12} - {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"✅ Pruebas exitosas: {passed}")
    print(f"❌ Pruebas fallidas: {failed}")
    print(f"📈 Porcentaje de éxito: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! Tu aplicación está lista.")
    else:
        print(f"\n⚠️  {failed} prueba(s) fallaron. Revisa los errores arriba.")
    
    print("=" * 50)

if __name__ == "__main__":
    run_full_test()