"""
Background Notification Service Module.

Demonstrates decoupled asynchronous background task processing using
FastAPI's native BackgroundTasks engine.
Simulates sending inventory notifications and dispatching audit events
without blocking the client's HTTP response cycle.

NOTE ON ARCHITECTURE:
FastAPI BackgroundTasks run within the same Python process in the background.
They are ideal for lightweight tasks (audit logging, non-critical webhooks,
dispatching emails). For heavy computation, reliable retries, or distributed
durable queues, a dedicated worker system such as Celery or ARQ with Redis
should be utilized.
"""

import asyncio
from datetime import datetime, timezone
from app.logging_config import logger


async def send_book_creation_notification(
    book_id: int,
    title: str,
    author: str,
    isbn: str,
    admin_email: str,
) -> None:
    """
    Asynchronous background task triggered whenever a new book is added.
    Simulates sending an inventory alert to store staff or external systems.

    Safety: Does NOT log sensitive credentials or secrets.
    """
    try:
        logger.info(
            f"[BACKGROUND TASK STARTED] Queuing inventory notification for "
            f"Book ID: {book_id} ('{title}' by {author}, ISBN: {isbn})"
        )

        # Non-blocking asynchronous I/O simulation (e.g. SMTP or third-party API dispatch)
        await asyncio.sleep(0.5)

        dispatched_at = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"[BACKGROUND TASK SUCCESS] Inventory notification dispatched at {dispatched_at}. "
            f"Audit log: Created by {admin_email} for Book ID: {book_id}."
        )
    except Exception as exc:
        logger.error(
            f"[BACKGROUND TASK FAILED] Could not dispatch notification for Book ID {book_id}: {exc}"
        )


async def send_welcome_email(user_email: str, user_id: int) -> None:
    """
    Simulates sending a welcome email upon user registration.
    """
    try:
        logger.info(f"[BACKGROUND TASK STARTED] Sending welcome notification to user ID {user_id}")
        await asyncio.sleep(0.3)
        logger.info(f"[BACKGROUND TASK SUCCESS] Welcome email dispatched to {user_email}")
    except Exception as exc:
        logger.error(f"[BACKGROUND TASK FAILED] Welcome email failed for user {user_id}: {exc}")
