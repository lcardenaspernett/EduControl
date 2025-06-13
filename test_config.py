print("=== Testing Security Config ===")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("1. Dotenv: OK")
except Exception as e:
    print("1. Dotenv: ERROR -", e)

print("Trying SecurityConfig...")
try:
    from app.config.security import SecurityConfig
    print("2. SecurityConfig: OK")
    print("   JWT_SECRET_KEY:", SecurityConfig.JWT_SECRET_KEY[:10] + "...")
    print("   MAX_LOGIN_ATTEMPTS:", SecurityConfig.MAX_LOGIN_ATTEMPTS)
except Exception as e:
    print("2. SecurityConfig: ERROR -", e)

print("Trying Extensions...")
try:
    from app.extensions import jwt, limiter
    print("3. Extensions: OK")
except Exception as e:
    print("3. Extensions: ERROR -", e)

print("Trying Models...")
try:
    from app.models.user import User
    from app.models.token import RefreshToken
    print("4. Models: OK")
except Exception as e:
    print("4. Models: ERROR -", e)

print("=== Test completed ===")
