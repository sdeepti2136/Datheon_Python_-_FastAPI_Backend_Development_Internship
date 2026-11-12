"""
Bootstrap Initial Administrator Account Script.

Provides a secure, non-interactive or interactive mechanism to initialize
the first administrative account in a freshly deployed environment.
Reads credentials from environment variables (BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD)
or safely prompts the operator via getpass if variables are unset.

Usage:
    python scripts/create_admin.py
"""

import asyncio
import getpass
import sys
from pathlib import Path

# Add project root to sys.path so app modules import cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.logging_config import logger
from app.models import User, UserRole
from app.security import hash_password

settings = get_settings()


async def bootstrap_admin():
    print("=" * 65)
    print("Datheon FastAPI Internship - Administrator Bootstrap Utility")
    print("=" * 65)

    # 1. Ensure database schema exists
    await init_db()

    # 2. Retrieve credentials
    admin_email = settings.BOOTSTRAP_ADMIN_EMAIL
    admin_password = settings.BOOTSTRAP_ADMIN_PASSWORD

    # If default or unset, prompt interactively
    if not admin_email or not admin_password or admin_password == "ChangeMeAdmin123!":
        print("\nNotice: Default or missing admin credentials detected.")
        choice = input("Would you like to enter custom admin credentials now? [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            admin_email = input("Enter admin email address: ").strip()
            while True:
                p1 = getpass.getpass("Enter secure admin password: ")
                p2 = getpass.getpass("Confirm secure admin password: ")
                if p1 != p2:
                    print("Error: Passwords do not match. Try again.")
                    continue
                if len(p1) < 8:
                    print("Error: Password must be at least 8 characters long.")
                    continue
                admin_password = p1
                break

    if not admin_email or not admin_password:
        print("Error: Email and password cannot be empty.")
        sys.exit(1)

    # 3. Create or elevate user in the database
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == admin_email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.role == UserRole.ADMIN.value:
                print(f"[INFO] User '{admin_email}' already exists and already has ADMIN privileges.")
                return
            else:
                existing_user.role = UserRole.ADMIN.value
                existing_user.is_active = True
                await session.commit()
                print(f"[SUCCESS] User '{admin_email}' promoted to ADMIN successfully!")
                return

        # Create new admin user
        hashed = hash_password(admin_password)
        new_admin = User(
            email=admin_email,
            hashed_password=hashed,
            role=UserRole.ADMIN.value,
            is_active=True,
        )

        session.add(new_admin)
        await session.commit()
        print(f"[SUCCESS] Initial administrator created successfully!")
        print(f" -> Email: {admin_email}")
        print(f" -> Role:  {UserRole.ADMIN.value}")
        print("You can now authenticate via /api/v1/auth/login or Swagger UI.\n")


if __name__ == "__main__":
    asyncio.run(bootstrap_admin())
