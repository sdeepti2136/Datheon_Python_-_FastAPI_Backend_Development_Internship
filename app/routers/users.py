"""
User Management Router (Admin Only).

Demonstrates role-based administrative capabilities:
- GET   /api/v1/users: List all registered users
- PATCH /api/v1/users/{user_id}/role: Change user role (user <-> admin)
- PATCH /api/v1/users/{user_id}/status: Activate / deactivate user account
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.logging_config import logger
from app.models import User
from app.schemas import UserResponse, UserRoleUpdate

router = APIRouter(
    prefix="/users",
    tags=["Users - Admin Management"],
)


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin only)",
    description="Returns all registered users in the database. Restricted strictly to administrators.",
)
async def list_users(
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[User]:
    result = await db.execute(select(User).order_by(User.id.asc()))
    users = result.scalars().all()
    return list(users)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user role (Admin only)",
    description="Elevates or changes a user's role between 'user' and 'admin'. Restricted to administrators.",
)
async def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found.",
        )

    # Prevent accidental self-demotion
    if user.id == current_admin.id and role_in.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote their own account role.",
        )

    user.role = role_in.role.value
    await db.flush()
    await db.refresh(user)

    logger.info(
        f"Admin '{current_admin.email}' updated role for user ID {user.id} ({user.email}) to '{user.role}'"
    )
    return user
