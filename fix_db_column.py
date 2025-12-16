"""
修复 verification_codes 表的列名
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from sqlalchemy import text
from app.core.database import engine


async def fix_column_name():
    """将 code_type 列改为 purpose"""
    async with engine.begin() as conn:
        try:
            # 修改列名
            await conn.execute(
                text("ALTER TABLE verification_codes RENAME COLUMN code_type TO purpose")
            )
            print("Column renamed successfully: code_type -> purpose")
        except Exception as e:
            if "does not exist" in str(e):
                print("Column 'purpose' already exists, no change needed")
            else:
                print(f"Error: {e}")
                raise


if __name__ == "__main__":
    asyncio.run(fix_column_name())
