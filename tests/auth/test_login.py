"""
测试完整的登录流程
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def test_login():
    """测试用户登录"""
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        try:
            # 使用已注册的用户登录
            print("Testing login with password...")
            success, message, token_data = await auth_service.login_with_password(
                phone="13900139999",
                password="test123456"
            )
            print(f"Success: {success}, Message: {message}")
            if token_data:
                print(f"Token: {token_data['access_token'][:50]}...")
                print(f"User ID: {token_data['user_id']}, Username: {token_data['username']}")

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_login())
