from app import create_app, db
from app.models.user import User
from app.models.role import Role

app = create_app()

with app.app_context():
    print('Roles existentes:')
    roles = Role.query.all()
    for role in roles:
        print(f'ID: {role.id}, Nombre: {role.name}, Descripción: {role.description}')
    
    print('\nUsuarios existentes:')
    users = User.query.all()
    for user in users:
        print(f'ID: {user.id}, Usuario: {user.username}, Rol: {user.role.name if user.role else 'Sin rol'}, Email: {user.email}')
