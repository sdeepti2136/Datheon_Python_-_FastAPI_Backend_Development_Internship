"""
Automated Test Suite for User Authentication and RBAC (Task 2).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User
from app.security import create_access_token

pytestmark = pytest.mark.asyncio


async def test_user_registration_success(client: AsyncClient):
    """
    Verifies that a new user can successfully register an account.
    """
    payload = {
        "email": "new_student@datheon.in",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "hashed_password" not in data  # Never leak hash!


async def test_duplicate_registration_rejected(client: AsyncClient):
    """
    Verifies that registering with an already existing email results in 409 Conflict.
    """
    payload = {
        "email": "duplicate_check@datheon.in",
        "password": "Password123!",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


async def test_registration_weak_password_rejected(client: AsyncClient):
    """
    Verifies that passwords under 8 characters or lacking digits/letters are rejected with 422.
    """
    # Too short (< 8 chars)
    res_short = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak1@datheon.in", "password": "abc"},
    )
    assert res_short.status_code == 422

    # No digits
    res_no_digit = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak2@datheon.in", "password": "onlylettershere"},
    )
    assert res_no_digit.status_code == 422


async def test_login_successful(client: AsyncClient):
    """
    Verifies login with valid credentials issues a JWT Bearer token.
    """
    email = "login_success@datheon.in"
    password = "MyPassword2026!"

    # Register first
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    # Login via OAuth2 form data
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["email"] == email


async def test_login_invalid_password(client: AsyncClient):
    """
    Verifies that login with wrong password returns 401 Unauthorized.
    """
    email = "test_wrong_pwd@datheon.in"
    password = "CorrectPassword123!"

    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


async def test_login_nonexistent_user(client: AsyncClient):
    """
    Verifies login for an unverified/unknown email returns generic 401.
    """
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@datheon.in", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401


async def test_get_current_user_profile(client: AsyncClient, user_auth_headers: dict):
    """
    Verifies /api/v1/auth/me returns the profile of the authenticated user.
    """
    response = await client.get("/api/v1/auth/me", headers=user_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "standard_test@datheon.local"
    assert data["role"] == "user"


async def test_get_profile_invalid_token(client: AsyncClient):
    """
    Verifies that requests with malformed tokens receive 401 Unauthorized.
    """
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert response.status_code == 401


async def test_inactive_user_access_blocked(client: AsyncClient, db_session):
    """
    Verifies that inactive users cannot access protected resources.
    """
    # Retrieve user from DB and deactivate
    result = await db_session.execute(
        select(User).where(User.email == "standard_test@datheon.local")
    )
    user = result.scalar_one_or_none()
    if user:
        user.is_active = False
        await db_session.commit()

        # Attempt to access /me with their token
        token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "Inactive user account" in response.json()["detail"]
