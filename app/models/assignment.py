### ARCHIVO: models/assignment.py
from datetime import datetime
from .database import db

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assignment_type = db.Column(db.String(50))  # homework, project, exam, quiz
    max_score = db.Column(db.Float, default=100.0)
    
    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=False)
    
    # Relaciones
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    course = db.relationship('Course', backref='assignments')
    teacher = db.relationship('User', backref='created_assignments')
    
    def __repr__(self):
        return f'<Assignment {self.title} - {self.course.code}>'
    
    @property
    def is_overdue(self):
        return self.due_date and datetime.utcnow() > self.due_date