from app import create_app, db
from app.models import User, Role
from werkzeug.security import generate_password_hash

def init_database():
    app = create_app()
    with app.app_context():
        # Crear tablas
        print("Creando tablas...")
        db.create_all()
        
        # Crear roles básicos
        roles = [
            {
                "name": "admin",
                "description": "Administrador del sistema",
                "can_manage_users": True,
                "can_manage_courses": True,
                "can_grade": True,
                "can_view_reports": True
            },
            {
                "name": "teacher",
                "description": "Profesor",
                "can_manage_users": False,
                "can_manage_courses": True,
                "can_grade": True,
                "can_view_reports": True
            },
            {
                "name": "student",
                "description": "Estudiante",
                "can_manage_users": False,
                "can_manage_courses": False,
                "can_grade": False,
                "can_view_reports": False
            }
        ]
        
        for role_data in roles:
            if not Role.query.filter_by(name=role_data["name"]).first():
                role = Role(**role_data)
                db.session.add(role)
                print(f"Rol {role_data['name']} creado")

        # Crear usuario admin por defecto
        if not User.query.filter_by(username='admin').first():
            admin_role = Role.query.filter_by(name='admin').first()
            admin = User(
                username='admin',
                email='admin@educontrol.com',
                first_name='Admin',
                last_name='Sistema',
                role_id=admin_role.id
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Usuario admin creado")

        db.session.commit()
        print("¡Base de datos inicializada correctamente!")

if __name__ == "__main__":
    init_database()
