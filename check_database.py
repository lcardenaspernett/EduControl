import os
import sqlite3

db_path = 'educontrol.db'

# Verificar si el archivo existe
print(f'Verificando si {db_path} existe...')
exists = os.path.exists(db_path)
print(f'Archivo existe: {exists}')

if exists:
    # Intentar abrir la base de datos
    try:
        conn = sqlite3.connect(db_path)
        print('Conexión exitosa a la base de datos')
        conn.close()
    except sqlite3.Error as e:
        print(f'Error al conectar a la base de datos: {e}')
