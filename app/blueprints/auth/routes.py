from . import auth_bp
from . import login, register, logout, profile, change_password

# Registrar las rutas
auth.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
auth.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
auth.add_url_rule('/logout', 'logout', logout, methods=['GET'])
auth.add_url_rule('/profile', 'profile', profile, methods=['GET'])
auth.add_url_rule('/change_password', 'change_password', change_password, methods=['GET', 'POST'])
