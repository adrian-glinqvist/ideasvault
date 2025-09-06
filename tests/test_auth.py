import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.models import User
from app.utils.auth import get_password_hash, create_access_token

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client(db_session):
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

@pytest.fixture
async def existing_user(db_session):
    user = User(
        email="existing@example.com",
        username="existing_user",
        password_hash=get_password_hash("password123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

class TestUserRegistration:
    
    def test_register_new_user(self, client):
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123"
        }
        response = client.post("/auth/register", data=user_data)
        assert response.status_code == 200
        assert "Welcome to IdeasVault" in response.text
        assert "newuser" in response.text
    
    def test_register_duplicate_email(self, client, existing_user):
        user_data = {
            "email": existing_user.email,
            "username": "different_username",
            "password": "password123"
        }
        response = client.post("/auth/register", data=user_data)
        assert response.status_code == 200
        assert "Email already registered" in response.text
    
    def test_register_duplicate_username(self, client, existing_user):
        user_data = {
            "email": "different@example.com",
            "username": existing_user.username,
            "password": "password123"
        }
        response = client.post("/auth/register", data=user_data)
        assert response.status_code == 200
        assert "Username already taken" in response.text
    
    def test_register_missing_fields(self, client):
        # Test missing email
        response = client.post("/auth/register", data={"username": "test", "password": "pass"})
        assert response.status_code == 422
        
        # Test missing username
        response = client.post("/auth/register", data={"email": "test@example.com", "password": "pass"})
        assert response.status_code == 422
        
        # Test missing password
        response = client.post("/auth/register", data={"email": "test@example.com", "username": "test"})
        assert response.status_code == 422

class TestUserLogin:
    
    def test_login_valid_credentials(self, client, existing_user):
        login_data = {
            "email": existing_user.email,
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        assert "Welcome back" in response.text
        assert existing_user.username in response.text
    
    def test_login_invalid_email(self, client):
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        assert "Invalid email or password" in response.text
    
    def test_login_invalid_password(self, client, existing_user):
        login_data = {
            "email": existing_user.email,
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        assert "Invalid email or password" in response.text
    
    def test_login_missing_fields(self, client):
        # Test missing email
        response = client.post("/auth/login", data={"password": "password123"})
        assert response.status_code == 422
        
        # Test missing password
        response = client.post("/auth/login", data={"email": "test@example.com"})
        assert response.status_code == 422

class TestUserProfile:
    
    def test_profile_unauthenticated(self, client):
        response = client.get("/auth/profile")
        assert response.status_code == 401
    
    def test_profile_authenticated(self, client, existing_user):
        # Create a valid JWT token
        token = create_access_token(data={"sub": str(existing_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/auth/profile", headers=headers)
        assert response.status_code == 200
        assert existing_user.username in response.text
        assert existing_user.email in response.text

class TestPasswordSecurity:
    
    def test_password_hashing(self):
        from app.utils.auth import get_password_hash, verify_password
        
        password = "test_password_123!@#"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        
        # Should not verify with wrong password
        assert verify_password("wrong_password", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        from app.utils.auth import get_password_hash
        
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password1")  # Same password
        hash3 = get_password_hash("password2")  # Different password
        
        # Same password should produce different hashes (salt)
        assert hash1 != hash2
        # Different passwords should produce different hashes
        assert hash1 != hash3
        assert hash2 != hash3

class TestJWTTokens:
    
    def test_token_creation_and_verification(self):
        from app.utils.auth import create_access_token
        from jose import jwt
        import os
        
        user_id = "123"
        token = create_access_token(data={"sub": user_id})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Verify token can be decoded
        secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert decoded["sub"] == user_id
        assert "exp" in decoded  # Expiration claim should be present
    
    def test_token_expiration(self):
        from app.utils.auth import create_access_token
        from datetime import timedelta
        from jose import jwt, JWTError
        import os
        import time
        
        # Create a token that expires in 1 second
        token = create_access_token(
            data={"sub": "123"}, 
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert decoded["sub"] == "123"
        
        # Wait for expiration and verify token is invalid
        time.sleep(2)
        with pytest.raises(JWTError):
            jwt.decode(token, secret_key, algorithms=["HS256"])

class TestUserModel:
    
    @pytest.mark.asyncio
    async def test_user_creation_with_required_fields(self, db_session):
        user = User(
            email="model_test@example.com",
            username="model_test_user",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "model_test@example.com"
        assert user.username == "model_test_user"
        assert user.is_admin is False  # Default value
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_user_unique_constraints(self, db_session):
        # Create first user
        user1 = User(
            email="unique@example.com",
            username="unique_user",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create user with same email - should fail
        user2 = User(
            email="unique@example.com",  # Same email
            username="different_user",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()
        
        # Rollback and try with same username
        await db_session.rollback()
        
        user3 = User(
            email="different@example.com",
            username="unique_user",  # Same username
            password_hash=get_password_hash("password123")
        )
        db_session.add(user3)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()

class TestAuthenticationFlow:
    
    def test_full_registration_login_flow(self, client):
        # Step 1: Register a new user
        register_data = {
            "email": "flow_test@example.com",
            "username": "flow_test_user",
            "password": "secure_password_123"
        }
        response = client.post("/auth/register", data=register_data)
        assert response.status_code == 200
        assert "Welcome to IdeasVault" in response.text
        
        # Step 2: Login with the same credentials
        login_data = {
            "email": "flow_test@example.com",
            "password": "secure_password_123"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        assert "Welcome back" in response.text