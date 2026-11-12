"""
FastAPI Route Dependencies Module.

Provides reusable dependencies for:
1. Asynchronous database sessions (get_db)
2. JWT Authentication and user identity resolution (get_current_user)
3. Role-Based Access Control (RBAC) authorization (require_admin, require_role)
"""

from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole
from app.security import decode_access_token, oauth2_scheme


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Decodes the Bearer token, fetches the user from the database,
    and verifies that the account is active.
    Raises HTTP 401 Unauthorized if the token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # Query user from database asynchronously
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Contact administrator.",
        )

    return user


def require_role(allowed_role: str) -> Callable:
    """
    Dependency factory that enforces Role-Based Access Control.
    Returns a dependency verifying the current user possesses the required role.
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role != allowed_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires '{allowed_role}' role privileges.",
            )
        return current_user

    return role_checker


# Convenient pre-configured dependency for administrator-only routes
require_admin = require_role(UserRole.ADMIN.value)
