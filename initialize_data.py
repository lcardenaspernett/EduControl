from app import app, db
from app.models import User, Role
from werkzeug.security import generate_password_hash

with app.app_context():
    # Crear roles si no existen
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrador del sistema')
        db.session.add(admin_role)
        db.session.commit()

    # Crear usuario de prueba
    user = User.query.filter_by(username='admin').first()
    if not user:
        user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='EduControl',
            role_id=admin_role.id
        )
        db.session.add(user)
        db.session.commit()
        print('Usuario de prueba creado: admin/admin123')
    else:
        print('El usuario admin ya existe')
