from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, db
from app.forms import LoginForm, RegisterForm

# -----------------------------
# INICIO DE SESIÓN
# -----------------------------
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')

            # Redirigir según el rol del usuario
            if next_page:
                return redirect(next_page)
            elif user.role.name == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif user.role.name == 'teacher':
                return redirect(url_for('main.teacher_dashboard'))
            elif user.role.name == 'student':
                return redirect(url_for('main.student_dashboard'))
            else:
                return redirect('/')
        else:
            flash('Credenciales inválidas. Por favor verifica tu usuario y contraseña.', 'error')

    return render_template('auth/login.html', form=form)

# -----------------------------
# REGISTRO
# -----------------------------
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                flash('El nombre de usuario ya está en uso.', 'error')
            else:
                flash('El email ya está registrado.', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data.lower(),
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role_id=form.role_id.data,
                phone=form.phone.data
            )
            db.session.add(user)
            db.session.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

# -----------------------------
# CERRAR SESIÓN
# -----------------------------
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    return redirect(url_for('main.index'))

# -----------------------------
# PERFIL
# -----------------------------
@login_required
def profile():
    """Perfil del usuario"""
    return render_template('auth/profile.html')

# -----------------------------
# CAMBIAR CONTRASEÑA
# -----------------------------
def change_password():
    """Página para cambiar la contraseña"""
    from app.forms import ChangePasswordForm
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('La contraseña actual es incorrecta.', 'error')
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Contraseña cambiada exitosamente.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)
