from app import create_app
from app.models import db, User, Role
from datetime import datetime

print("Iniciando inicialización de la base de datos...")

# Crear aplicación
app = create_app()

with app.app_context():
    try:
        print("Creando todas las tablas...")
        db.create_all()
        
        # Crear roles básicos si no existen
        roles = [
            {"name": "admin", "description": "Administrador del sistema", 
             "can_manage_users": True, "can_manage_courses": True, "can_grade": True, "can_view_reports": True},
            {"name": "teacher", "description": "Profesor", 
             "can_manage_users": False, "can_manage_courses": True, "can_grade": True, "can_view_reports": True},
            {"name": "student", "description": "Estudiante", 
             "can_manage_users": False, "can_manage_courses": False, "can_grade": False, "can_view_reports": False}
        ]
        
        for role_data in roles:
            role = Role.query.filter_by(name=role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                db.session.add(role)
                print(f"Role {role_data['name']} creado")
        
        db.session.commit()
        print("Base de datos inicializada exitosamente!")
    except Exception as e:
        db.session.rollback()
        print(f"Error al inicializar la base de datos: {str(e)}")
