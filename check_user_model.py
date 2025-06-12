from app import create_app
from app.models import User

app = create_app()

with app.app_context():
    # Verificar campos del modelo User
    print("Campos del modelo User:")
    for column in User.__table__.columns:
        print(f"- {column.name} ({column.type})")
    
    # Verificar métodos del modelo User
    print("\nMétodos del modelo User:")
    for method in dir(User):
        if not method.startswith('_'):
            print(f"- {method}")
    
    # Intentar crear un nuevo usuario
    try:
        new_user = User(
            username='test_user',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role_id=1
        )
        print("\nUsuario creado exitosamente")
    except Exception as e:
        print(f"\nError al crear usuario: {str(e)}")
