from app import create_app, db  # Importar db desde app
from app.models.user import User
from app.models.role import Role
from werkzeug.security import generate_password_hash

# Crear la app
app = create_app()

with app.app_context():
    print("Creando usuario de prueba...")
    
    # Crear rol admin si no existe
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator')
        db.session.add(admin_role)
        db.session.commit()
        print("✅ Rol admin creado")
    
    # Crear usuario de prueba
    test_user = User.query.filter_by(username='admin').first()
    if not test_user:
        test_user = User(
            username='admin',
            email='admin@educontrol.com',
            password='admin123',  # Cambiar a password en lugar de password_hash
            first_name='Admin',
            last_name='User',
            role_id=admin_role.id,
            is_active=True
        )
        db.session.add(test_user)
        db.session.commit()
        print("✅ Usuario de prueba creado:")
        print("   Username: admin")
        print("   Email: admin@educontrol.com")
        print("   Password: admin123")
    else:
        print("✅ Usuario admin ya existe")
        print("   Username: admin")
        print("   Email: admin@educontrol.com")