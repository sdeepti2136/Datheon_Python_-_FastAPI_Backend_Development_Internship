"""
Authentication & Authorization REST Router.

Implements secure registration, login with JWT token issuance,
current user profile retrieval, and rate-limiting protection.
Endpoints:
- POST /api/v1/auth/register: User account creation (Rate-limited)
- POST /api/v1/auth/login: OAuth2/JWT authentication (Rate-limited)
- GET  /api/v1/auth/me: Retrieve current authenticated user profile
- POST /api/v1/auth/refresh: Refresh current access token
"""

from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.dependencies import get_current_user
from app.logging_config import logger
from app.models import User, UserRole
from app.schemas import Token, UserRegister, UserResponse
from app.security import create_access_token, hash_password, verify_password
from app.services.notifications import send_welcome_email

settings = get_settings()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication & Security"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account (Rate limited)",
    description=(
        "Registers a new standard user account. "
        "Validates email uniqueness and password complexity. "
        "Passwords are encrypted with bcrypt before saving. "
        "Protected by rate limiting against automated account creation spam."
    ),
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Conflict: Email address is already registered"},
        429: {"description": "Too Many Requests: Rate limit exceeded"},
    },
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    user_in: UserRegister,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    # Check if email is already taken
    existing_user = await db.execute(select(User).where(User.email == user_in.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{user_in.email}' already exists.",
        )

    # Hash password with bcrypt salt
    hashed = hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed,
        role=UserRole.USER.value,
        is_active=True,
    )

    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    # Queue asynchronous welcome notification
    background_tasks.add_task(
        send_welcome_email,
        user_email=new_user.email,
        user_id=new_user.id,
    )

    logger.info(f"New user registered successfully: ID {new_user.id} ({new_user.email})")
    return new_user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain JWT Access Token (Rate limited)",
    description=(
        "Authenticates user credentials and issues a cryptographically signed JWT token. "
        "Accepts standard OAuth2 form data (username=email, password=password) "
        "compatible with Swagger UI 'Authorize' button. "
        "Protected by rate limiting to mitigate brute-force password guessing."
    ),
    responses={
        200: {"description": "Authentication successful, token issued"},
        401: {"description": "Invalid credentials or inactive account"},
        429: {"description": "Rate limit exceeded (too many login attempts)"},
    },
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    email = form_data.username.strip().lower()
    plain_password = form_data.password

    # Query user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Generic authentication failure to prevent user enumeration attacks
    auth_failed_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        logger.warning(f"Failed login attempt for non-existent email: {email}")
        raise auth_failed_exception

    if not verify_password(plain_password, user.hashed_password):
        logger.warning(f"Failed login attempt (invalid password) for: {email}")
        raise auth_failed_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact the administrator.",
        )

    # Generate JWT token
    token_claims = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
    }
    access_token = create_access_token(data=token_claims)

    logger.info(f"User {user.email} (ID: {user.id}, Role: {user.role}) logged in successfully")
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        email=user.email,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile (Authenticated)",
    description="Returns the profile details of the currently authenticated user.",
    responses={
        200: {"description": "User profile details"},
        401: {"description": "Authentication token missing or invalid"},
    },
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token (Authenticated)",
    description="Issues a refreshed JWT token for a currently authenticated active user.",
)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
) -> Token:
    token_claims = {
        "sub": current_user.email,
        "user_id": current_user.id,
        "role": current_user.role,
    }
    new_token = create_access_token(data=token_claims)
    return Token(
        access_token=new_token,
        token_type="bearer",
        role=current_user.role,
        user_id=current_user.id,
        email=current_user.email,
    )
