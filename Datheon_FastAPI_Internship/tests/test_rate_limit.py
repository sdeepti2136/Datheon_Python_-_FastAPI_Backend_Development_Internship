"""
Automated Test Suite for Rate Limiting, OpenAPI, and Background Tasks (Task 4).
"""

import pytest
from httpx import AsyncClient
from app.config import get_settings

pytestmark = pytest.mark.asyncio
settings = get_settings()


async def test_openapi_and_docs_endpoints(client: AsyncClient):
    """
    Verifies that Swagger UI (/docs) and OpenAPI specification (/openapi.json)
    are accessible and return valid 200 responses.
    """
    res_docs = await client.get("/docs")
    assert res_docs.status_code == 200
    assert "swagger-ui" in res_docs.text.lower()

    res_openapi = await client.get("/openapi.json")
    assert res_openapi.status_code == 200
    spec = res_openapi.json()
    assert spec["info"]["title"] == settings.PROJECT_NAME
    assert "/api/v1/books" in spec["paths"]
    assert "/api/v1/auth/login" in spec["paths"]


async def test_health_check_endpoint(client: AsyncClient):
    """
    Verifies the container health check endpoint returns 200 and healthy status.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


async def test_rate_limiting_enforcement(client: AsyncClient):
    """
    Verifies that exceeding the configured rate limit quota on the login endpoint
    triggers an HTTP 429 Too Many Requests response.
    """
    login_payload = {
        "username": "ratelimit_tester@datheon.in",
        "password": "Password123!",
    }

    # The login rate limit is set to 5/minute in config.py
    # Send consecutive requests until rate limit triggers or quota is exhausted
    status_codes = []
    for _ in range(8):
        res = await client.post("/api/v1/auth/login", data=login_payload)
        status_codes.append(res.status_code)

    # At least one request should be rate-limited (HTTP 429)
    assert 429 in status_codes, f"Expected HTTP 429 in responses: {status_codes}"
