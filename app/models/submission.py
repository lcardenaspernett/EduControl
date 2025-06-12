# models/submission.py
from datetime import datetime
from .database import db

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, default=False)
    
    # Relaciones
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    
    student = db.relationship('User', backref='submission_student', lazy=True, overlaps="submission_student,student_submissions")
    assignment = db.relationship('Assignment', backref='submissions')
    
    # Constraint único - un estudiante solo puede enviar una vez por tarea
    __table_args__ = (
        db.UniqueConstraint('student_id', 'assignment_id', name='unique_submission_per_assignment'),
    )
    
    def __repr__(self):
        return f'<Submission {self.student.username} - {self.assignment.title}>'