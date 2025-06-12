from app import create_app, db
from app.models.user import User
from app.models.role import Role

app = create_app()

with app.app_context():
    # Verificar la estructura de la tabla users
    print('\nEstructura de la tabla users:')
    print(db.inspect(db.engine).get_columns('users'))
    
    # Verificar los roles existentes con más detalle
    print('\nRoles existentes con ID:')
    roles = Role.query.all()
    for role in roles:
        print(f'ID: {role.id}, Nombre: {role.name}, Descripción: {role.description}')
    
    # Verificar si existe un usuario con rol teacher
    print('\nUsuarios con rol teacher:')
    users = User.query.filter_by(role_id=2).all()
    for user in users:
        print(f'ID: {user.id}, Usuario: {user.username}, Email: {user.email}')
