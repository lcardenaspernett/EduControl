# models/__init__.py
from .database import db
from .user import User
from .course import Course
from .subject import Subject
from .grade import Grade
from .attendance import Attendance
from .assignment import Assignment
from .submission import Submission
from .configuration import Configuration
from .role import Role

__all__ = [
    'db',
    'User',
    'Course',
    'Subject', 
    'Grade',
    'Attendance',
    'Assignment',
    'Submission',
    'Configuration',  # ← AGREGADA LA COMA QUE FALTABA
    'Role'
]