from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Importar la instancia de SQLAlchemy desde database.py
from app.models.database import db

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    
    # Permissions
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_courses = db.Column(db.Boolean, default=False)
    can_grade = db.Column(db.Boolean, default=False)
    can_view_reports = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert role to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'can_manage_users': self.can_manage_users,
            'can_manage_courses': self.can_manage_courses,
            'can_grade': self.can_grade,
            'can_view_reports': self.can_view_reports
        }
    
    def is_role(self, role_name):
        """Check if this role matches the given role name (case-insensitive)"""
        if not self.name:
            return False
        return self.name.lower() == role_name.lower()
    
    def __repr__(self):
        return f'<Role {self.name}>'