from datetime import datetime, timedelta
from app import db
from werkzeug.security import generate_password_hash
import secrets

class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', back_populates='refresh_tokens')
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.token = self.generate_token()
        self.expires_at = datetime.utcnow() + timedelta(days=30)
    
    def generate_token(self):
        """Generar un token seguro y único"""
        while True:
            token = secrets.token_urlsafe(32)
            if not RefreshToken.query.filter_by(token=token).first():
                return token
    
    def revoke(self):
        """Revocar el token"""
        self.revoked = True
        db.session.commit()
    
    def is_expired(self):
        """Verificar si el token está expirado"""
        return self.expires_at < datetime.utcnow()
    
    def is_valid(self):
        """Verificar si el token es válido"""
        return not self.revoked and not self.is_expired()
    
    @classmethod
    def verify_token(cls, token):
        """Verificar un token de refresco"""
        refresh_token = cls.query.filter_by(token=token).first()
        if refresh_token and refresh_token.is_valid():
            return refresh_token
        return None
    
    def __repr__(self):
        return f'<RefreshToken {self.token[:10]}...>'
