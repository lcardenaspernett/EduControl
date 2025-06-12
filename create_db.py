from app import create_app, db

print("Iniciando la creación de la base de datos...")
app = create_app()
with app.app_context():
    print("Creando todas las tablas...")
    db.create_all()
    print("Base de datos creada exitosamente!")
