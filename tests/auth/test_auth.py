"""
测试认证 API 的脚本
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def test_send_code():
    """测试发送验证码"""
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        try:
            success, message = await auth_service.send_verification_code(
                phone="13800138000",
                purpose="register"
            )
            print(f"Success: {success}")
            print(f"Message: {message}")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_send_code())
