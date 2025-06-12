# app/blueprints/admin/routes.py
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User
from app.models.course import Course

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorador para verificar que el usuario sea admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('No tienes permisos para acceder a esta página.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del administrador"""
    try:
        # Obtener estadísticas básicas
        total_usuarios = User.query.count()
        total_estudiantes = User.query.filter_by(role='student').count()
        total_profesores = User.query.filter_by(role='teacher').count()
        total_admins = User.query.filter_by(role='admin').count()
        total_cursos = Course.query.count()
        cursos_activos = Course.query.filter_by(is_active=True).count()
        
        # Obtener usuarios recientes (últimos 5)
        usuarios_recientes = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # Obtener cursos recientes
        cursos_recientes = Course.query.order_by(Course.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_usuarios=total_usuarios,
                             total_estudiantes=total_estudiantes,
                             total_profesores=total_profesores,
                             total_admins=total_admins,
                             total_cursos=total_cursos,
                             cursos_activos=cursos_activos,
                             usuarios_recientes=usuarios_recientes,
                             cursos_recientes=cursos_recientes)
                             
    except Exception as e:
        print(f"Error en admin dashboard: {e}")
        flash('Error al cargar el dashboard', 'error')
        return render_template('admin/dashboard.html',
                             total_usuarios=0,
                             total_estudiantes=0,
                             total_profesores=0,
                             total_admins=0,
                             total_cursos=0,
                             cursos_activos=0,
                             usuarios_recientes=[],
                             cursos_recientes=[])

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    """Lista todos los usuarios"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users = User.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return render_template('admin/users.html', users=users)
        
    except Exception as e:
        print(f"Error listando usuarios: {e}")
        flash('Error al cargar la lista de usuarios', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/users')
@login_required
@admin_required
def get_users_api():
    """API para obtener usuarios (JSON)"""
    try:
        users = User.query.all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'nombre': user.nombre,
                'apellido': user.apellido,
                'telefono': user.telefono,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'total': len(users_data)
        })
        
    except Exception as e:
        print(f"Error en API usuarios: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener usuarios'
        }), 500

@admin_bp.route('/courses')
@login_required
@admin_required
def list_courses():
    """Lista todos los cursos"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        courses = Course.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return render_template('admin/courses.html', courses=courses)
        
    except Exception as e:
        print(f"Error listando cursos: {e}")
        flash('Error al cargar la lista de cursos', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/courses')
@login_required
@admin_required
def get_courses_api():
    """API para obtener cursos (JSON)"""
    try:
        courses = Course.query.all()
        courses_data = []
        
        for course in courses:
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'description': course.description,
                'teacher_id': course.teacher_id,
                'teacher_name': course.teacher.get_full_name() if course.teacher else None,
                'credits': course.credits,
                'semester': course.semester,
                'is_active': course.is_active,
                'created_at': course.created_at.isoformat() if course.created_at else None
            })
        
        return jsonify({
            'success': True,
            'courses': courses_data,
            'total': len(courses_data)
        })
        
    except Exception as e:
        print(f"Error en API cursos: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener cursos'
        }), 500