from app import create_app, db
from app.models.user import User
from app.models.role import Role

app = create_app()

with app.app_context():
    # Crear usuario estudiante de prueba
    username = 'estudiante1'
    email = 'estudiante1@educontrol.com'
    password = 'estudiante123'
    first_name = 'María'
    last_name = 'García'

    # Verificar si el usuario ya existe
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f'El usuario {username} ya existe.')
    else:
        # Crear nuevo usuario
        student = User(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role_id=3  # ID del rol student
        )
        db.session.add(student)
        db.session.commit()
        print(f'Usuario estudiante creado exitosamente: {username}')
