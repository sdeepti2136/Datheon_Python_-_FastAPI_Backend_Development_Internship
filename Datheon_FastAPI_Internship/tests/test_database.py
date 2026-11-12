"""
Automated Test Suite for Database Persistence, Constraints & Transactions (Task 3).
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book, User, UserRole
from app.security import hash_password

pytestmark = pytest.mark.asyncio


async def test_database_persistence_and_relationships(db_session: AsyncSession):
    """
    Verifies that User and Book records persist properly in SQLite
    and maintain relational foreign key integrity.
    """
    # 1. Create User
    admin = User(
        email="db_persistence_admin@datheon.local",
        hashed_password=hash_password("AdminSecurePass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    assert admin.id is not None

    # 2. Create Book associated with admin
    book = Book(
        title="Database Systems Concepts",
        author="Silberschatz",
        description="Classic database textbook.",
        price=75.0,
        isbn="9780073523323",
        publication_year=2019,
        created_by_user_id=admin.id,
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    assert book.id is not None
    assert book.created_by_user_id == admin.id

    # 3. Query back in a clean query
    result = await db_session.execute(select(Book).where(Book.isbn == "9780073523323"))
    persisted_book = result.scalar_one_or_none()
    assert persisted_book is not None
    assert persisted_book.title == "Database Systems Concepts"


async def test_database_unique_email_constraint(db_session: AsyncSession):
    """
    Verifies that SQLite enforces the unique email constraint at the database level.
    """
    user1 = User(
        email="unique_constraint@datheon.local",
        hashed_password="hash1",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user1)
    await db_session.commit()

    user2 = User(
        email="unique_constraint@datheon.local",
        hashed_password="hash2",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


async def test_database_unique_isbn_constraint(db_session: AsyncSession):
    """
    Verifies that SQLite enforces the unique ISBN constraint at the database level.
    """
    book1 = Book(
        title="Book Alpha",
        author="Author",
        price=20.0,
        isbn="9785555555555",
        publication_year=2023,
    )
    db_session.add(book1)
    await db_session.commit()

    book2 = Book(
        title="Book Beta",
        author="Author",
        price=25.0,
        isbn="9785555555555",  # Identical ISBN
        publication_year=2024,
    )
    db_session.add(book2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()
