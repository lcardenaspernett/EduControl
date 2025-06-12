from app import create_app, db
from app.models.user import User
from app.models.role import Role
from sqlalchemy import text

# Crear la aplicación
app = create_app()

with app.app_context():
    # Verificar si la columna role existe
    inspector = db.inspect(db.engine)
    columns = inspector.get_columns('users')
    
    if any(col['name'] == 'role' for col in columns):
        print('Eliminando la columna role redundante...')
        
        # Crear una nueva tabla temporal
        db.session.execute(text("""
            CREATE TABLE users_temp (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) NOT NULL,
                email VARCHAR(120) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME,
                updated_at DATETIME,
                last_login DATETIME,
                role_id INTEGER NOT NULL,
                phone VARCHAR(20),
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """))
        
        # Copiar datos a la tabla temporal
        db.session.execute(text("""
            INSERT INTO users_temp (
                id, username, email, password_hash, first_name,
                last_name, is_active, created_at, updated_at,
                last_login, role_id, phone
            )
            SELECT 
                id, username, email, password_hash, first_name,
                last_name, is_active, created_at, updated_at,
                last_login, role_id, phone
            FROM users
        """))
        
        # Eliminar la tabla original y renombrar la temporal
        db.session.execute(text("DROP TABLE users"))
        db.session.execute(text("ALTER TABLE users_temp RENAME TO users"))
        
        # Actualizar los índices y constraints
        db.session.execute(text("""
            CREATE UNIQUE INDEX idx_users_username ON users(username)
        """))
        db.session.execute(text("""
            CREATE UNIQUE INDEX idx_users_email ON users(email)
        """))
        
        db.session.commit()
        print('Base de datos actualizada exitosamente')
    else:
        print('La columna role ya ha sido eliminada')
