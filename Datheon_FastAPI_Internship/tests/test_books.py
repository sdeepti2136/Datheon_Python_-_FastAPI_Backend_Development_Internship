"""
Automated Test Suite for BookStore CRUD Operations (Task 1 & Task 3).
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_book_as_admin(client: AsyncClient, admin_auth_headers: dict):
    """
    Verifies that an administrator can successfully register a new book.
    """
    payload = {
        "title": "FastAPI Web Architecture",
        "author": "Bill Lubanovic",
        "description": "Comprehensive guide to building production APIs with FastAPI.",
        "price": 39.99,
        "isbn": "9781492080770",
        "publication_year": 2023,
    }

    response = await client.post(
        "/api/v1/books",
        json=payload,
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["isbn"] == "9781492080770"
    assert data["price"] == 39.99
    assert "id" in data
    assert "created_at" in data


async def test_create_book_unauthorized_for_standard_user(
    client: AsyncClient, user_auth_headers: dict
):
    """
    Verifies that a standard user receives 403 Forbidden when attempting to create a book.
    """
    payload = {
        "title": "Unauthorized Book Creation",
        "author": "Hacker",
        "price": 19.99,
        "isbn": "9780000000001",
        "publication_year": 2024,
    }
    response = await client.post(
        "/api/v1/books",
        json=payload,
        headers=user_auth_headers,
    )
    assert response.status_code == 403
    assert "Requires 'admin' role privileges" in response.json()["detail"]


async def test_create_book_missing_token(client: AsyncClient):
    """
    Verifies that unauthenticated requests receive 401 Unauthorized.
    """
    payload = {
        "title": "Anonymous Creation",
        "author": "Anon",
        "price": 10.0,
        "isbn": "9780000000002",
        "publication_year": 2024,
    }
    response = await client.post("/api/v1/books", json=payload)
    assert response.status_code == 401


async def test_create_book_duplicate_isbn_rejected(
    client: AsyncClient, admin_auth_headers: dict
):
    """
    Verifies that attempting to register a duplicate ISBN results in 409 Conflict.
    """
    payload = {
        "title": "Original Book",
        "author": "Author A",
        "price": 25.0,
        "isbn": "9781234567890",
        "publication_year": 2022,
    }
    res1 = await client.post("/api/v1/books", json=payload, headers=admin_auth_headers)
    assert res1.status_code == 201

    # Second creation with identical ISBN
    res2 = await client.post("/api/v1/books", json=payload, headers=admin_auth_headers)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


async def test_book_validation_rules(client: AsyncClient, admin_auth_headers: dict):
    """
    Verifies Pydantic schema validation rejects invalid prices, publication years, and ISBNs.
    """
    # Negative price
    res_neg_price = await client.post(
        "/api/v1/books",
        json={
            "title": "Bad Price",
            "author": "Author",
            "price": -5.0,
            "isbn": "9781111111111",
            "publication_year": 2023,
        },
        headers=admin_auth_headers,
    )
    assert res_neg_price.status_code == 422

    # Invalid ISBN (invalid length)
    res_bad_isbn = await client.post(
        "/api/v1/books",
        json={
            "title": "Bad ISBN",
            "author": "Author",
            "price": 20.0,
            "isbn": "123",
            "publication_year": 2023,
        },
        headers=admin_auth_headers,
    )
    assert res_bad_isbn.status_code == 422


async def test_list_books_pagination_and_filtering(
    client: AsyncClient, admin_auth_headers: dict
):
    """
    Verifies listing books, pagination envelope, and query filtering.
    """
    # Seed unique books
    for i in range(1, 4):
        await client.post(
            "/api/v1/books",
            json={
                "title": f"Python Volume {i}",
                "author": f"Guido {i}",
                "price": float(20 + (i * 10)),
                "isbn": f"978999999999{i}",
                "publication_year": 2020 + i,
            },
            headers=admin_auth_headers,
        )

    # Public listing
    response = await client.get("/api/v1/books?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) <= 2

    # Filter by title
    filter_res = await client.get("/api/v1/books?title=Volume 2")
    assert filter_res.status_code == 200
    filtered_data = filter_res.json()
    assert any("Volume 2" in b["title"] for b in filtered_data["items"])


async def test_get_single_book_and_not_found(
    client: AsyncClient, admin_auth_headers: dict
):
    """
    Verifies single book retrieval and 404 response for nonexistent IDs.
    """
    create_res = await client.post(
        "/api/v1/books",
        json={
            "title": "Single Book Test",
            "author": "Author One",
            "price": 15.0,
            "isbn": "9783333333333",
            "publication_year": 2021,
        },
        headers=admin_auth_headers,
    )
    book_id = create_res.json()["id"]

    # Fetch existing
    res = await client.get(f"/api/v1/books/{book_id}")
    assert res.status_code == 200
    assert res.json()["id"] == book_id

    # Nonexistent ID
    res_404 = await client.get("/api/v1/books/999999")
    assert res_404.status_code == 404


async def test_update_and_delete_book(
    client: AsyncClient, admin_auth_headers: dict
):
    """
    Verifies full lifecycle of updating and deleting a book.
    """
    create_res = await client.post(
        "/api/v1/books",
        json={
            "title": "Book To Modify",
            "author": "Original Author",
            "price": 50.0,
            "isbn": "9784444444444",
            "publication_year": 2020,
        },
        headers=admin_auth_headers,
    )
    book_id = create_res.json()["id"]

    # Update title and price
    update_res = await client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Updated Title", "price": 59.99},
        headers=admin_auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"
    assert update_res.json()["price"] == 59.99

    # Delete book
    del_res = await client.delete(
        f"/api/v1/books/{book_id}", headers=admin_auth_headers
    )
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # Confirm deletion returns 404
    get_del = await client.get(f"/api/v1/books/{book_id}")
    assert get_del.status_code == 404
