# app/routes/main.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, db
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
    if not current_user.role.name == 'admin':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect('/')
    
    # Obtener estadísticas
    total_usuarios = User.query.count()
    total_estudiantes = User.query.filter_by(role='student').count()
    total_profesores = User.query.filter_by(role='teacher').count()
    total_admins = User.query.filter_by(role='admin').count()
    
    # Obtener usuarios recientes
    usuarios_recientes = User.query.order_by(User.fecha_registro.desc()).limit(5).all()
    
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
    if not current_user.role.name == 'teacher':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect('/')
    
    # Obtener cursos del profesor
    cursos = Course.query.filter_by(profesor_id=current_user.id).all()
    
    # Obtener estadísticas
    stats = {
        'total_cursos': len(cursos),
        'total_estudiantes': sum([c.estudiantes.count() for c in cursos]),
        'calificaciones_pendientes': 0,  # Implementar lógica para contar calificaciones pendientes
        'asistencia_pendiente': 0  # Implementar lógica para contar asistencia pendiente
    }
    
    return render_template('main/teacher/dashboard.html', 
                         stats=stats,
                         cursos=cursos)

@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    """Dashboard del estudiante"""
    if not current_user.role.name == 'student':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect('/')
    
    # Obtener inscripciones del estudiante
    inscripciones = Inscription.query.filter_by(student_id=current_user.id).all()
    
    # Obtener estadísticas
    stats = {
        'total_cursos': len(inscripciones),
        'total_creditos': sum([i.curso.creditos for i in inscripciones]),
        'promedio_general': 0,  # Implementar cálculo del promedio
        'porcentaje_asistencia': 0  # Implementar cálculo del porcentaje de asistencia
    }
    
    return render_template('main/student/dashboard.html', 
                         stats=stats,
                         inscripciones=inscripciones)

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
