from functools import wraps
from flask import abort, jsonify, request, flash, redirect, url_for
from flask_login import current_user
import jwt

# Decorador para roles generales (web)
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Debes iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:  # Cambiado de 'rol' a 'role'
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('No tienes permisos para acceder a esta página.', 'error')
                return redirect('/')

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Decoradores específicos para vistas web
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_admin():
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Necesitas permisos de administrador para acceder a esta página.', 'error')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_teacher():  # Cambiado de 'is_profesor()' a 'is_teacher()'
            if request.is_json:
                return jsonify({'error': 'Teacher access required'}), 403
            flash('Necesitas ser profesor para acceder a esta página.', 'error')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_student():  # Cambiado de 'is_estudiante()' a 'is_student()'
            if request.is_json:
                return jsonify({'error': 'Student access required'}), 403
            flash('Necesitas ser estudiante para acceder a esta página.', 'error')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function

# Decorador JWT genérico
def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]

            from flask import current_app
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']

            # Importación tardía para evitar ciclos
            from app.models.models import User
            usuario = User.query.get(current_user_id)
            if not usuario or not usuario.is_active:  # Cambiado de 'activo' a 'is_active'
                return jsonify({'error': 'User not found or inactive'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated_function

# Decorador JWT + verificación de rol
def api_role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Token missing'}), 401

            try:
                if token.startswith('Bearer '):
                    token = token[7:]

                from flask import current_app
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                current_user_id = data['user_id']

                # Importación tardía para evitar ciclos
                from app.models import User
                usuario = User.query.get(current_user_id)
                if not usuario or not usuario.is_active:  # Cambiado de 'activo' a 'is_active'
                    return jsonify({'error': 'User not found or inactive'}), 401

                if usuario.role not in roles:  # Cambiado de 'rol' a 'role'
                    return jsonify({'error': 'Insufficient permissions'}), 403

            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Token is invalid'}), 401

            return f(current_user_id, *args, **kwargs)
        return decorated_function
    return decorator

# Decoradores API específicos
def api_admin_required(f):
    return api_role_required('admin')(f)

def api_teacher_required(f):
    return api_role_required('teacher')(f)  # Cambiado de 'profesor' a 'teacher'

def api_student_required(f):
    return api_role_required('student')(f)  # Cambiado de 'estudiante' a 'student'

# ✅ Decorador genérico para autenticación en APIs (sin validación de rol)
def api_auth_required(f):
    return jwt_required(f)