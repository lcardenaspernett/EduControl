from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, User
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

courses = Blueprint('courses', __name__)

# Formulario básico para cursos (puedes moverlo a forms.py después)
class CourseForm(FlaskForm):
    nombre = StringField('Nombre del Curso', validators=[DataRequired(), Length(min=2, max=100)])
    descripcion = TextAreaField('Descripción', validators=[Length(max=500)])
    profesor_id = SelectField('Profesor', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar Curso')

@courses.route('/create', methods=['GET', 'POST'])
@login_required
def create_course():
    # Solo admin puede crear cursos
    if current_user.rol != 'admin':
        flash('No tienes permisos para crear cursos.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = CourseForm()
    
    # Llenar opciones de profesores
    profesores = User.query.filter_by(rol='profesor').all()
    form.profesor_id.choices = [(p.id, p.nombre) for p in profesores]
    
    if form.validate_on_submit():
        # Por ahora solo simulamos la creación
        flash(f'Curso "{form.nombre.data}" creado exitosamente.', 'success')
        return redirect(url_for('courses.list_courses'))
    
    return render_template('admin/create_course.html', form=form)

@courses.route('/list')
@login_required
def list_courses():
    # Solo admin y profesores pueden ver cursos
    if current_user.rol not in ['admin', 'profesor']:
        flash('No tienes permisos para ver la lista de cursos.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Por ahora retornamos una lista vacía
    cursos = []
    return render_template('admin/list_courses.html', cursos=cursos)