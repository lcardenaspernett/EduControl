# EduControl

Sistema de Gestión Escolar con Flask

## Características

- Autenticación por roles (Admin, Profesor, Estudiante)
- Dashboard personalizado por rol
- Gestión de usuarios y cursos
- Sistema de calificaciones y asistencia
- Interfaz moderna y responsive

## Requisitos

- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/educontrol.git
cd educontrol
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Inicializar la base de datos:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Ejecutar el servidor:
```bash
flask run
```

## Estructura del Proyecto

```
educontrol/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── main.py
│   └── static/
│       └── assets/
└── requirements.txt
```

## Licencia

MIT License
