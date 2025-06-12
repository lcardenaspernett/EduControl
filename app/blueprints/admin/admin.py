# app/blueprints/admin.py

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

# ✅ Importaciones correctas desde app.models
from app.models import db, User, Course, Calificacion, Asistencia

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorador para verificar que el usuario sea admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('main.login'))
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
        # Estadísticas generales
        total_usuarios = User.query.count()
        total_estudiantes = User.query.filter_by(role='student').count()
        total_profesores = User.query.filter_by(role='teacher').count()
        total_admins = User.query.filter_by(role='admin').count()
        total_cursos = Course.query.count()
        cursos_activos = Course.query.filter_by(is_active=True).count()
        
        # Usuarios recientes (últimos 5)
        usuarios_recientes = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # Cursos recientes (últimos 5)
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
        print(f"Error en dashboard: {e}")
        flash('Error al cargar el dashboard.', 'error')
        return redirect(url_for('main.index'))

@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    """Lista de todos los usuarios"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        users = User.query.order_by(User.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return render_template('admin/usuarios.html', users=users)
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        flash('Error al cargar usuarios.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/users')
@login_required
@admin_required
def get_users():
    """API para obtener lista de usuarios"""
    try:
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'nombre': user.nombre or '',
            'apellido': user.apellido or '',
            'telefono': user.telefono or '',
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users])
    except Exception as e:
        print(f"Error obteniendo usuarios API: {e}")
        return jsonify({'error': 'Error obteniendo usuarios'}), 500

@admin_bp.route('/cursos')
@login_required
@admin_required
def cursos():
    """Lista de todos los cursos"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        courses = Course.query.order_by(Course.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return render_template('admin/cursos.html', courses=courses)
    except Exception as e:
        print(f"Error obteniendo cursos: {e}")
        flash('Error al cargar cursos.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/estadisticas')
@login_required
@admin_required
def estadisticas():
    """Página de estadísticas detalladas"""
    try:
        # Estadísticas de usuarios
        stats_usuarios = {
            'total': User.query.count(),
            'estudiantes': User.query.filter_by(role='student').count(),
            'profesores': User.query.filter_by(role='teacher').count(),
            'admins': User.query.filter_by(role='admin').count(),
            'activos': User.query.filter_by(is_active=True).count()
        }
        
        # Estadísticas de cursos
        stats_cursos = {
            'total': Course.query.count(),
            'activos': Course.query.filter_by(is_active=True).count(),
            'inactivos': Course.query.filter_by(is_active=False).count()
        }
        
        return render_template('admin/estadisticas.html',
                             stats_usuarios=stats_usuarios,
                             stats_cursos=stats_cursos)
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        flash('Error al cargar estadísticas.', 'error')
        return redirect(url_for('admin.dashboard'))
