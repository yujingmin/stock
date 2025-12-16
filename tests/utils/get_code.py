"""
Get verification code for a phone number
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def get_code(phone, purpose="register"):
    """Get verification code"""
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        success, message = await auth_service.send_verification_code(
            phone=phone,
            purpose=purpose
        )
        if success:
            print(f"\nVerification code sent!")
            print(f"Phone: {phone}")
            print(f"Message: {message}")
            # Extract code from message
            code = message.split(":")[-1].strip().rstrip(")")
            print(f"\n===========================")
            print(f"CODE: {code}")
            print(f"===========================\n")
        else:
            print(f"Failed: {message}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        phone = sys.argv[1]
        purpose = sys.argv[2] if len(sys.argv) > 2 else "register"
        asyncio.run(get_code(phone, purpose))
    else:
        print("Usage: python get_code.py <phone> [purpose]")
        print("Example: python get_code.py 13800138456 register")
