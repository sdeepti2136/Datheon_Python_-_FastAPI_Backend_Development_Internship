"""
Security & Cryptography Module.

Implements industry-standard password hashing using direct bcrypt,
JSON Web Token (JWT) encoding/decoding, and OAuth2 Bearer schemes.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer
from app.config import get_settings
from app.logging_config import logger

settings = get_settings()

# OAuth2 Password Bearer scheme for OpenAPI Swagger documentation
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


# ==============================================================================
# PASSWORD HASHING (BCRYPT)
# ==============================================================================

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a generated salt.
    Never stores or returns raw plaintext.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    Safely handles invalid hash encodings.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


# ==============================================================================
# JSON WEB TOKENS (JWT)
# ==============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Includes subject (email), user_id, role, issued-at, and expiration claims.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT token's signature, algorithm, and expiration.
    Returns payload dictionary if valid, or None if expired/tampered.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT validation failed: Token has expired.")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning(f"JWT validation failed: Invalid token ({exc}).")
        return None
