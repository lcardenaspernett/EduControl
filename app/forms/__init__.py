# app/forms/__init__.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    username = StringField('User', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida')
    ])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    """Formulario de registro"""
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=20, message='El usuario debe tener entre 3 y 20 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Ingresa un email válido'),
        Length(max=120, message='El email no puede exceder 120 caracteres')
    ])
    first_name = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    last_name = StringField('Apellido', validators=[
        DataRequired(message='El apellido es requerido'),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    phone = StringField('Teléfono', validators=[
        Optional(),
        Length(min=10, max=15, message='Ingresa un teléfono válido')
    ])
    role_id = SelectField('Rol', choices=[
        ('1', 'Admin'),
        ('2', 'Profesor'),
        ('3', 'Estudiante')
    ], validators=[DataRequired(message='Selecciona un rol')], coerce=int)
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    password2 = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Confirma tu contraseña'),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        """Validar que el username sea único"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso.')
        
        # Validar formato del username
        if not re.match("^[a-zA-Z0-9_]+$", username.data):
            raise ValidationError('El usuario solo puede contener letras, números y guiones bajos.')

    def validate_email(self, email):
        """Validar que el email sea único"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Este email ya está registrado.')

    def validate_phone(self, phone):
        """Validar formato del teléfono"""
        if phone.data:
            # Limpiar el teléfono de espacios y caracteres especiales
            phone_clean = re.sub(r'[^\d]', '', phone.data)
            if len(phone_clean) < 10:
                raise ValidationError('Ingresa un número de teléfono válido.')

class CourseForm(FlaskForm):
    """Formulario para crear/editar cursos"""
    nombre = StringField('Nombre del Curso', validators=[
        DataRequired(message='El nombre del curso es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])
    codigo = StringField('Código del Curso', validators=[
        DataRequired(message='El código del curso es requerido'),
        Length(min=3, max=20, message='El código debe tener entre 3 y 20 caracteres')
    ])
    descripcion = TextAreaField('Descripción', validators=[
        Length(max=500, message='La descripción no puede exceder 500 caracteres')
    ])
    creditos = SelectField('Créditos', choices=[
        ('1', '1 Crédito'),
        ('2', '2 Créditos'),
        ('3', '3 Créditos'),
        ('4', '4 Créditos'),
        ('5', '5 Créditos')
    ], validators=[DataRequired(message='Selecciona el número de créditos')])
    submit = SubmitField('Guardar Curso')

class UserForm(FlaskForm):
    """Formulario para crear/editar usuarios (solo admin)"""
    username = StringField('User', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Ingresa un email válido'),
        Length(max=120, message='El email no puede exceder 120 caracteres')
    ])
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    apellido = StringField('Apellido', validators=[
        DataRequired(message='El apellido es requerido'),
        Length(min=2, max=100, message='El apellido debe tener entre 2 y 100 caracteres')
    ])
    rol = SelectField('Rol', choices=[
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor'),
        ('admin', 'Administrador')
    ], validators=[DataRequired(message='Selecciona un rol')])
    activo = BooleanField('User Activo', default=True)
    submit = SubmitField('Guardar User')