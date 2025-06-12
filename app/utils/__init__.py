import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.models import User, db

def generate_token(user_id, remember=False):
    """Genera un token JWT para el usuario"""
    expire_time = timedelta(days=7 if remember else hours=24)
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + expire_time,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.query.get(payload['user_id'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def refresh_token(token):
    """Refresca un token JWT válido"""
    user = verify_token(token)
    if user:
        return generate_token(user.id)
    return None

def decode_token(token):
    """Decodifica un token JWT y retorna el payload"""
    try:
        return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired')
    except jwt.InvalidTokenError:
        raise Exception('Token is invalid')

def get_user_from_token(token):
    """Obtiene el usuario desde un token JWT"""
    try:
        payload = decode_token(token)
        user = User.query.get(payload['user_id'])
        if user and user.activo:
            return user
        return None
    except:
        return None

def is_token_expired(token):
    """Verifica si un token ha expirado"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], 
                           algorithms=['HS256'], options={'verify_exp': False})
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
            return datetime.utcnow() > exp_datetime
        return True
    except:
        return True