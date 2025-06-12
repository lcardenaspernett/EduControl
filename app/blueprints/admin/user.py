from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import db, User as User
from ..forms import RegisterForm

users = Blueprint('users', __name__)

@users.route('/create', methods=['GET', 'POST'])
@login_required
def create_user():
    # Solo admin puede crear usuarios
    if current_user.rol != 'admin':
        flash('No tienes permisos para crear usuarios.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            nombre=form.nombre.data,
            email=form.email.data.lower(),
            password=hashed_password,
            rol=form.rol.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {new_user.nombre} creado exitosamente.', 'success')
        return redirect(url_for('users.list_users'))
    
    return render_template('admin/create_user.html', form=form)

@users.route('/list')
@login_required
def list_users():
    # Solo admin puede ver lista de usuarios
    if current_user.rol != 'admin':
        flash('No tienes permisos para ver la lista de usuarios.', 'error')
        return redirect(url_for('main.dashboard'))
    
    usuarios = User.query.all()
    return render_template('admin/list_users.html', usuarios=usuarios)

@users.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Solo admin puede editar usuarios
    if current_user.rol != 'admin':
        flash('No tienes permisos para editar usuarios.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = RegisterForm(obj=user)
    
    if form.validate_on_submit():
        user.nombre = form.nombre.data
        user.email = form.email.data.lower()
        user.rol = form.rol.data
        
        # Solo actualizar contraseña si se proporciona una nueva
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash(f'User {user.nombre} actualizado exitosamente.', 'success')
        return redirect(url_for('users.list_users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@users.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Solo admin puede eliminar usuarios
    if current_user.rol != 'admin':
        flash('No tienes permisos para eliminar usuarios.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # No permitir que el admin se elimine a sí mismo
    if user.id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'error')
        return redirect(url_for('users.list_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.nombre} eliminado exitosamente.', 'success')
    return redirect(url_for('users.list_users'))