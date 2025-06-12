from app import create_app
from app.models import User, Role, db
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Obtener el usuario administrador
    admin = User.query.get(1)
    if admin:
        print(f"Encontrado usuario administrador: {admin.email}")
        
        # Crear el rol admin si no existe
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrador del sistema',
                can_manage_users=True,
                can_manage_courses=True,
                can_grade=True,
                can_view_reports=True
            )
            db.session.add(admin_role)
            db.session.commit()
            print("Rol admin creado")
        
        # Actualizar el rol del usuario
        admin.role_id = admin_role.id
        admin.role_obj = admin_role
        
        # Establecer una contraseña predeterminada y nombres
        admin.first_name = 'Admin'
        admin.last_name = 'EduControl'
        admin.password_hash = generate_password_hash('admin123')
        
        db.session.commit()
        print("Usuario administrador actualizado con éxito")
        print(f"Email: {admin.email}")
        print(f"Contraseña: admin123")
    else:
        print("No se encontró el usuario administrador")
