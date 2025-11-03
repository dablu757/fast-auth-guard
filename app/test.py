import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.session import get_db
from app.db.models import User
from app.utils.jwt import create_access_token


# ---------- Test Setup ----------
@pytest.fixture(scope="module")
def event_loop():
    """Create a fresh event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def async_client():
    """Provide an async test client for FastAPI."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(scope="module")
async def db_session() -> AsyncSession:
    """Provide a database session."""
    async for session in get_db():
        yield session
        break


# ---------- Helper ----------
async def create_test_user(db: AsyncSession, email="test@example.com", name="Test User"):
    """Create and persist a test user."""
    user = User(email=email, name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------- Test Cases ----------

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Basic sanity test."""
    response = await async_client.get("/")
    assert response.status_code in [200, 404]  # depending on whether root route exists


@pytest.mark.asyncio
async def test_user_me_unauthorized(async_client: AsyncClient):
    """Access /users/me without login should fail."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Authentication token" in response.text


@pytest.mark.asyncio
async def test_user_me_authorized(async_client: AsyncClient, db_session: AsyncSession):
    """Simulate login and test /users/me."""
    # Create fake user
    user = await create_test_user(db_session)

    # Create JWT and set as cookie
    token = create_access_token(data={"sub": str(user.id)})
    cookies = {"access_token": token}

    response = await async_client.get("/api/v1/users/me", cookies=cookies)
    assert response.status_code == 200
    assert response.json()["email"] == user.email


@pytest.mark.asyncio
async def test_get_all_users(async_client: AsyncClient, db_session: AsyncSession):
    """Test /users/all route."""
    user = await create_test_user(db_session, email="admin@example.com")
    token = create_access_token(data={"sub": str(user.id)})
    cookies = {"access_token": token}

    response = await async_client.get("/api/v1/users/all", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(u["email"] == "admin@example.com" for u in data)
