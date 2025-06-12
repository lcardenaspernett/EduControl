from app import create_app, db
from app.models.user import User
from app.models.role import Role

# Crear la aplicación
app = create_app()

with app.app_context():
    # Verificar si el rol de teacher existe
    teacher_role = Role.query.filter_by(name='teacher').first()
    if not teacher_role:
        # Crear el rol de teacher
        teacher_role = Role(
            name='teacher',
            description='Profesor',
            can_manage_courses=True,
            can_grade=True,
            can_view_reports=True
        )
        db.session.add(teacher_role)
        db.session.commit()
        print('Rol de teacher creado exitosamente')
    else:
        print('Rol de teacher ya existe')

    # Verificar si el rol de admin existe
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        # Crear el rol de admin
        admin_role = Role(name='admin', description='Administrador')
        db.session.add(admin_role)
        db.session.commit()
        print('Rol de admin creado exitosamente')
    else:
        print('Rol de admin ya existe')

    # Crear usuario docente de prueba
    username = 'profesor1'
    email = 'profesor1@educontrol.com'
    password = 'profesor123'
    first_name = 'Juan'
    last_name = 'Pérez'

    # Verificar si el usuario ya existe
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f'El usuario {username} ya existe.')
    else:
        # Crear nuevo usuario
        teacher = User(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role_id=2  # Usar el ID del rol teacher que ya existe
        )
        
        # Verificar que el rol existe
        teacher_role = Role.query.get(2)
        if teacher_role:
            teacher.role_id = 2
            db.session.add(teacher)
            db.session.commit()
            print(f'Usuario docente creado exitosamente: {username}')
        else:
            print('Error: El rol teacher no existe en la base de datos')

    # Verificar el usuario creado
    teacher = User.query.filter_by(username=username).first()
    if teacher:
        print(f'Usuario docente creado: {teacher.username} ({teacher.role.name})')
