import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.main import app
from app.models.database import Base, get_db
from app.models import User, Idea, Vote

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    echo=True
)

TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

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
async def sample_user(db_session):
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$test_hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def sample_idea(db_session, sample_user):
    idea = Idea(
        title="Test Startup Idea",
        description="This is a test idea description",
        category="saas",
        tags="tech,startup",
        user_id=sample_user.id,
        vote_count=5,
        view_count=10
    )
    db_session.add(idea)
    await db_session.commit()
    await db_session.refresh(idea)
    return idea

class TestIdeasEndpoints:
    
    @pytest.mark.asyncio
    async def test_list_ideas_empty(self, client):
        response = client.get("/ideas")
        assert response.status_code == 200
        assert "No ideas found" in response.text
    
    @pytest.mark.asyncio
    async def test_list_ideas_with_data(self, client, sample_idea):
        response = client.get("/ideas")
        assert response.status_code == 200
        assert sample_idea.title in response.text
        assert sample_idea.category in response.text
    
    @pytest.mark.asyncio
    async def test_list_ideas_category_filter(self, client, sample_idea):
        response = client.get("/ideas?category=saas")
        assert response.status_code == 200
        assert sample_idea.title in response.text
        
        response = client.get("/ideas?category=fintech")
        assert response.status_code == 200
        assert sample_idea.title not in response.text
    
    @pytest.mark.asyncio
    async def test_list_ideas_sorting(self, client, sample_idea):
        # Test different sorting options
        response = client.get("/ideas?sort=newest")
        assert response.status_code == 200
        
        response = client.get("/ideas?sort=popular")
        assert response.status_code == 200
        
        response = client.get("/ideas?sort=trending")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_idea_anonymous(self, client):
        idea_data = {
            "title": "New Test Idea",
            "description": "This is a new test idea",
            "category": "fintech",
            "tags": "innovation,finance",
            "is_anonymous": True
        }
        response = client.post("/ideas", data=idea_data)
        assert response.status_code == 200
        assert "created successfully" in response.text
    
    @pytest.mark.asyncio
    async def test_get_idea_detail(self, client, sample_idea):
        response = client.get(f"/ideas/{sample_idea.id}")
        assert response.status_code == 200
        assert sample_idea.title in response.text
        assert sample_idea.description in response.text
        assert sample_idea.category in response.text
    
    @pytest.mark.asyncio
    async def test_get_idea_not_found(self, client):
        response = client.get("/ideas/999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_vote_idea_unauthenticated(self, client, sample_idea):
        response = client.patch(f"/ideas/{sample_idea.id}/vote", data={"vote_type": 1})
        assert response.status_code == 401

class TestVotingLogic:
    
    @pytest.mark.asyncio
    async def test_vote_creation(self, db_session, sample_user, sample_idea):
        # Test upvote
        vote = Vote(user_id=sample_user.id, idea_id=sample_idea.id, vote_type=1)
        db_session.add(vote)
        await db_session.commit()
        
        # Verify vote was created
        from sqlalchemy import select
        result = await db_session.execute(
            select(Vote).where(Vote.user_id == sample_user.id, Vote.idea_id == sample_idea.id)
        )
        saved_vote = result.scalar_one_or_none()
        assert saved_vote is not None
        assert saved_vote.vote_type == 1
    
    @pytest.mark.asyncio
    async def test_duplicate_vote_constraint(self, db_session, sample_user, sample_idea):
        # Create first vote
        vote1 = Vote(user_id=sample_user.id, idea_id=sample_idea.id, vote_type=1)
        db_session.add(vote1)
        await db_session.commit()
        
        # Try to create duplicate vote - should fail
        vote2 = Vote(user_id=sample_user.id, idea_id=sample_idea.id, vote_type=-1)
        db_session.add(vote2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()

class TestModels:
    
    @pytest.mark.asyncio
    async def test_user_creation(self, db_session):
        user = User(
            email="newuser@example.com",
            username="newuser",
            password_hash="hashed_password"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_idea_creation(self, db_session, sample_user):
        idea = Idea(
            title="Model Test Idea",
            description="Testing idea model creation",
            category="healthtech",
            user_id=sample_user.id
        )
        db_session.add(idea)
        await db_session.commit()
        await db_session.refresh(idea)
        
        assert idea.id is not None
        assert idea.title == "Model Test Idea"
        assert idea.vote_count == 0  # Default value
        assert idea.view_count == 0  # Default value
        assert idea.status == "active"  # Default value
        assert idea.created_at is not None
    
    @pytest.mark.asyncio
    async def test_idea_user_relationship(self, db_session, sample_user, sample_idea):
        # Test relationship loading
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        result = await db_session.execute(
            select(Idea).options(selectinload(Idea.user)).where(Idea.id == sample_idea.id)
        )
        idea_with_user = result.scalar_one()
        
        assert idea_with_user.user is not None
        assert idea_with_user.user.id == sample_user.id
        assert idea_with_user.user.username == sample_user.username

class TestAuthentication:
    
    def test_password_hashing(self):
        from app.utils.auth import get_password_hash, verify_password
        
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_jwt_token_creation(self):
        from app.utils.auth import create_access_token
        from jose import jwt
        import os
        
        data = {"sub": "123"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert decoded["sub"] == "123"