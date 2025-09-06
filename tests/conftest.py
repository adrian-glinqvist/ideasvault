"""
Shared test configuration and fixtures for the IdeasVault test suite.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.models import User, Idea, Vote
from app.utils.auth import get_password_hash, create_access_token

# Test database URL - use in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test database engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client(test_db: AsyncSession) -> TestClient:
    """Create a test client with database dependency override."""
    def override_get_db():
        return test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up override
    del app.dependency_overrides[get_db]

# User fixtures
@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("testpassword123")
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
async def admin_user(test_db: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("adminpassword123"),
        is_admin=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
async def second_user(test_db: AsyncSession) -> User:
    """Create a second test user for multi-user tests."""
    user = User(
        email="user2@example.com",
        username="testuser2",
        password_hash=get_password_hash("testpassword123")
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

# Idea fixtures
@pytest.fixture
async def test_idea(test_db: AsyncSession, test_user: User) -> Idea:
    """Create a test idea."""
    idea = Idea(
        title="Revolutionary AI Startup",
        description="An innovative AI-powered platform that revolutionizes how people interact with technology through natural language processing and machine learning.",
        category="saas",
        tags="ai,ml,nlp,innovation",
        user_id=test_user.id,
        vote_count=10,
        view_count=50
    )
    test_db.add(idea)
    await test_db.commit()
    await test_db.refresh(idea)
    return idea

@pytest.fixture
async def anonymous_idea(test_db: AsyncSession) -> Idea:
    """Create an anonymous test idea."""
    idea = Idea(
        title="Anonymous Startup Concept",
        description="A brilliant startup idea submitted anonymously to protect intellectual property while getting community feedback.",
        category="fintech",
        tags="fintech,blockchain,crypto",
        user_id=None,
        is_anonymous=True,
        vote_count=3,
        view_count=25
    )
    test_db.add(idea)
    await test_db.commit()
    await test_db.refresh(idea)
    return idea

@pytest.fixture
async def multiple_ideas(test_db: AsyncSession, test_user: User, second_user: User) -> list[Idea]:
    """Create multiple test ideas for testing lists and filters."""
    ideas = [
        Idea(
            title="SaaS Platform for Small Business",
            description="Comprehensive business management platform",
            category="saas",
            tags="business,management",
            user_id=test_user.id,
            vote_count=15,
            view_count=100
        ),
        Idea(
            title="FinTech Payment Solution",
            description="Revolutionary payment processing system",
            category="fintech", 
            tags="payments,fintech",
            user_id=second_user.id,
            vote_count=8,
            view_count=75
        ),
        Idea(
            title="HealthTech Telemedicine App",
            description="Telemedicine platform for remote consultations",
            category="healthtech",
            tags="health,telemedicine", 
            user_id=test_user.id,
            vote_count=20,
            view_count=150
        ),
        Idea(
            title="E-commerce Marketplace",
            description="Niche marketplace for artisan products",
            category="ecommerce",
            tags="marketplace,artisan",
            user_id=second_user.id,
            vote_count=5,
            view_count=60
        )
    ]
    
    for idea in ideas:
        test_db.add(idea)
    
    await test_db.commit()
    
    for idea in ideas:
        await test_db.refresh(idea)
    
    return ideas

# Vote fixtures
@pytest.fixture
async def test_vote(test_db: AsyncSession, test_user: User, test_idea: Idea) -> Vote:
    """Create a test vote."""
    vote = Vote(
        user_id=test_user.id,
        idea_id=test_idea.id,
        vote_type=1  # Upvote
    )
    test_db.add(vote)
    await test_db.commit()
    await test_db.refresh(vote)
    return vote

# Authentication fixtures
@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create a valid JWT token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def admin_auth_token(admin_user: User) -> str:
    """Create a valid JWT token for the admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})

@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers with the test user's token."""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def admin_headers(admin_auth_token: str) -> dict:
    """Create authorization headers with the admin user's token."""
    return {"Authorization": f"Bearer {admin_auth_token}"}

# Common test data
@pytest.fixture
def sample_idea_data() -> dict:
    """Sample data for creating ideas in tests."""
    return {
        "title": "Test Startup Idea",
        "description": "This is a comprehensive test of our idea creation system with a longer description that provides meaningful content for testing purposes.",
        "category": "saas",
        "tags": "test,innovation,startup",
        "is_anonymous": False
    }

@pytest.fixture
def sample_user_data() -> dict:
    """Sample data for creating users in tests."""
    return {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "securepassword123"
    }

@pytest.fixture
def sample_login_data() -> dict:
    """Sample data for login tests."""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }