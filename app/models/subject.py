### ARCHIVO: models/subject.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Importar la instancia de SQLAlchemy desde database.py
from app.models.database import db

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con profesor
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='subject_teacher', lazy=True, overlaps="subject_teacher,subjects_taught")
    
    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'