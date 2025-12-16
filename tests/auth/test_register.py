"""
测试完整的注册流程
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def test_register():
    """测试用户注册"""
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        try:
            # 发送验证码
            print("1. Sending verification code...")
            success, message = await auth_service.send_verification_code(
                phone="13900139003",
                purpose="register"
            )
            print(f"   Success: {success}, Message: {message}")

            if not success:
                return

            # 提取验证码（从message中）
            code = message.split("：")[-1].rstrip("）")
            print(f"   Verification code: {code}")

            # 注册用户
            print("\n2. Registering user...")
            success, message, user = await auth_service.register(
                username="testuser3",
                phone="13900139003",
                password="test123456",
                verification_code=code
            )
            print(f"   Success: {success}, Message: {message}")
            if user:
                print(f"   User ID: {user.id}, Username: {user.username}")

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_register())
