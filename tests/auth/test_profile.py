"""
测试获取和更新用户信息
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def test_user_profile():
    """测试获取和更新用户信息"""
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        try:
            # 1. 登录获取 user_id
            print("1. Logging in...")
            success, message, token_data = await auth_service.login_with_password(
                phone="13900139999",
                password="test123456"
            )
            if not success:
                print(f"Login failed: {message}")
                return

            user_id = token_data['user_id']
            print(f"   Logged in as user {user_id}")

            # 2. 获取用户信息
            print("\n2. Getting user profile...")
            user = await auth_service.get_user_by_id(user_id)
            if user:
                print(f"   Username: {user.username}")
                print(f"   Phone: {user.phone}")
                print(f"   Nickname: {user.nickname}")
                print(f"   Status: {user.status}")

            # 3. 更新用户信息
            print("\n3. Updating user profile...")
            success, message, updated_user = await auth_service.update_user_profile(
                user_id=user_id,
                nickname="API Test User",
                email="test@example.com"
            )
            print(f"   Success: {success}, Message: {message}")
            if updated_user:
                print(f"   Updated Nickname: {updated_user.nickname}")
                print(f"   Updated Email: {updated_user.email}")

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_user_profile())
