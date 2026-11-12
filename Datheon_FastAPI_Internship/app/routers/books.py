"""
BookStore REST API Router.

Implements complete CRUD endpoints for the BookStore catalog:
- POST /api/v1/books: Create book (Admin only, queues background notification)
- GET /api/v1/books: List books with filtering and pagination (Public)
- GET /api/v1/books/{book_id}: Retrieve single book by ID (Public)
- PUT /api/v1/books/{book_id}: Update book attributes (Admin only)
- DELETE /api/v1/books/{book_id}: Remove book (Admin only)
"""

from typing import Annotated, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.logging_config import logger
from app.models import Book, User
from app.schemas import (
    BookCreate,
    BookListResponse,
    BookResponse,
    BookUpdate,
    MessageResponse,
)
from app.services.notifications import send_book_creation_notification

router = APIRouter(
    prefix="/books",
    tags=["Books - Catalog Management"],
)


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book (Admin only)",
    description=(
        "Registers a new book in the inventory catalog. "
        "Requires **admin** role authentication. "
        "Validates ISBN uniqueness, title, price, and year. "
        "Triggers an asynchronous background notification upon success."
    ),
    responses={
        201: {"description": "Book created successfully"},
        400: {"description": "Validation error or invalid input"},
        401: {"description": "Authentication credentials missing or invalid"},
        403: {"description": "Forbidden: Requires administrator privileges"},
        409: {"description": "Conflict: Book with this ISBN already exists"},
    },
)
async def create_book(
    book_in: BookCreate,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Book:
    # Check for existing book with the same ISBN
    existing_isbn = await db.execute(select(Book).where(Book.isbn == book_in.isbn))
    if existing_isbn.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A book with ISBN '{book_in.isbn}' is already registered in the system.",
        )

    # Instantiate model and attach creator ID for auditability
    new_book = Book(
        title=book_in.title,
        author=book_in.author,
        description=book_in.description,
        price=book_in.price,
        isbn=book_in.isbn,
        publication_year=book_in.publication_year,
        created_by_user_id=current_admin.id,
    )

    db.add(new_book)
    await db.flush()  # Populates new_book.id before background task queuing
    await db.refresh(new_book)

    # Queue background task for non-blocking notification
    background_tasks.add_task(
        send_book_creation_notification,
        book_id=new_book.id,
        title=new_book.title,
        author=new_book.author,
        isbn=new_book.isbn,
        admin_email=current_admin.email,
    )

    logger.info(f"Book created with ID {new_book.id} by admin '{current_admin.email}'")
    return new_book


@router.get(
    "",
    response_model=BookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List books with pagination & filters (Public)",
    description=(
        "Retrieves a paginated list of books from the catalog. "
        "Supports filtering by title, author, ISBN, price range, and publication year."
    ),
)
async def list_books(
    db: Annotated[AsyncSession, Depends(get_db)],
    title: Optional[str] = Query(
        None, description="Filter by book title (case-insensitive substring)"
    ),
    author: Optional[str] = Query(
        None, description="Filter by author name (case-insensitive substring)"
    ),
    isbn: Optional[str] = Query(
        None, description="Filter by exact or partial ISBN"
    ),
    min_price: Optional[float] = Query(
        None, ge=0, description="Minimum price threshold"
    ),
    max_price: Optional[float] = Query(
        None, ge=0, description="Maximum price threshold"
    ),
    publication_year: Optional[int] = Query(
        None, ge=1400, le=2030, description="Exact publication calendar year"
    ),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> BookListResponse:
    # Build filter conditions dynamically
    query = select(Book)
    count_query = select(func.count()).select_from(Book)

    filters = []
    if title:
        filters.append(Book.title.ilike(f"%{title}%"))
    if author:
        filters.append(Book.author.ilike(f"%{author}%"))
    if isbn:
        filters.append(Book.isbn.ilike(f"%{isbn}%"))
    if min_price is not None:
        filters.append(Book.price >= min_price)
    if max_price is not None:
        filters.append(Book.price <= max_price)
    if publication_year is not None:
        filters.append(Book.publication_year == publication_year)

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    # Compute total matches for pagination envelope
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and sorting (most recent first)
    query = query.order_by(Book.id.desc()).offset(offset).limit(limit)
    books_result = await db.execute(query)
    items = books_result.scalars().all()

    return BookListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=list(items),
    )


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single book by ID (Public)",
    description="Fetches detailed metadata of a specific book by its unique numeric ID.",
    responses={
        200: {"description": "Book found and returned"},
        404: {"description": "Book with requested ID not found"},
    },
)
async def get_book(
    book_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Book:
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} was not found in the catalog.",
        )
    return book


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a book by ID (Admin only)",
    description=(
        "Updates specified fields of an existing book. "
        "Requires **admin** role authentication. "
        "Verifies ISBN uniqueness if a modified ISBN is provided."
    ),
    responses={
        200: {"description": "Book updated successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Book not found"},
        409: {"description": "New ISBN conflicts with an existing book"},
    },
)
async def update_book(
    book_id: int,
    book_in: BookUpdate,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Book:
    # Fetch existing book
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} was not found.",
        )

    # Check for ISBN collision if ISBN is being updated
    if book_in.isbn and book_in.isbn != book.isbn:
        isbn_check = await db.execute(
            select(Book).where(Book.isbn == book_in.isbn, Book.id != book_id)
        )
        if isbn_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another book with ISBN '{book_in.isbn}' already exists.",
            )

    # Apply only provided updates (exclude unset fields)
    update_data = book_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)

    await db.flush()
    await db.refresh(book)
    logger.info(f"Book ID {book_id} updated by admin '{current_admin.email}'")
    return book


@router.delete(
    "/{book_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a book by ID (Admin only)",
    description="Permanently removes a book from the catalog. Requires **admin** role authentication.",
    responses={
        200: {"description": "Book deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Book not found"},
    },
)
async def delete_book(
    book_id: int,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} was not found.",
        )

    await db.delete(book)
    logger.info(f"Book ID {book_id} permanently deleted by admin '{current_admin.email}'")
    return MessageResponse(
        message="Book deleted successfully",
        detail=f"Book with ID {book_id} ('{book.title}') was removed from the database.",
    )
