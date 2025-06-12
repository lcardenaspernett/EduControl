from app import create_app, db
from app.models.user import User
from app.models.course import Course

app = create_app()

with app.app_context():
    # Obtener el profesor
    profesor = User.query.filter_by(username='profesor1').first()
    
    if profesor:
        # Crear cursos de ejemplo
        cursos = [
            {
                'name': 'Matemáticas Avanzadas',
                'code': 'MAT101',
                'credits': 4,
                'description': 'Curso avanzado de matemáticas'
            },
            {
                'name': 'Física General',
                'code': 'FIS101',
                'credits': 3,
                'description': 'Introducción a la física'
            },
            {
                'name': 'Programación I',
                'code': 'PRO101',
                'credits': 3,
                'description': 'Fundamentos de programación'
            }
        ]
        
        for curso_data in cursos:
            curso = Course(
                name=curso_data['name'],
                code=curso_data['code'],
                credits=curso_data['credits'],
                description=curso_data['description'],
                teacher_id=profesor.id
            )
            db.session.add(curso)
        
        db.session.commit()
        print('Cursos creados exitosamente')
    else:
        print('No se encontró el profesor')
