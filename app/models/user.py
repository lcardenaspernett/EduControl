from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.models.database import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Campos de seguridad
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(128), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    last_login_attempt = db.Column(db.DateTime, nullable=True)
    
    # Foreign Key - CORREGIDO
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    # Relationships - CORREGIDO
    role = db.relationship('Role', backref='user_roles', lazy='joined')  # Usar lazy='joined' para cargar el rol siempre
    
    # Relación con refresh tokens
    refresh_tokens = db.relationship('RefreshToken', back_populates='user', lazy=True)
    
    # Propiedad para obtener el nombre del rol
    @property
    def role_name(self):
        return self.role.name if self.role else None
    
    # Teacher-specific relationships
    courses_taught = db.relationship('Course', foreign_keys='Course.teacher_id', backref='course_teacher', lazy='dynamic', overlaps="course_teacher,courses_taught")
    subjects_taught = db.relationship('Subject', foreign_keys='Subject.teacher_id', backref='subject_teacher', lazy='dynamic', overlaps="subject_teacher,subjects_taught")
    
    # Student-specific relationships
    student_grades = db.relationship('Grade', backref='grade_student', lazy=True, overlaps="grade_student,student_grades")
    student_attendances = db.relationship('Attendance', backref='attendance_student', lazy=True, overlaps="attendance_student,student_attendances")
    student_submissions = db.relationship('Submission', backref='submission_student', lazy=True, overlaps="submission_student,student_submissions")
    
    def __init__(self, username, email, password, first_name, last_name, role_id=None, **kwargs):
        self.username = username
        self.email = email.lower()
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role_id = role_id
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login = None
        self.password_reset_token = None
        self.password_reset_expires = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def role_name(self):
        return self.role.name if self.role else None

    @property
    def is_admin(self):
        return self.role.name == 'admin' if self.role else False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role and (self.role.is_role('admin') or self.role.is_role('administrador'))
    
    @property
    def is_teacher(self):
        """Check if user is teacher"""
        return self.role and (self.role.is_role('teacher') or self.role.is_role('profesor'))
    
    @property
    def is_student(self):
        """Check if user is student"""
        return self.role and (self.role.is_role('student') or self.role.is_role('estudiante'))
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if not self.role:
            return False
        return getattr(self.role, permission, False)
    
    def get_courses(self):
        """Get courses associated with user based on role"""
        if self.is_teacher:
            return self.courses_taught
        elif self.is_student:
            # Get courses through grades/enrollments
            return [grade.course for grade in self.enrollments]
        return []
    
    def get_subjects(self):
        """Get subjects associated with user based on role"""
        if self.is_teacher:
            return self.subjects_taught
        elif self.is_student:
            # Get subjects through courses
            courses = self.get_courses()
            subjects = []
            for course in courses:
                if hasattr(course, 'subjects'):
                    subjects.extend(course.subjects)
            return list(set(subjects))  # Remove duplicates
        return []
    
    def get_attendance_rate(self, course_id=None, subject_id=None):
        """Calculate attendance rate for student"""
        if not self.is_student:
            return None
        
        query = Attendance.query.filter_by(student_id=self.id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        total_classes = query.count()
        if total_classes == 0:
            return 0
        
        present_classes = query.filter_by(present=True).count()
        return round((present_classes / total_classes) * 100, 2)
    
    def get_average_grade(self, course_id=None, subject_id=None):
        """Calculate average grade for student"""
        if not self.is_student:
            return None
        
        query = Grade.query.filter_by(student_id=self.id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        grades = [g.score for g in query.all() if g.score is not None]
        if not grades:
            return None
        
        return round(sum(grades) / len(grades), 2)
    
    def can_edit_user(self, target_user):
        """Check if current user can edit target user"""
        if self.is_admin:
            return True
        if self.id == target_user.id:
            return True
        return False
    
    def can_view_user(self, target_user):
        """Check if current user can view target user"""
        if self.is_admin or self.is_teacher:
            return True
        if self.id == target_user.id:
            return True
        return False
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_sensitive else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone if include_sensitive else None,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'address': self.address if include_sensitive else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'role': self.role.to_dict() if self.role else None
        }
        return data
    
    def __repr__(self):
        return f'<User {self.username}: {self.full_name}>'
    
    def __str__(self):
        return self.full_name


# Imports necesarios para las relaciones
from .grade import Grade
from .attendance import Attendance
from .token import RefreshToken
from .course import Course
from .subject import Subject
from .submission import Submission