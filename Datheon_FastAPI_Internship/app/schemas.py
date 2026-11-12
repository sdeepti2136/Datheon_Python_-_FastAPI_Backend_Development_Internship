"""
Pydantic Validation and Serialization Schemas.

Defines strict input validation, data sanitization, and output serialization
for BookStore resources, authentication tokens, and user profiles.
Utilizes Pydantic V2 syntax (model_config, Field, field_validator).
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import UserRole


# ==============================================================================
# BOOK SCHEMAS
# ==============================================================================

class BookBase(BaseModel):
    """
    Base attributes for a Book resource.
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title of the book",
        examples=["FastAPI Modern Web APIs"],
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the author",
        examples=["Bill Lubanovic"],
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Comprehensive summary or overview of the book",
        examples=["A complete guide to designing high-performance backend APIs using FastAPI."],
    )
    price: float = Field(
        ...,
        gt=0.0,
        description="Retail price (must be greater than 0)",
        examples=[39.99],
    )
    isbn: str = Field(
        ...,
        description="International Standard Book Number (10 or 13 digits)",
        examples=["9781492080770"],
    )
    publication_year: int = Field(
        ...,
        ge=1400,
        le=2030,
        description="Publication calendar year",
        examples=[2023],
    )

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str) -> str:
        """
        Validates ISBN format: strips hyphens/spaces and verifies length is 10 or 13.
        """
        cleaned = re.sub(r"[-\s]", "", value.strip())
        if len(cleaned) not in (10, 13):
            raise ValueError("ISBN must be either 10 or 13 digits (excluding hyphens)")
        if not re.match(r"^[0-9]{9}[0-9X]$|^[0-9]{13}$", cleaned, re.IGNORECASE):
            raise ValueError("ISBN contains invalid characters")
        return cleaned

    @field_validator("title", "author")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or contain only whitespace")
        return trimmed


class BookCreate(BookBase):
    """
    Payload required to register a new book.
    """
    pass


class BookUpdate(BaseModel):
    """
    Payload for partial or full updates to an existing book.
    All fields are optional.
    """
    title: Optional[str] = Field(
        None, min_length=1, max_length=255, examples=["Advanced FastAPI Patterns"]
    )
    author: Optional[str] = Field(
        None, min_length=1, max_length=255, examples=["Sebastián Ramírez"]
    )
    description: Optional[str] = Field(
        None, max_length=2000, examples=["Updated comprehensive handbook."]
    )
    price: Optional[float] = Field(
        None, gt=0.0, examples=[44.99]
    )
    isbn: Optional[str] = Field(
        None, examples=["9781492080770"]
    )
    publication_year: Optional[int] = Field(
        None, ge=1400, le=2030, examples=[2024]
    )

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = re.sub(r"[-\s]", "", value.strip())
        if len(cleaned) not in (10, 13):
            raise ValueError("ISBN must be either 10 or 13 digits (excluding hyphens)")
        if not re.match(r"^[0-9]{9}[0-9X]$|^[0-9]{13}$", cleaned, re.IGNORECASE):
            raise ValueError("ISBN contains invalid characters")
        return cleaned


class BookResponse(BookBase):
    """
    Response schema returning complete book metadata.
    """
    id: int = Field(..., description="Unique database ID of the book")
    created_by_user_id: Optional[int] = Field(
        None, description="User ID of the administrator who registered the book"
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookListResponse(BaseModel):
    """
    Paginated response envelope for book collection queries.
    """
    total: int = Field(..., description="Total number of books matching search filters")
    limit: int = Field(..., description="Maximum books returned per page")
    offset: int = Field(..., description="Number of books skipped")
    items: list[BookResponse] = Field(..., description="List of books for the requested page")


# ==============================================================================
# AUTH & USER SCHEMAS
# ==============================================================================

class UserRegister(BaseModel):
    """
    Payload for new user registration.
    """
    email: EmailStr = Field(
        ..., description="Valid personal or work email address", examples=["learner@datheon.in"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Account password (minimum 8 characters, must contain at least one digit and letter)",
        examples=["StrongP@ssw0rd2026"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, password: str) -> str:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("Password must contain at least one alphabetical character")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one numeric digit")
        return password


class UserLogin(BaseModel):
    """
    Payload for standard JSON authentication.
    """
    email: EmailStr = Field(..., examples=["learner@datheon.in"])
    password: str = Field(..., examples=["StrongP@ssw0rd2026"])


class Token(BaseModel):
    """
    JWT Bearer token returned upon successful login.
    """
    access_token: str = Field(..., description="Encrypted JWT Bearer string")
    token_type: str = Field("bearer", description="Token authentication scheme")
    role: str = Field(..., description="Assigned authorization role (user/admin)")
    user_id: int = Field(..., description="User unique database ID")
    email: str = Field(..., description="Authenticated user email")


class TokenPayload(BaseModel):
    """
    Decoded payload structure inside the JWT token.
    """
    sub: str  # User email
    user_id: int
    role: str
    exp: int


class UserResponse(BaseModel):
    """
    Public profile information for an authenticated user.
    Hashed passwords and secrets are strictly excluded.
    """
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    """
    Payload used by administrators to change user role.
    """
    role: UserRole = Field(..., description="New role to assign (user or admin)")


class MessageResponse(BaseModel):
    """
    Generic informative response message.
    """
    message: str
    detail: Optional[str] = None
