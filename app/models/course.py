from datetime import datetime
from .database import db

# Tabla de asociación para estudiantes inscritos en cursos
enrollments = db.Table('enrollments',
    db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('enrolled_at', db.DateTime, default=datetime.utcnow)
)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relación con profesor (Teacher)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='course_teacher', lazy=True, overlaps="course_teacher,courses_taught")
    
    # Relación con materia
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    subject = db.relationship('Subject', backref='courses')
    
    # Relación many-to-many con estudiantes
    students = db.relationship('User', 
                             secondary=enrollments,
                             primaryjoin='Course.id == enrollments.c.course_id',
                             secondaryjoin='User.id == enrollments.c.student_id',
                             backref='enrolled_courses')
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'
    
    def get_student_count(self):
        return len(self.students)
    
    def is_student_enrolled(self, user_id):
        return any(student.id == user_id for student in self.students)