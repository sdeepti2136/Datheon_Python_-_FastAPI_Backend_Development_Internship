"""
Pytest Test Suite Configuration and Shared Fixtures.

Configures an isolated SQLite test database, AsyncClient HTTP test runner,
dependency overrides, and authentication fixtures for normal users and admins.
"""

import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole
from app.security import create_access_token, hash_password

# Dedicated isolated SQLite database for automated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_datheon_bookstore.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_database():
    """
    Session-level fixture: creates database tables prior to test suite execution,
    and drops all tables upon completion.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Function-level fixture yielding an isolated AsyncSession.
    Ensures state isolation between consecutive test cases.
    """
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an asynchronous HTTP test client bound to the FastAPI application
    with database dependency overridden to point to the test database.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """
    Creates and returns a verified administrator user in the test database.
    """
    admin_email = "admin_test@datheon.local"
    user = User(
        email=admin_email,
        hashed_password=hash_password("AdminP@ssword123"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_auth_headers(test_admin: User) -> dict:
    """
    Generates a valid Authorization header containing an admin JWT token.
    """
    token = create_access_token(
        data={"sub": test_admin.email, "user_id": test_admin.id, "role": test_admin.role}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Creates and returns a standard non-admin user in the test database.
    """
    user_email = "standard_test@datheon.local"
    user = User(
        email=user_email,
        hashed_password=hash_password("UserP@ssword123"),
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_auth_headers(test_user: User) -> dict:
    """
    Generates a valid Authorization header containing a standard user JWT token.
    """
    token = create_access_token(
        data={"sub": test_user.email, "user_id": test_user.id, "role": test_user.role}
    )
    return {"Authorization": f"Bearer {token}"}
