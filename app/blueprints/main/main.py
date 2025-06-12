# app/routes/main.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, db, Role, Course
import random
import string
from datetime import datetime

# Crear el blueprint principal
main_bp = Blueprint('main', __name__)

# Definir las funciones

@main_bp.route('/')
def index():
    """Página principal"""
    if current_user.is_authenticated:
        if current_user.role.name == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role.name == 'teacher':
            return redirect(url_for('main.teacher_dashboard'))
        elif current_user.role.name == 'student':
            return redirect(url_for('main.student_dashboard'))
    
    # Si no está autenticado, mostrar la página principal
    return render_template('main/index.html')

@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Dashboard del administrador"""
    if current_user.role.name != 'admin':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect('/')
    
    # Obtener estadísticas
    total_usuarios = User.query.count()
    total_estudiantes = User.query.join(Role).filter(Role.name == 'student').count()
    total_profesores = User.query.join(Role).filter(Role.name == 'teacher').count()
    total_admins = User.query.join(Role).filter(Role.name == 'admin').count()
    
    # Obtener usuarios recientes
    usuarios_recientes = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('main/admin/dashboard.html', 
                         stats={
                             'total_usuarios': total_usuarios,
                             'total_estudiantes': total_estudiantes,
                             'total_profesores': total_profesores,
                             'total_admins': total_admins
                         },
                         usuarios_recientes=usuarios_recientes)

@main_bp.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    """Dashboard del profesor"""
    if current_user.role.name != 'teacher':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect('/')
    
    # Obtener cursos del profesor
    cursos = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # Obtener estadísticas
    stats = {
        'total_cursos': len(cursos),
        'total_estudiantes': sum([c.get_student_count() for c in cursos]),
        'calificaciones_pendientes': 0,  # Implementar lógica para contar calificaciones pendientes
        'asistencia_pendiente': 0,  # Implementar lógica para contar asistencia pendiente
        'cursos_activos': len([c for c in cursos if c.is_active]),
        'cursos_inactivos': len([c for c in cursos if not c.is_active]),
        'creditos_totales': sum([c.credits for c in cursos])
    }
    
    # Obtener entregas pendientes (simuladas)
    entregas_pendientes = [
        {
            'curso': 'Matemáticas Avanzadas',
            'asignatura': 'Álgebra Lineal',
            'estudiantes': 15,
            'fecha_limite': '2025-06-15'
        },
        {
            'curso': 'Física General',
            'asignatura': 'Termodinámica',
            'estudiantes': 20,
            'fecha_limite': '2025-06-20'
        }
    ]
    
    return render_template('main/teacher/dashboard.html', 
                         stats=stats,
                         cursos=cursos,
                         entregas_pendientes=entregas_pendientes)

@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    """Dashboard del estudiante"""
    if current_user.role.name != 'student':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect('/')
    
    # Obtener cursos inscritos del estudiante
    cursos_inscritos = current_user.enrolled_courses
    
    # Obtener estadísticas
    stats = {
        'total_cursos': len(cursos_inscritos),
        'total_creditos': sum([c.credits for c in cursos_inscritos]),
        'promedio_general': 0,  # Implementar cálculo del promedio
        'porcentaje_asistencia': 0  # Implementar cálculo del porcentaje de asistencia
    }
    
    return render_template('main/student/dashboard.html', 
                         stats=stats,
                         cursos_inscritos=cursos_inscritos)

@main_bp.route('/profile')
@login_required
def profile():
    """Perfil del usuario"""
    return render_template('main/profile.html')

@main_bp.route('/about')
def about():
    """Página acerca de"""
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    """Página de contacto"""
    return render_template('main/contact.html')

# Exportar el blueprint
__all__ = ['main_bp']
