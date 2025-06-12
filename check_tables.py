from app import create_app, db

app = create_app()
with app.app_context():
    print('Tablas en la base de datos:', db.engine.table_names())
