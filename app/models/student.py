# app/models/student.py
from .database import db
from .user import User

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_code = db.Column(db.String(20), unique=True, nullable=False)

    user = db.relationship('User', backref='student', uselist=False)

    def __repr__(self):
        return f'<Student {self.student_code}>'
