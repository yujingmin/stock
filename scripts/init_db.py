# -*- coding: utf-8 -*-
"""
Database initialization script
"""
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.core.database import engine, Base
from app.models.user import User, UserSession, VerificationCode


async def init_database():
    """Initialize database tables"""
    print("Starting database initialization...")

    try:
        # Import all models to ensure they are registered to Base.metadata
        print("Importing models...")

        # Create all tables
        print("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("Database initialization successful!")
        print(f"Created tables: {', '.join(Base.metadata.tables.keys())}")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Close database connection
        await engine.dispose()

    return True


async def drop_all_tables():
    """Drop all tables (use with caution!)"""
    print("WARNING: About to drop all tables...")
    confirm = input("Confirm drop all tables? (yes/no): ")

    if confirm.lower() != "yes":
        print("Operation cancelled")
        return False

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("All tables dropped")
        return True
    except Exception as e:
        print(f"Failed to drop tables: {e}")
        return False
    finally:
        await engine.dispose()


async def reset_database():
    """Reset database (drop and recreate all tables)"""
    print("Resetting database...")
    if await drop_all_tables():
        await init_database()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database management tool")
    parser.add_argument(
        "action",
        choices=["init", "drop", "reset"],
        help="Action type: init(initialize), drop(drop all tables), reset(reset)"
    )

    args = parser.parse_args()

    if args.action == "init":
        asyncio.run(init_database())
    elif args.action == "drop":
        asyncio.run(drop_all_tables())
    elif args.action == "reset":
        asyncio.run(reset_database())
