# app/blueprints/admin.py

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, desc, asc, or_
from datetime import datetime, timedelta

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
        
        # Calcular crecimiento mensual
        fecha_mes_anterior = datetime.now() - timedelta(days=30)
        usuarios_mes_anterior = User.query.filter(User.created_at >= fecha_mes_anterior).count()
        
        if total_usuarios > 0:
            crecimiento_usuarios = round((usuarios_mes_anterior / total_usuarios) * 100, 1)
        else:
            crecimiento_usuarios = 0
        
        # Crear diccionario de estadísticas para el template
        stats = {
            'total_usuarios': total_usuarios,
            'total_estudiantes': total_estudiantes,
            'total_profesores': total_profesores,
            'total_admins': total_admins,
            'crecimiento_usuarios': crecimiento_usuarios
        }
        
        # Usuarios recientes (últimos 10)
        usuarios_recientes = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        # Cursos recientes (últimos 5)
        cursos_recientes = Course.query.order_by(Course.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
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
    """Lista de todos los usuarios (página simple)"""
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

# ============ NUEVA GESTIÓN AVANZADA DE USUARIOS ============

@admin_bp.route('/users/manage')
@login_required
@admin_required
def manage_users():
    """Página avanzada de gestión de usuarios con búsqueda, filtros y paginación"""
    
    try:
        # Parámetros de búsqueda y filtros
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '')
        status_filter = request.args.get('status', '')
        sort_by = request.args.get('sort', 'created_at')
        sort_order = request.args.get('order', 'desc')
        
        # Validar parámetros
        per_page = min(per_page, 100)  # Máximo 100 por página
        valid_sorts = ['username', 'email', 'nombre', 'apellido', 'created_at', 'role']
        if sort_by not in valid_sorts:
            sort_by = 'created_at'
        
        # Construir query base
        query = User.query
        
        # Aplicar búsqueda
        if search:
            search_filter = or_(
                User.username.ilike(f'%{search}%'),
                User.nombre.ilike(f'%{search}%'),
                User.apellido.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.role.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Aplicar filtro de rol
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        # Aplicar filtro de estado
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Aplicar ordenamiento
        sort_column = getattr(User, sort_by)
        
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Ejecutar paginación
        users_pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Obtener estadísticas
        total_users = User.query.count()
        active_users = User.query.filter(User.is_active == True).count()
        
        # Roles disponibles para el filtro
        available_roles = ['admin', 'teacher', 'student']
        
        # Estadísticas por rol
        role_stats = {}
        for role in available_roles:
            count = User.query.filter(User.role == role).count()
            role_stats[role] = count
        
        return render_template('admin/manage_users.html',
                             users=users_pagination,
                             search=search,
                             role_filter=role_filter,
                             status_filter=status_filter,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             per_page=per_page,
                             total_users=total_users,
                             active_users=active_users,
                             available_roles=available_roles,
                             role_stats=role_stats)
                             
    except Exception as e:
        print(f"Error en manage_users: {str(e)}")
        flash('Error al cargar la lista de usuarios', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/users/search')
@login_required
@admin_required
def search_users_api():
    """API para búsqueda en tiempo real de usuarios"""
    
    try:
        query_text = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query_text:
            return jsonify({'success': True, 'users': []})
        
        # Búsqueda en múltiples campos
        search_filter = or_(
            User.username.ilike(f'%{query_text}%'),
            User.nombre.ilike(f'%{query_text}%'),
            User.apellido.ilike(f'%{query_text}%'),
            User.email.ilike(f'%{query_text}%'),
            User.role.ilike(f'%{query_text}%')
        )
        
        users = User.query.filter(search_filter).limit(limit).all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username or '',
                'full_name': f"{user.nombre or ''} {user.apellido or ''}".strip(),
                'email': user.email or '',
                'role': user.role or 'unknown',
                'role_display': user.role.title() if user.role else 'Usuario',
                'created_at': user.created_at.strftime('%d/%m/%Y') if user.created_at else 'N/A',
                'is_active': user.is_active,
                'telefono': user.telefono or 'N/A'
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'count': len(users_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/users/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_user_action():
    """API para acciones en lote sobre usuarios"""
    
    try:
        data = request.get_json()
        action = data.get('action')
        user_ids = data.get('user_ids', [])
        
        if not action or not user_ids:
            return jsonify({
                'success': False,
                'message': 'Acción o IDs de usuarios no válidos'
            }), 400
        
        # Validar que no se incluya al usuario actual
        if current_user.id in user_ids:
            return jsonify({
                'success': False,
                'message': 'No puedes realizar acciones sobre tu propia cuenta'
            }), 400
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            return jsonify({
                'success': False,
                'message': 'No se encontraron usuarios válidos'
            }), 404
        
        results = []
        
        if action == 'activate':
            for user in users:
                user.is_active = True
                results.append(f"{user.username} activado")
                
        elif action == 'deactivate':
            for user in users:
                user.is_active = False
                results.append(f"{user.username} desactivado")
                
        elif action == 'delete':
            for user in users:
                db.session.delete(user)
                results.append(f"{user.username} eliminado")
                
        elif action == 'change_role':
            new_role = data.get('new_role')
            if not new_role or new_role not in ['admin', 'teacher', 'student']:
                return jsonify({
                    'success': False,
                    'message': 'Rol no válido'
                }), 400
                
            for user in users:
                user.role = new_role
                results.append(f"{user.username} → {new_role}")
        
        else:
            return jsonify({
                'success': False,
                'message': 'Acción no válida'
            }), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Acción completada sobre {len(users)} usuarios',
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al ejecutar acción: {str(e)}'
        }), 500

@admin_bp.route('/api/users/stats')
@login_required
@admin_required
def get_users_stats():
    """API para obtener estadísticas rápidas de usuarios"""
    
    try:
        # Estadísticas básicas
        total = User.query.count()
        active = User.query.filter(User.is_active == True).count()
        
        # Registros recientes
        today = datetime.now().date()
        this_week = today - timedelta(days=7)
        this_month = today - timedelta(days=30)
        
        registered_today = User.query.filter(func.date(User.created_at) == today).count()
        registered_week = User.query.filter(User.created_at >= this_week).count()
        registered_month = User.query.filter(User.created_at >= this_month).count()
        
        # Por roles
        roles_data = []
        roles = ['admin', 'teacher', 'student']
        for role in roles:
            count = User.query.filter(User.role == role).count()
            roles_data.append({
                'name': role,
                'display_name': role.title(),
                'count': count,
                'percentage': round((count / total * 100) if total > 0 else 0, 1)
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'active': active,
                'inactive': total - active,
                'registered_today': registered_today,
                'registered_week': registered_week,
                'registered_month': registered_month,
                'roles': roles_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    """Ver detalles de un usuario específico"""
    try:
        user = User.query.get_or_404(user_id)
        return render_template('admin/view_user.html', user=user)
    except Exception as e:
        print(f"Error viewing user: {e}")
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Eliminar usuario individual"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Verificar que no se elimine a sí mismo
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'No puedes eliminarte a ti mismo'
            }), 400
        
        # Guardar nombre para el mensaje
        user_name = user.username
        
        # Eliminar usuario
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usuario {user_name} eliminado exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar usuario: {str(e)}'
        }), 500

# ============ RUTAS EXISTENTES ORIGINALES ============

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

# ============ FUNCIONES AUXILIARES ============

def check_user_permission(action, target_user=None):
    """Validar si el usuario actual puede realizar una acción"""
    
    if not current_user.is_authenticated:
        return False, "Usuario no autenticado"
    
    if not current_user.is_admin():
        return False, "No tienes permisos de administrador"
    
    if target_user and target_user.id == current_user.id:
        if action in ['delete', 'deactivate']:
            return False, "No puedes realizar esta acción sobre tu propia cuenta"
    
    return True, "Permitido"