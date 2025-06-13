import unittest
from app import create_app
from app.models import User, Role
from app.extensions import db
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

class TestAuthJWT(unittest.TestCase):
    def setUp(self):
        """Configurar la aplicación de prueba"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        # Crear contexto de aplicación
        with self.app.app_context():
            # Crear roles
            admin_role = Role(name='admin', description='Administrador')
            teacher_role = Role(name='teacher', description='Profesor')
            student_role = Role(name='student', description='Estudiante')
            
            # Crear usuario de prueba
            self.test_user = User(
                username='testuser',
                email='test@example.com',
                password='Test123!',
                first_name='Test',
                last_name='User',
                role=admin_role
            )
            
            # Agregar al contexto
            db.session.add(admin_role)
            db.session.add(teacher_role)
            db.session.add(student_role)
            db.session.add(self.test_user)
            db.session.commit()
    
    def tearDown(self):
        """Limpiar la base de datos después de cada prueba"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_login_success(self):
        """Probar login exitoso"""
        with self.app.app_context():
            response = self.client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'Test123!'
            })
            
            self.assertEqual(response.status_code, 200)
            data = response.json
            self.assertIn('access_token', data)
            self.assertIn('refresh_token', data)
            self.assertIn('user', data)
            
    def test_login_invalid_credentials(self):
        """Probar login con credenciales inválidas"""
        with self.app.app_context():
            response = self.client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            
            self.assertEqual(response.status_code, 401)
            
    def test_refresh_token(self):
        """Probar refrescar token"""
        with self.app.app_context():
            # Primero obtener tokens
            login_response = self.client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'Test123!'
            })
            
            refresh_token = login_response.json['refresh_token']
            
            # Intentar refrescar token
            response = self.client.post('/api/auth/refresh', 
                                      headers={'Authorization': f'Bearer {refresh_token}'})
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('access_token', response.json)
    
    def test_protected_route(self):
        """Probar ruta protegida"""
        with self.app.app_context():
            # Primero obtener tokens
            login_response = self.client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'Test123!'
            })
            
            access_token = login_response.json['access_token']
            
            # Intentar acceder a ruta protegida
            response = self.client.get('/api/auth/profile',
                                     headers={'Authorization': f'Bearer {access_token}'})
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('user', response.json)
    
    def test_rate_limit(self):
        """Probar límite de tasa en login"""
        with self.app.app_context():
            # Intentar login 5 veces con credenciales incorrectas
            for _ in range(5):
                response = self.client.post('/api/auth/login', json={
                    'username': 'testuser',
                    'password': 'wrongpassword'
                })
                
            # El sexto intento debería ser bloqueado
            response = self.client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            
            self.assertEqual(response.status_code, 429)  # Too Many Requests

if __name__ == '__main__':
    unittest.main()
