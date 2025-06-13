print("=== Testing Database with JWT models ===")

try:
    from app import create_app
    from app.models.user import User
    from app.models.token import RefreshToken
    
    app = create_app()
    with app.app_context():
        users_count = User.query.count()
        tokens_count = RefreshToken.query.count()
        
        print(f"Users in DB: {users_count}")
        print(f"Tokens in DB: {tokens_count}")
        
        # Verificar campos de seguridad en User
        user_columns = [column.name for column in User.__table__.columns]
        print(f"User table has {len(user_columns)} columns")
        print(f"Columns: {user_columns}")
        
        security_fields = ['failed_login_attempts', 'locked_until', 'last_login_attempt']
        missing_fields = [field for field in security_fields if field not in user_columns]
        
        if not missing_fields:
            print("✅ All security fields added to User model")
        else:
            print(f"❌ Missing security fields: {missing_fields}")
            
        print("✅ Database test completed successfully")
        
except Exception as e:
    print(f"❌ Database test error: {e}")