"""
SQLAlchemy ORM Database Models.

Defines database schemas for User authentication and BookStore inventory.
Includes constraints, indexes, and timezone-aware timestamps.
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    """
    Role-Based Access Control (RBAC) user roles.
    """
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    User database model for authentication and authorization.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), default=UserRole.USER.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship to books authored/added by this user
    books: Mapped[list["Book"]] = relationship(
        "Book", back_populates="creator", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Book(Base):
    """
    Book database model representing bookstore inventory.
    """
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    isbn: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    publication_year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Audit trail: user who registered this book
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    creator: Mapped[User | None] = relationship("User", back_populates="books")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"
