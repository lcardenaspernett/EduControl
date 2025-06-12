### ARCHIVO: models/grade.py
from datetime import datetime
from .database import db

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, default=100.0)
    grade_type = db.Column(db.String(50))  # exam, quiz, homework, project, etc.
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'))
    
    student = db.relationship('User', backref='grade_student', lazy=True, overlaps="grade_student,student_grades")
    course = db.relationship('Course', backref='grades')
    assignment = db.relationship('Assignment', backref='grades')
    
    @property
    def percentage(self):
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0
    
    def __repr__(self):
        return f'<Grade {self.student.username} - {self.score}/{self.max_score}>'