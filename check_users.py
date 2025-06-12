from app import create_app
from app.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"Total usuarios en la base de datos: {len(users)}")
    
    if users:
        print("\nUsuarios encontrados:")
        for user in users:
            print(f"- {user.email} (ID: {user.id}) - Rol: {user.role}")
    else:
        print("No hay usuarios en la base de datos")
