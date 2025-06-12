# app/blueprints/api/v1/routes.py
from flask import jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
from app import db
from app.models import User, Course, Subject, Grade, Attendance, Assignment, Submission, Role
from . import api_v1_bp
# ================== ROLES ==================
ADMIN_ROLE = 'admin'
TEACHER_ROLE = 'teacher'
STUDENT_ROLE = 'student'

def api_key_required(f):
    """Decorator para requerir API key (opcional para futuro)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Por ahora solo requiere login, en el futuro se puede agregar API key
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para endpoints solo de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def teacher_or_admin_required(f):
    """Decorator para endpoints de profesores y admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name not in ['teacher', 'admin']:
            return jsonify({'error': 'Teacher or admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ================== DOCUMENTACION AUTOMATICA ==================
@api_v1_bp.route('/docs', methods=['GET'])
def api_docs():
    """Devuelve una documentación básica de los endpoints disponibles"""
    return jsonify({
        'endpoints': [
            {'path': '/status', 'method': 'GET', 'description': 'Estado de la API'},
            {'path': '/me', 'method': 'GET', 'description': 'Información del usuario actual'},
            {'path': '/users', 'method': 'GET|POST', 'description': 'Lista y creación de usuarios (admin)'},
            {'path': '/users/<id>', 'method': 'GET|PUT|DELETE', 'description': 'Gestión de usuario por ID'},
            {'path': '/courses', 'method': 'GET|POST', 'description': 'Lista y creación de cursos'},
            {'path': '/subjects', 'method': 'GET|POST', 'description': 'Lista y creación de materias'},
            {'path': '/grades', 'method': 'GET|POST', 'description': 'Lista y registro de calificaciones'},
            {'path': '/attendance', 'method': 'GET|POST', 'description': 'Registros de asistencia'},
            {'path': '/assignments', 'method': 'GET|POST', 'description': 'Lista y creación de tareas'},
            {'path': '/submissions', 'method': 'GET|POST', 'description': 'Lista y envío de entregas'},
        ]
    })
# ================== ENDPOINTS DE INFORMACIÓN GENERAL ==================

@api_v1_bp.route('/status', methods=['GET'])
def status():
    """Estado de la API"""
    return jsonify({
        'status': 'active',
        'version': '1.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_v1_bp.route('/me', methods=['GET'])
@login_required
@api_key_required
def current_user_info():
    """Información del usuario actual"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'role': current_user.role.name,
        'created_at': current_user.created_at.isoformat()
    })

# ================== ENDPOINTS DE USUARIOS ==================

@api_v1_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Obtener lista de usuarios"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role_filter = request.args.get('role')
    
    query = User.query
    if role_filter:
        query = query.join(Role).filter(Role.name == role_filter)
    
    users = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        } for user in users.items],
        'pagination': {
            'page': users.page,
            'pages': users.pages,
            'per_page': users.per_page,
            'total': users.total
        }
    })

@api_v1_bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Crear nuevo usuario"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar si el usuario ya existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Verificar que el rol existe
    role = Role.query.get(data['role_id'])
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role_id=data['role_id'],
            is_active=data.get('is_active', True)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'id': user.id,
            'message': 'User created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@api_v1_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@api_key_required
def get_user(user_id):
    """Obtener información de un usuario específico"""
    # Solo admin puede ver otros usuarios, o el usuario puede verse a sí mismo
    if current_user.role.name != 'admin' and current_user.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role.name,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat()
    }
    
    # Agregar información específica según el rol
    if user.role.name == 'student':
        user_data['enrolled_courses'] = [{
            'id': course.id,
            'name': course.name,
            'code': course.code
        } for course in user.enrolled_courses]
        
    elif user.role.name == 'teacher':
        user_data['teaching_courses'] = [{
            'id': course.id,
            'name': course.name,
            'code': course.code
        } for course in user.teaching_courses]
    
    return jsonify(user_data)

@api_v1_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Actualizar usuario"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Actualizar campos permitidos
        if 'username' in data:
            # Verificar que el username no esté en uso por otro usuario
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Username already exists'}), 409
            user.username = data['username']
        
        if 'email' in data:
            # Verificar que el email no esté en uso por otro usuario
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Email already exists'}), 409
            user.email = data['email']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'role_id' in data:
            role = Role.query.get(data['role_id'])
            if not role:
                return jsonify({'error': 'Role not found'}), 404
            user.role_id = data['role_id']
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@api_v1_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Eliminar usuario"""
    user = User.query.get_or_404(user_id)
    
    # No permitir eliminar el usuario actual
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500

# ================== ENDPOINTS DE ROLES ==================

@api_v1_bp.route('/roles', methods=['GET'])
@login_required
@admin_required
def get_roles():
    """Obtener lista de roles"""
    roles = Role.query.all()
    return jsonify({
        'roles': [{
            'id': role.id,
            'name': role.name,
            'description': role.description
        } for role in roles]
    })

# ================== ENDPOINTS DE CURSOS ==================

@api_v1_bp.route('/courses', methods=['GET'])
@login_required
@api_key_required
def get_courses():
    """Obtener lista de cursos"""
    if current_user.role.name == ADMIN_ROLE:
        courses = Course.query.all()
    elif current_user.role.name == TEACHER_ROLE:
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
    elif current_user.role.name == STUDENT_ROLE:
        courses = current_user.enrolled_courses
    else:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'courses': [{
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'teacher': {
                'id': course.teacher.id,
                'name': f"{course.teacher.first_name} {course.teacher.last_name}"
            } if course.teacher else None,
            'student_count': len(course.students),
            'subject_count': len(course.subjects)
        } for course in courses]
    })

@api_v1_bp.route('/courses', methods=['POST'])
@login_required
@admin_required
def create_course():
    """Crear nuevo curso"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['name', 'code', 'teacher_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar que el código del curso no exista
    if Course.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Course code already exists'}), 409
    
    # Verificar que el profesor existe y tiene rol de teacher
    teacher = User.query.join(Role).filter(
        User.id == data['teacher_id'],
        Role.name == 'teacher'
    ).first()
    if not teacher:
        return jsonify({'error': 'Teacher not found or invalid role'}), 404
    
    try:
        course = Course(
            name=data['name'],
            code=data['code'],
            description=data.get('description', ''),
            teacher_id=data['teacher_id']
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'id': course.id,
            'message': 'Course created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create course'}), 500

@api_v1_bp.route('/courses/<int:course_id>', methods=['GET'])
@login_required
@api_key_required
def get_course(course_id):
    """Obtener información detallada de un curso"""
    course = Course.query.get_or_404(course_id)
    
    # Verificar acceso
    has_access = (
        current_user.role.name == ADMIN_ROLE or
        (current_user.role.name == TEACHER_ROLE and course.teacher_id == current_user.id) or
        (current_user.role.name == STUDENT_ROLE and course in current_user.enrolled_courses)
    )
    
    if not has_access:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': course.id,
        'name': course.name,
        'code': course.code,
        'description': course.description,
        'teacher': {
            'id': course.teacher.id,
            'name': f"{course.teacher.first_name} {course.teacher.last_name}",
            'email': course.teacher.email
        } if course.teacher else None,
        'students': [{
            'id': student.id,
            'name': f"{student.first_name} {student.last_name}",
            'email': student.email
        } for student in course.students],
        'subjects': [{
            'id': subject.id,
            'name': subject.name,
            'description': subject.description
        } for subject in course.subjects],
        'created_at': course.created_at.isoformat()
    })

@api_v1_bp.route('/courses/<int:course_id>', methods=['PUT'])
@login_required
@admin_required
def update_course(course_id):
    """Actualizar curso"""
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'name' in data:
            course.name = data['name']
        if 'code' in data:
            # Verificar que el código no esté en uso por otro curso
            existing = Course.query.filter_by(code=data['code']).first()
            if existing and existing.id != course_id:
                return jsonify({'error': 'Course code already exists'}), 409
            course.code = data['code']
        if 'description' in data:
            course.description = data['description']
        if 'teacher_id' in data:
            teacher = User.query.join(Role).filter(
                User.id == data['teacher_id'],
                Role.name == 'teacher'
            ).first()
            if not teacher:
                return jsonify({'error': 'Teacher not found or invalid role'}), 404
            course.teacher_id = data['teacher_id']
        
        db.session.commit()
        return jsonify({'message': 'Course updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update course'}), 500

@api_v1_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_course(course_id):
    """Eliminar curso"""
    course = Course.query.get_or_404(course_id)
    
    try:
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete course'}), 500

@api_v1_bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
@admin_required
def enroll_student(course_id):
    """Inscribir estudiante en curso"""
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    
    if not data or 'student_id' not in data:
        return jsonify({'error': 'Student ID required'}), 400
    
    student = User.query.join(Role).filter(
        User.id == data['student_id'],
        Role.name == 'student'
    ).first()
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if student in course.students:
        return jsonify({'error': 'Student already enrolled'}), 409
    
    try:
        course.students.append(student)
        db.session.commit()
        return jsonify({'message': 'Student enrolled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to enroll student'}), 500

@api_v1_bp.route('/courses/<int:course_id>/unenroll', methods=['DELETE'])
@login_required
@admin_required
def unenroll_student(course_id):
    """Desinscribir estudiante del curso"""
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    
    if not data or 'student_id' not in data:
        return jsonify({'error': 'Student ID required'}), 400
    
    student = User.query.get(data['student_id'])
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if student not in course.students:
        return jsonify({'error': 'Student not enrolled'}), 404
    
    try:
        course.students.remove(student)
        db.session.commit()
        return jsonify({'message': 'Student unenrolled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to unenroll student'}), 500

# ================== ENDPOINTS DE MATERIAS ==================

@api_v1_bp.route('/subjects', methods=['GET'])
@login_required
@api_key_required
def get_subjects():
    """Obtener lista de materias"""
    course_id = request.args.get('course_id', type=int)
    
    query = Subject.query
    
    # Filtros de acceso según rol
    if current_user.role.name == STUDENT_ROLE:
        # Estudiantes solo ven materias de sus cursos
        enrolled_course_ids = [c.id for c in current_user.enrolled_courses]
        query = query.filter(Subject.course_id.in_(enrolled_course_ids))
    elif current_user.role.name == TEACHER_ROLE:
        # Profesores solo ven materias de sus cursos
        query = query.join(Course).filter(Course.teacher_id == current_user.id)
    # Admin puede ver todas
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    subjects = query.all()
    
    return jsonify({
        'subjects': [{
            'id': subject.id,
            'name': subject.name,
            'description': subject.description,
            'course': {
                'id': subject.course.id,
                'name': subject.course.name,
                'code': subject.course.code
            },
            'assignment_count': len(subject.assignments),
            'created_at': subject.created_at.isoformat()
        } for subject in subjects]
    })

@api_v1_bp.route('/subjects', methods=['POST'])
@login_required
@teacher_or_admin_required
def create_subject():
    """Crear nueva materia"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['name', 'course_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar acceso al curso
    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    if current_user.role.name == TEACHER_ROLE and course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied to this course'}), 403
    
    try:
        subject = Subject(
            name=data['name'],
            description=data.get('description', ''),
            course_id=data['course_id']
        )
        
        db.session.add(subject)
        db.session.commit()
        
        return jsonify({
            'id': subject.id,
            'message': 'Subject created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create subject'}), 500

@api_v1_bp.route('/subjects/<int:subject_id>', methods=['GET'])
@login_required
@api_key_required
def get_subject(subject_id):
    """Obtener información detallada de una materia"""
    subject = Subject.query.get_or_404(subject_id)
    
    # Verificar acceso
    has_access = (
        current_user.role.name == ADMIN_ROLE or
        (current_user.role.name == TEACHER_ROLE and course.teacher_id == current_user.id) or
        (current_user.role.name == STUDENT_ROLE and course in current_user.enrolled_courses)
    )
    
    if not has_access:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': subject.id,
        'name': subject.name,
        'description': subject.description,
        'course': {
            'id': subject.course.id,
            'name': subject.course.name,
            'code': subject.course.code
        },
        'assignments': [{
            'id': assignment.id,
            'title': assignment.title,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None
        } for assignment in subject.assignments],
        'created_at': subject.created_at.isoformat()
    })

@api_v1_bp.route('/subjects/<int:subject_id>', methods=['PUT'])
@login_required
@teacher_or_admin_required
def update_subject(subject_id):
    """Actualizar materia"""
    subject = Subject.query.get_or_404(subject_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE and subject.course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'name' in data:
            subject.name = data['name']
        if 'description' in data:
            subject.description = data['description']
        
        db.session.commit()
        return jsonify({'message': 'Subject updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update subject'}), 500

@api_v1_bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
@login_required
@teacher_or_admin_required
def delete_subject(subject_id):
    """Eliminar materia"""
    subject = Subject.query.get_or_404(subject_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE and subject.course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(subject)
        db.session.commit()
        return jsonify({'message': 'Subject deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete subject'}), 500

# ================== ENDPOINTS DE CALIFICACIONES ==================

@api_v1_bp.route('/grades', methods=['GET'])
@login_required
@api_key_required
def get_grades():
    """Obtener calificaciones"""
    student_id = request.args.get('student_id', type=int)
    course_id = request.args.get('course_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    query = Grade.query
    
    # Filtros de acceso según rol
    if current_user.role.name == STUDENT_ROLE:
        query = query.filter_by(student_id=current_user.id)
    elif current_user.role.name == TEACHER_ROLE:
        query = query.join(Subject).join(Course).filter(Course.teacher_id == current_user.id)
    # Admin puede ver todas
    
    # Aplicar filtros adicionales
    if student_id:
        query = query.filter_by(student_id=student_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if course_id:
        query = query.join(Subject).filter(Subject.course_id == course_id)
    
    grades = query.all()
    
    return jsonify({
        'grades': [{
            'id': grade.id,
            'value': grade.value,
            'student': {
                'id': grade.student.id,
                'name': f"{grade.student.first_name} {grade.student.last_name}"
            },
            'subject': {
                'id': grade.subject.id,
                'name': grade.subject.name,
                'course': {
                    'id': grade.subject.course.id,
                    'name': grade.subject.course.name
                }
            },
            'teacher': {
                'id': grade.teacher.id,
                'name': f"{grade.teacher.first_name} {grade.teacher.last_name}"
            } if grade.teacher else None,
            'created_at': grade.created_at.isoformat(),
            'updated_at': grade.updated_at.isoformat() if grade.updated_at else None
        } for grade in grades]
    })

@api_v1_bp.route('/grades', methods=['POST'])
@login_required
@teacher_or_admin_required
def create_grade():
    """Crear nueva calificación"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['student_id', 'subject_id', 'value']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar que la materia existe y el profesor tiene acceso
    subject = Subject.query.get(data['subject_id'])
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404
    
    if current_user.role.name == TEACHER_ROLE and subject.course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied to this subject'}), 403
    
    # Verificar que el estudiante existe y está inscrito en el curso
    student = User.query.join(Role).filter(
        User.id == data['student_id'],
        Role.name == 'student'
    ).first()
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if subject.course not in student.enrolled_courses:
        return jsonify({'error': 'Student not enrolled in this course'}), 400
    
    try:
        grade = Grade(
            student_id=data['student_id'],
            subject_id=data['subject_id'],
            value=data['value'],
            teacher_id=current_user.id
        )
        
        db.session.add(grade)
        db.session.commit()
        
        return jsonify({
            'id': grade.id,
            'message': 'Grade created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create grade'}), 500

@api_v1_bp.route('/grades/<int:grade_id>', methods=['PUT'])
@login_required
@teacher_or_admin_required
def update_grade(grade_id):
    """Actualizar calificación"""
    grade = Grade.query.get_or_404(grade_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE:
        if grade.subject.course.teacher_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'value' in data:
            grade.value = data['value']
        
        grade.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Grade updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update grade'}), 500

@api_v1_bp.route('/grades/<int:grade_id>', methods=['DELETE'])
@login_required
@teacher_or_admin_required
def delete_grade(grade_id):
    """Eliminar calificación"""
    grade = Grade.query.get_or_404(grade_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE:
        if grade.subject.course.teacher_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(grade)
        db.session.commit()
        return jsonify({'message': 'Grade deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete grade'}), 500

# ================== ENDPOINTS DE ASISTENCIA ==================

@api_v1_bp.route('/attendance', methods=['GET'])
@login_required
@api_key_required
def get_attendance():
    """Obtener registros de asistencia"""
    student_id = request.args.get('student_id', type=int)
    course_id = request.args.get('course_id', type=int)
    date_from = request.args.get('date_from', type=lambda x: datetime.strptime(x, '%Y-%m-%d').date())
    date_to = request.args.get('date_to', type=lambda x: datetime.strptime(x, '%Y-%m-%d').date())
    
    query = Attendance.query
    
    # Filtros de acceso según rol
    if current_user.role.name == STUDENT_ROLE:
        query = query.filter_by(student_id=current_user.id)
    elif current_user.role.name == TEACHER_ROLE:
        query = query.join(Course).filter(Course.teacher_id == current_user.id)
    # Admin puede ver todas
    
    # Aplicar filtros adicionales
    if student_id:
        query = query.filter_by(student_id=student_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    
    attendance_records = query.order_by(Attendance.date.desc()).all()
    
    return jsonify({
        'attendance': [{
            'id': record.id,
            'status': record.status,
            'date': record.date.isoformat(),
            'student': {
                'id': record.student.id,
                'name': f"{record.student.first_name} {record.student.last_name}"
            },
            'course': {
                'id': record.course.id,
                'name': record.course.name,
                'code': record.course.code
            },
            'recorded_by': {
                'id': record.recorded_by.id,
                'name': f"{record.recorded_by.first_name} {record.recorded_by.last_name}"
            } if record.recorded_by else None,
            'notes': record.notes,
            'created_at': record.created_at.isoformat()
        } for record in attendance_records]
    })

@api_v1_bp.route('/attendance', methods=['POST'])
@login_required
@teacher_or_admin_required
def create_attendance():
    """Crear nuevo registro de asistencia"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['student_id', 'course_id', 'status', 'date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar que el curso existe y el profesor tiene acceso
    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    if current_user.role.name == TEACHER_ROLE and course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied to this course'}), 403
    
    # Verificar que el estudiante existe y está inscrito en el curso
    student = User.query.join(Role).filter(
        User.id == data['student_id'],
        Role.name == 'student'
    ).first()
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if course not in student.enrolled_courses:
        return jsonify({'error': 'Student not enrolled in this course'}), 400
    
    try:
        # Convertir la fecha del string a objeto date
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Verificar si ya existe un registro para este estudiante en esta fecha
        existing = Attendance.query.filter_by(
            student_id=data['student_id'],
            course_id=data['course_id'],
            date=attendance_date
        ).first()
        
        if existing:
            return jsonify({'error': 'Attendance record already exists for this date'}), 409
        
        attendance = Attendance(
            student_id=data['student_id'],
            course_id=data['course_id'],
            status=data['status'],
            date=attendance_date,
            recorded_by_id=current_user.id,
            notes=data.get('notes', '')
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'id': attendance.id,
            'message': 'Attendance record created successfully'
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create attendance record'}), 500

@api_v1_bp.route('/attendance/<int:attendance_id>', methods=['PUT'])
@login_required
@teacher_or_admin_required
def update_attendance(attendance_id):
    """Actualizar registro de asistencia"""
    attendance = Attendance.query.get_or_404(attendance_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE:
        if attendance.course.teacher_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'status' in data:
            attendance.status = data['status']
        if 'notes' in data:
            attendance.notes = data['notes']
        if 'date' in data:
            attendance.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        attendance.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Attendance record updated successfully'})
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update attendance record'}), 500

@api_v1_bp.route('/attendance/<int:attendance_id>', methods=['DELETE'])
@login_required
@teacher_or_admin_required
def delete_attendance(attendance_id):
    """Eliminar registro de asistencia"""
    attendance = Attendance.query.get_or_404(attendance_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE:
        if attendance.course.teacher_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(attendance)
        db.session.commit()
        return jsonify({'message': 'Attendance record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete attendance record'}), 500

# ================== ENDPOINTS DE TAREAS ==================

@api_v1_bp.route('/assignments', methods=['GET'])
@login_required
@api_key_required
def get_assignments():
    """Obtener lista de tareas"""
    subject_id = request.args.get('subject_id', type=int)
    course_id = request.args.get('course_id', type=int)
    student_id = request.args.get('student_id', type=int)
    
    query = Assignment.query
    
    # Filtros de acceso según rol
    if current_user.role.name == STUDENT_ROLE:
        # Estudiantes solo ven tareas de sus cursos
        enrolled_course_ids = [c.id for c in current_user.enrolled_courses]
        query = query.join(Subject).filter(Subject.course_id.in_(enrolled_course_ids))
    elif current_user.role.name == TEACHER_ROLE:
        # Profesores solo ven tareas de sus cursos
        query = query.join(Subject).join(Course).filter(Course.teacher_id == current_user.id)
    # Admin puede ver todas
    
    # Aplicar filtros adicionales
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if course_id:
        query = query.join(Subject).filter(Subject.course_id == course_id)
    
    assignments = query.order_by(Assignment.due_date.asc()).all()
    
    # Filtrar por estudiante si se especifica
    if student_id:
        assignments = [a for a in assignments if any(
            s.student_id == student_id for s in a.submissions
        )]
    
    return jsonify({
        'assignments': [{
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'max_score': assignment.max_score,
            'subject': {
                'id': assignment.subject.id,
                'name': assignment.subject.name
            },
            'course': {
                'id': assignment.subject.course.id,
                'name': assignment.subject.course.name
            },
            'submission_count': len(assignment.submissions),
            'created_at': assignment.created_at.isoformat()
        } for assignment in assignments]
    })

@api_v1_bp.route('/assignments', methods=['POST'])
@login_required
@teacher_or_admin_required
def create_assignment():
    """Crear nueva tarea"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['title', 'subject_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar que la materia existe y el profesor tiene acceso
    subject = Subject.query.get(data['subject_id'])
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404
    
    if current_user.role.name == TEACHER_ROLE and subject.course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied to this subject'}), 403
    
    try:
        assignment = Assignment(
            title=data['title'],
            description=data.get('description', ''),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if 'due_date' in data else None,
            max_score=data.get('max_score', 100),
            subject_id=data['subject_id']
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'id': assignment.id,
            'message': 'Assignment created successfully'
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create assignment'}), 500

@api_v1_bp.route('/assignments/<int:assignment_id>', methods=['GET'])
@login_required
@api_key_required
def get_assignment(assignment_id):
    """Obtener información detallada de una tarea"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verificar acceso
    has_access = (
        current_user.role.name == ADMIN_ROLE or
        (current_user.role.name == TEACHER_ROLE and assignment.subject.course.teacher_id == current_user.id) or
        (current_user.role.name == STUDENT_ROLE and assignment.subject.course in current_user.enrolled_courses)
    )
    
    if not has_access:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': assignment.id,
        'title': assignment.title,
        'description': assignment.description,
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'max_score': assignment.max_score,
        'subject': {
            'id': assignment.subject.id,
            'name': assignment.subject.name,
            'course': {
                'id': assignment.subject.course.id,
                'name': assignment.subject.course.name,
                'code': assignment.subject.course.code
            }
        },
        'submissions': [{
            'id': submission.id,
            'student': {
                'id': submission.student.id,
                'name': f"{submission.student.first_name} {submission.student.last_name}"
            },
            'score': submission.score,
            'submitted_at': submission.submitted_at.isoformat(),
            'status': submission.status
        } for submission in assignment.submissions],
        'created_at': assignment.created_at.isoformat()
    })

@api_v1_bp.route('/assignments/<int:assignment_id>', methods=['PUT'])
@login_required
@teacher_or_admin_required
def update_assignment(assignment_id):
    """Actualizar tarea"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE and assignment.subject.course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'title' in data:
            assignment.title = data['title']
        if 'description' in data:
            assignment.description = data['description']
        if 'due_date' in data:
            assignment.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        if 'max_score' in data:
            assignment.max_score = data['max_score']
        
        db.session.commit()
        return jsonify({'message': 'Assignment updated successfully'})
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update assignment'}), 500

@api_v1_bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
@teacher_or_admin_required
def delete_assignment(assignment_id):
    """Eliminar tarea"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verificar acceso
    if current_user.role.name == TEACHER_ROLE and assignment.subject.course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(assignment)
        db.session.commit()
        return jsonify({'message': 'Assignment deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete assignment'}), 500

# ================== ENDPOINTS DE ENTREGAS ==================

@api_v1_bp.route('/submissions', methods=['GET'])
@login_required
@api_key_required
def get_submissions():
    """Obtener entregas de tareas"""
    assignment_id = request.args.get('assignment_id', type=int)
    student_id = request.args.get('student_id', type=int)
    
    query = Submission.query
    
    # Filtros de acceso según rol
    if current_user.role.name == STUDENT_ROLE:
        query = query.filter_by(student_id=current_user.id)
    elif current_user.role.name == TEACHER_ROLE:
        query = query.join(Assignment).join(Subject).join(Course).filter(
            Course.teacher_id == current_user.id
        )
    # Admin puede ver todas
    
    # Aplicar filtros adicionales
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    
    return jsonify({
        'submissions': [{
            'id': submission.id,
            'content': submission.content,
            'score': submission.score,
            'feedback': submission.feedback,
            'status': submission.status,
            'submitted_at': submission.submitted_at.isoformat(),
            'student': {
                'id': submission.student.id,
                'name': f"{submission.student.first_name} {submission.student.last_name}"
            },
            'assignment': {
                'id': submission.assignment.id,
                'title': submission.assignment.title,
                'max_score': submission.assignment.max_score,
                'subject': {
                    'id': submission.assignment.subject.id,
                    'name': submission.assignment.subject.name
                }
            },
            'graded_by': {
                'id': submission.graded_by.id,
                'name': f"{submission.graded_by.first_name} {submission.graded_by.last_name}"
            } if submission.graded_by else None,
            'graded_at': submission.graded_at.isoformat() if submission.graded_at else None
        } for submission in submissions]
    })

@api_v1_bp.route('/submissions', methods=['POST'])
@login_required
def create_submission():
    """Crear nueva entrega de tarea"""
    if current_user.role.name != 'student':
        return jsonify({'error': 'Only students can submit assignments'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['assignment_id', 'content']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar que la tarea existe
    assignment = Assignment.query.get(data['assignment_id'])
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    # Verificar que el estudiante está inscrito en el curso
    if assignment.subject.course not in current_user.enrolled_courses:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Verificar si ya existe una entrega para esta tarea
    existing = Submission.query.filter_by(
        assignment_id=data['assignment_id'],
        student_id=current_user.id
    ).first()
    
    if existing:
        return jsonify({'error': 'You have already submitted this assignment'}), 409
    
    try:
        submission = Submission(
            assignment_id=data['assignment_id'],
            student_id=current_user.id,
            content=data['content'],
            status='submitted'
        )
        
        db.session.add(submission)
        db.session.commit()
        
        return jsonify({
            'id': submission.id,
            'message': 'Assignment submitted successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit assignment'}), 500

@api_v1_bp.route('/submissions/<int:submission_id>', methods=['PUT'])
@login_required
def update_submission(submission_id):
    """Actualizar entrega de tarea"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Verificar acceso
    if current_user.role.name == STUDENT_ROLE and submission.student_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if current_user.role.name == STUDENT_ROLE:
            # Estudiantes solo pueden actualizar el contenido antes de ser calificado
            if submission.status == 'graded':
                return jsonify({'error': 'Cannot update graded submission'}), 400
            
            if 'content' in data:
                submission.content = data['content']
            
            submission.status = 'submitted'
            submission.submitted_at = datetime.utcnow()
        
        elif current_user.role.name in [TEACHER_ROLE, ADMIN_ROLE]:
            # Profesores y admin pueden calificar
            if 'score' in data:
                submission.score = data['score']
            if 'feedback' in data:
                submission.feedback = data['feedback']
            if 'status' in data:
                submission.status = data['status']
            
            submission.graded_by_id = current_user.id
            submission.graded_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': 'Submission updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update submission'}), 500

@api_v1_bp.route('/submissions/<int:submission_id>', methods=['DELETE'])
@login_required
def delete_submission(submission_id):
    """Eliminar entrega de tarea"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Verificar acceso
    if current_user.role.name == STUDENT_ROLE:
        if submission.student_id != current_user.id or submission.status == 'graded':
            return jsonify({'error': 'Access denied'}), 403
    elif current_user.role.name == TEACHER_ROLE:
        if submission.assignment.subject.course.teacher_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(submission)
        db.session.commit()
        return jsonify({'message': 'Submission deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete submission'}), 500