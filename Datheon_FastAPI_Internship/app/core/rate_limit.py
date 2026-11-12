"""
Rate Limiting Infrastructure Module.

Implements IP-based rate limiting via SlowAPI (backed by the token-bucket
and fixed-window algorithms in python-limits).
Safeguards public endpoints and brute-force targets like /auth/login.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.logging_config import logger

settings = get_settings()


def safe_get_remote_address(request: Request) -> str:
    """
    Safely resolves the client identifier for rate limiting.
    Uses request.client.host by default to prevent client IP spoofing via headers.
    When operating behind trusted reverse proxies (NGINX/Cloudflare),
    the proxy headers middleware should sanitize the host IP first.
    """
    client_ip = get_remote_address(request)
    return client_ip or "127.0.0.1"


# Global SlowAPI Limiter instance
limiter = Limiter(
    key_func=safe_get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    headers_enabled=True,
)


def custom_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> Response:
    """
    Custom HTTP 429 response handler returning structured JSON
    consistent with application error conventions.
    """
    logger.warning(
        f"Rate limit exceeded by {request.client.host if request.client else 'unknown'} "
        f"on endpoint {request.method} {request.url.path}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Rate limit quota exceeded. Please slow down your requests.",
            "detail": f"Limit rule: {exc.detail}",
        },
        headers={"Retry-After": "60"},
    )
