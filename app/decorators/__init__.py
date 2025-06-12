"""
Módulo de decoradores para EduControl
Contiene decoradores de autorización y validación
"""

from .auth_decorators import (
    role_required,
    admin_required,
    teacher_required,
    student_required,
    api_auth_required,
    api_role_required
)

# Alias para compatibilidad
check_user_permissions = api_role_required

__all__ = [
    'role_required',
    'admin_required', 
    'teacher_required',
    'student_required',
    'api_auth_required',
    'check_user_permissions'
]
