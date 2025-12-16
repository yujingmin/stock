"""
重建用户认证相关的数据库表
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.user import User, UserSession, VerificationCode


async def recreate_tables():
    """删除并重建表"""
    async with engine.begin() as conn:
        # 删除旧表
        print("Dropping old tables...")
        await conn.execute(text("DROP TABLE IF EXISTS user_sessions CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS verification_codes CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        print("Old tables dropped.")

        # 创建新表
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("New tables created successfully!")

        # 显示创建的表
        print(f"\nCreated tables: {', '.join(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    asyncio.run(recreate_tables())
